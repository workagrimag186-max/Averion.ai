from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import RequestContext, get_request_context
from app.db.documents import DatabaseNotConfiguredError
from app.db.users import (
    AccountProfileUpdate,
    get_account_profile,
    get_team,
    update_account_profile,
    update_organization_name,
    update_team_member_role
)
from app.schemas.users import (
    AccountProfileResponse,
    AccountProfileUpdateRequest,
    OrganizationUpdateRequest,
    TeamMemberResponse,
    TeamMemberRoleUpdateRequest,
    TeamResponse
)


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


def _require_profile(context: RequestContext) -> None:
    if context.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication profile is required."
        )


def _require_owner(context: RequestContext) -> None:
    _require_profile(context)

    if context.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners can manage workspace settings."
        )


def _team_response_from_record(team) -> TeamResponse:
    return TeamResponse(
        organization_id=team.organization_id,
        organization_name=team.organization_name,
        members=[
            TeamMemberResponse(**member.__dict__)
            for member in team.members
        ]
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


@router.get("/team", response_model=TeamResponse)
def get_current_user_team(
    context: RequestContext = Depends(get_request_context)
) -> TeamResponse:
    _require_profile(context)

    try:
        team = get_team(context.organization_id)
    except DatabaseNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc)
        ) from exc

    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found."
        )

    return _team_response_from_record(team)


@router.patch("/organization", response_model=TeamResponse)
def update_current_user_organization(
    request: OrganizationUpdateRequest,
    context: RequestContext = Depends(get_request_context)
) -> TeamResponse:
    _require_owner(context)

    try:
        team = update_organization_name(
            organization_id=context.organization_id,
            name=request.name
        )
    except DatabaseNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc)
        ) from exc

    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found."
        )

    return _team_response_from_record(team)


@router.patch("/team/{user_id}/role", response_model=TeamMemberResponse)
def update_current_user_team_member_role(
    user_id: str,
    request: TeamMemberRoleUpdateRequest,
    context: RequestContext = Depends(get_request_context)
) -> TeamMemberResponse:
    _require_owner(context)

    if user_id == context.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owners cannot change their own role."
        )

    try:
        member = update_team_member_role(
            organization_id=context.organization_id,
            user_id=user_id,
            role=request.role
        )
    except DatabaseNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc)
        ) from exc

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found."
        )

    return TeamMemberResponse(**member.__dict__)
