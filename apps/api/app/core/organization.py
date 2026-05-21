from app.core.config import settings


def get_current_organization_id() -> str:
    """
    Return the organization scope for the current request.

    The MVP does not have authentication yet, so every request is scoped to the
    development organization from DEFAULT_ORGANIZATION_ID. Keeping this in one
    helper makes the temporary path easy to replace when auth lands.
    """
    return settings.default_organization_id

