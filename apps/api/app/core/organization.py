from fastapi import Depends

from app.core.auth import RequestContext, get_request_context


def get_current_organization_id(
    context: RequestContext = Depends(get_request_context)
) -> str:
    """
    Return the organization scope for the current request.

    Authenticated requests use the organization resolved from the bearer token
    and Averion profile. Local development can still fall back to the default
    organization while AUTH_REQUIRED is false.
    """
    return context.organization_id
