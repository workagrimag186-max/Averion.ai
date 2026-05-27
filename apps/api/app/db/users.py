from dataclasses import dataclass

import psycopg

from app.core.config import settings
from app.db.connection import is_database_configured
from app.db.documents import DatabaseNotConfiguredError


@dataclass(frozen=True)
class UserProfile:
    user_id: str
    organization_id: str
    auth_user_id: str | None
    email: str
    name: str | None
    avatar_url: str | None
    job_title: str | None
    role: str


@dataclass(frozen=True)
class AuthProfileCreate:
    auth_user_id: str
    email: str
    organization_id: str
    name: str | None = None
    avatar_url: str | None = None
    job_title: str | None = None
    role: str = "member"


@dataclass(frozen=True)
class AccountProfile:
    user_id: str
    organization_id: str
    organization_name: str | None
    auth_user_id: str | None
    email: str
    name: str | None
    avatar_url: str | None
    job_title: str | None
    role: str


@dataclass(frozen=True)
class AccountProfileUpdate:
    user_id: str
    organization_id: str
    name: str | None
    job_title: str | None


def _ensure_organization(cursor, organization_id: str) -> None:
    if organization_id != settings.default_organization_id:
        return

    cursor.execute(
        """
        insert into organizations (id, name)
        values (%s::uuid, %s)
        on conflict (id) do nothing
        """,
        (
            settings.default_organization_id,
            "Development Organization"
        )
    )


def _row_to_user_profile(row) -> UserProfile:
    return UserProfile(
        user_id=row[0],
        organization_id=row[1],
        auth_user_id=row[2],
        email=row[3],
        name=row[4],
        avatar_url=row[5],
        job_title=row[6],
        role=row[7]
    )


def _row_to_account_profile(row) -> AccountProfile:
    return AccountProfile(
        user_id=row[0],
        organization_id=row[1],
        organization_name=row[2],
        auth_user_id=row[3],
        email=row[4],
        name=row[5],
        avatar_url=row[6],
        job_title=row[7],
        role=row[8]
    )


def get_user_profile_by_auth_id(auth_user_id: str) -> UserProfile | None:
    if not is_database_configured():
        raise DatabaseNotConfiguredError("DATABASE_URL is not configured.")

    with psycopg.connect(settings.database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                select
                    id::text,
                    organization_id::text,
                    auth_user_id::text,
                    email,
                    name,
                    avatar_url,
                    job_title,
                    role
                from users
                where auth_user_id = %s::uuid
                """,
                (auth_user_id,)
            )

            row = cursor.fetchone()
            return _row_to_user_profile(row) if row else None


def get_account_profile(
    *,
    user_id: str,
    organization_id: str
) -> AccountProfile | None:
    if not is_database_configured():
        raise DatabaseNotConfiguredError("DATABASE_URL is not configured.")

    with psycopg.connect(settings.database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                select
                    users.id::text,
                    users.organization_id::text,
                    organizations.name,
                    users.auth_user_id::text,
                    users.email,
                    users.name,
                    users.avatar_url,
                    users.job_title,
                    users.role
                from users
                join organizations
                    on organizations.id = users.organization_id
                where users.id = %s::uuid
                    and users.organization_id = %s::uuid
                """,
                (
                    user_id,
                    organization_id
                )
            )

            row = cursor.fetchone()
            return _row_to_account_profile(row) if row else None


def update_account_profile(profile: AccountProfileUpdate) -> AccountProfile | None:
    if not is_database_configured():
        raise DatabaseNotConfiguredError("DATABASE_URL is not configured.")

    with psycopg.connect(settings.database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                update users
                set
                    name = %s,
                    job_title = %s,
                    updated_at = now()
                where id = %s::uuid
                    and organization_id = %s::uuid
                returning
                    id::text,
                    organization_id::text,
                    (
                        select organizations.name
                        from organizations
                        where organizations.id = users.organization_id
                    ),
                    auth_user_id::text,
                    email,
                    name,
                    avatar_url,
                    job_title,
                    role
                """,
                (
                    profile.name,
                    profile.job_title,
                    profile.user_id,
                    profile.organization_id
                )
            )

            row = cursor.fetchone()
            return _row_to_account_profile(row) if row else None


def get_or_create_user_profile(profile: AuthProfileCreate) -> UserProfile:
    if not is_database_configured():
        raise DatabaseNotConfiguredError("DATABASE_URL is not configured.")

    with psycopg.connect(settings.database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            _ensure_organization(cursor, profile.organization_id)

            cursor.execute(
                """
                insert into users (
                    organization_id,
                    auth_user_id,
                    email,
                    name,
                    avatar_url,
                    job_title,
                    role
                )
                values (%s::uuid, %s::uuid, %s, %s, %s, %s, %s)
                on conflict (auth_user_id) do update set
                    email = excluded.email,
                    name = coalesce(excluded.name, users.name),
                    avatar_url = coalesce(excluded.avatar_url, users.avatar_url),
                    job_title = coalesce(excluded.job_title, users.job_title),
                    updated_at = now()
                returning
                    id::text,
                    organization_id::text,
                    auth_user_id::text,
                    email,
                    name,
                    avatar_url,
                    job_title,
                    role
                """,
                (
                    profile.organization_id,
                    profile.auth_user_id,
                    profile.email,
                    profile.name,
                    profile.avatar_url,
                    profile.job_title,
                    profile.role
                )
            )

            return _row_to_user_profile(cursor.fetchone())
