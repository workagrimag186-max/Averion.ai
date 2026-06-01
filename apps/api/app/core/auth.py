from dataclasses import dataclass
import ssl
from typing import Annotated, Any

import certifi
import jwt
from jwt.exceptions import PyJWKClientConnectionError, PyJWKClientError
from jwt import PyJWKClient
from fastapi import Header, HTTPException, status

from app.core.config import settings
from app.db.connection import is_database_configured
from app.db.documents import DatabaseNotConfiguredError
from app.db.users import (
    AuthProfileCreate,
    UserProfile,
    get_or_create_user_profile
)


@dataclass(frozen=True)
class RequestContext:
    organization_id: str
    user_id: str | None
    auth_user_id: str | None
    email: str | None
    role: str | None
    is_authenticated: bool


class AuthConfigurationError(RuntimeError):
    pass


ASYMMETRIC_JWT_ALGORITHMS = {"ES256", "RS256"}
LEGACY_JWT_ALGORITHMS = {"HS256"}


def _development_context() -> RequestContext:
    return RequestContext(
        organization_id=settings.default_organization_id,
        user_id=None,
        auth_user_id=None,
        email=None,
        role=None,
        is_authenticated=False
    )


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header."
        )

    return token.strip()


def _get_token_algorithm(token: str) -> str:
    try:
        header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token."
        ) from exc

    algorithm = str(header.get("alg") or "").strip()

    if not algorithm:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token."
        )

    return algorithm


def _get_supabase_jwks_url() -> str:
    if not settings.supabase_url:
        raise AuthConfigurationError("SUPABASE_URL is not configured.")

    return f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"


def _get_jwks_ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


def _decode_legacy_supabase_token(token: str) -> dict[str, Any]:
    if not settings.supabase_jwt_secret:
        raise AuthConfigurationError("SUPABASE_JWT_SECRET is not configured.")

    return jwt.decode(
        token,
        settings.supabase_jwt_secret,
        algorithms=["HS256"],
        audience="authenticated"
    )


def _decode_asymmetric_supabase_token(token: str, algorithm: str) -> dict[str, Any]:
    jwks_client = PyJWKClient(
        _get_supabase_jwks_url(),
        ssl_context=_get_jwks_ssl_context()
    )
    signing_key = jwks_client.get_signing_key_from_jwt(token)

    return jwt.decode(
        token,
        signing_key.key,
        algorithms=[algorithm],
        audience="authenticated"
    )


def _decode_supabase_token(token: str) -> dict[str, Any]:
    algorithm = _get_token_algorithm(token)

    try:
        if algorithm in ASYMMETRIC_JWT_ALGORITHMS:
            return _decode_asymmetric_supabase_token(token, algorithm)

        if algorithm in LEGACY_JWT_ALGORITHMS:
            return _decode_legacy_supabase_token(token)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unsupported authentication token algorithm."
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired."
        ) from exc
    except PyJWKClientConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not fetch Supabase signing keys."
        ) from exc
    except PyJWKClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token."
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token."
        ) from exc


def _email_domain_is_allowed(email: str) -> bool:
    allowed_domains = settings.allowed_email_domain_list

    if not allowed_domains:
        return True

    domain = email.strip().lower().split("@")[-1]
    return domain in allowed_domains


def _profile_from_claims(claims: dict[str, Any]) -> AuthProfileCreate:
    auth_user_id = str(claims.get("sub") or "").strip()
    email = str(claims.get("email") or "").strip().lower()

    if not auth_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing a subject."
        )

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing an email."
        )

    if not _email_domain_is_allowed(email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email domain is not allowed."
        )

    metadata = claims.get("user_metadata")
    user_metadata = metadata if isinstance(metadata, dict) else {}

    return AuthProfileCreate(
        auth_user_id=auth_user_id,
        email=email,
        name=user_metadata.get("full_name") or user_metadata.get("name"),
        avatar_url=user_metadata.get("avatar_url"),
        role="owner"
    )


def _context_from_profile(profile: UserProfile) -> RequestContext:
    return RequestContext(
        organization_id=profile.organization_id,
        user_id=profile.user_id,
        auth_user_id=profile.auth_user_id,
        email=profile.email,
        role=profile.role,
        is_authenticated=True
    )


def get_request_context(
    authorization: Annotated[str | None, Header()] = None
) -> RequestContext:
    token = _extract_bearer_token(authorization)

    if token is None:
        if settings.auth_required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required."
            )

        return _development_context()

    try:
        claims = _decode_supabase_token(token)
        profile = _profile_from_claims(claims)

        if not is_database_configured():
            if settings.auth_required:
                raise DatabaseNotConfiguredError("DATABASE_URL is not configured.")

            return RequestContext(
                organization_id=settings.default_organization_id,
                user_id=None,
                auth_user_id=profile.auth_user_id,
                email=profile.email,
                role=None,
                is_authenticated=True
            )

        return _context_from_profile(get_or_create_user_profile(profile))
    except AuthConfigurationError as exc:
        if settings.auth_required:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc)
            ) from exc

        return _development_context()
    except DatabaseNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc)
        ) from exc
