from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import RequestContext, get_request_context
from app.db.documents import DatabaseNotConfiguredError
from app.db.users import (
    AccountProfileUpdate,
    get_account_profile,
    update_account_profile
)
from app.schemas.users import AccountProfileResponse, AccountProfileUpdateRequest


router = APIRouter(prefix="/users", tags=["users"])


def _response_from_context(context: RequestContext) -> AccountProfileResponse:
    return AccountProfileResponse(
        user_id=context.user_id,
        organization_id=context.organization_id,
        organization_name=None,
        auth_user_id=context.auth_user_id,
        email=context.email,
        name=None,
        avatar_url=None,
        job_title=None,
        role=context.role
    )


@router.get("/me", response_model=AccountProfileResponse)
def get_current_user_profile(
    context: RequestContext = Depends(get_request_context)
) -> AccountProfileResponse:
    if context.user_id is None:
        return _response_from_context(context)

    try:
        profile = get_account_profile(
            user_id=context.user_id,
            organization_id=context.organization_id
        )
    except DatabaseNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc)
        ) from exc

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found."
        )

    return AccountProfileResponse(**profile.__dict__)


@router.patch("/me", response_model=AccountProfileResponse)
def update_current_user_profile(
    request: AccountProfileUpdateRequest,
    context: RequestContext = Depends(get_request_context)
) -> AccountProfileResponse:
    if context.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication profile is required to update account details."
        )

    try:
        profile = update_account_profile(
            AccountProfileUpdate(
                user_id=context.user_id,
                organization_id=context.organization_id,
                name=request.name,
                job_title=request.job_title
            )
        )
    except DatabaseNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc)
        ) from exc

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found."
        )

    return AccountProfileResponse(**profile.__dict__)
