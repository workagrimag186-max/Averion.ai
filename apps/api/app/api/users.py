from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import RequestContext, get_request_context
from app.db.documents import DatabaseNotConfiguredError
from app.db.users import (
    AccountProfileUpdate,
    accept_organization_invitation,
    create_organization_invitation,
    get_account_profile,
    get_team,
    list_pending_invitations_for_email,
    remove_team_member_from_organization,
    update_account_profile,
    update_organization_name,
    update_team_member_role
)
from app.schemas.users import (
    AccountProfileResponse,
    AccountProfileUpdateRequest,
    OrganizationInvitationCreateRequest,
    OrganizationInvitationResponse,
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


def _invitation_response_from_record(invitation) -> OrganizationInvitationResponse:
    return OrganizationInvitationResponse(**invitation.__dict__)


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


@router.post("/invitations", response_model=OrganizationInvitationResponse)
def create_current_user_organization_invitation(
    request: OrganizationInvitationCreateRequest,
    context: RequestContext = Depends(get_request_context)
) -> OrganizationInvitationResponse:
    _require_owner(context)

    if request.email == (context.email or "").strip().lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owners cannot invite themselves."
        )

    try:
        invitation = create_organization_invitation(
            organization_id=context.organization_id,
            invited_by_user_id=context.user_id,
            invited_email=request.email
        )
    except DatabaseNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc)
        ) from exc

    return _invitation_response_from_record(invitation)


@router.get("/invitations", response_model=list[OrganizationInvitationResponse])
def get_current_user_invitations(
    context: RequestContext = Depends(get_request_context)
) -> list[OrganizationInvitationResponse]:
    _require_profile(context)

    try:
        invitations = list_pending_invitations_for_email(context.email or "")
    except DatabaseNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc)
        ) from exc

    return [
        _invitation_response_from_record(invitation)
        for invitation in invitations
    ]


@router.post("/invitations/{invitation_id}/accept", response_model=AccountProfileResponse)
def accept_current_user_organization_invitation(
    invitation_id: str,
    context: RequestContext = Depends(get_request_context)
) -> AccountProfileResponse:
    _require_profile(context)

    try:
        profile = accept_organization_invitation(
            invitation_id=invitation_id,
            user_id=context.user_id,
            email=context.email or ""
        )
    except DatabaseNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc)
        ) from exc

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found."
        )

    return AccountProfileResponse(
        user_id=profile.user_id,
        organization_id=profile.organization_id,
        organization_name=None,
        auth_user_id=profile.auth_user_id,
        email=profile.email,
        name=profile.name,
        avatar_url=profile.avatar_url,
        job_title=profile.job_title,
        role=profile.role
    )


@router.delete("/team/{user_id}", response_model=TeamMemberResponse)
def remove_current_user_team_member(
    user_id: str,
    context: RequestContext = Depends(get_request_context)
) -> TeamMemberResponse:
    _require_owner(context)

    if user_id == context.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owners cannot remove themselves."
        )

    try:
        member = remove_team_member_from_organization(
            organization_id=context.organization_id,
            user_id=user_id
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
