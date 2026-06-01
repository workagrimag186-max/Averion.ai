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
    organization_id: str | None = None
    name: str | None = None
    avatar_url: str | None = None
    job_title: str | None = None
    role: str = "owner"
    organization_name: str | None = None


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


@dataclass(frozen=True)
class TeamMember:
    user_id: str
    email: str
    name: str | None
    job_title: str | None
    role: str


@dataclass(frozen=True)
class Team:
    organization_id: str
    organization_name: str
    members: list[TeamMember]


def _ensure_organization(
    cursor,
    organization_id: str,
    name: str = "Development Organization"
) -> None:
    cursor.execute(
        """
        insert into organizations (id, name)
        values (%s::uuid, %s)
        on conflict (id) do nothing
        """,
        (
            organization_id,
            name
        )
    )


def _workspace_name_for_profile(profile: AuthProfileCreate) -> str:
    if profile.organization_name and profile.organization_name.strip():
        return profile.organization_name.strip()

    if profile.name and profile.name.strip():
        return f"{profile.name.strip()}'s Workspace"

    email_name = profile.email.split("@", maxsplit=1)[0].strip()
    return f"{email_name or 'Averion'}'s Workspace"


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


def _row_to_team_member(row) -> TeamMember:
    return TeamMember(
        user_id=row[0],
        email=row[1],
        name=row[2],
        job_title=row[3],
        role=row[4]
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


def get_team(organization_id: str) -> Team | None:
    if not is_database_configured():
        raise DatabaseNotConfiguredError("DATABASE_URL is not configured.")

    with psycopg.connect(settings.database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                select id::text, name
                from organizations
                where id = %s::uuid
                """,
                (organization_id,)
            )
            organization_row = cursor.fetchone()

            if organization_row is None:
                return None

            cursor.execute(
                """
                select
                    id::text,
                    email,
                    name,
                    job_title,
                    role
                from users
                where organization_id = %s::uuid
                order by
                    case when role = 'owner' then 0 else 1 end,
                    email
                """,
                (organization_id,)
            )

            return Team(
                organization_id=organization_row[0],
                organization_name=organization_row[1],
                members=[
                    _row_to_team_member(row)
                    for row in cursor.fetchall()
                ]
            )


def update_organization_name(
    *,
    organization_id: str,
    name: str
) -> Team | None:
    if not is_database_configured():
        raise DatabaseNotConfiguredError("DATABASE_URL is not configured.")

    with psycopg.connect(settings.database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                update organizations
                set name = %s,
                    updated_at = now()
                where id = %s::uuid
                returning id::text
                """,
                (
                    name,
                    organization_id
                )
            )

            if cursor.fetchone() is None:
                return None

    return get_team(organization_id)


def update_team_member_role(
    *,
    organization_id: str,
    user_id: str,
    role: str
) -> TeamMember | None:
    if not is_database_configured():
        raise DatabaseNotConfiguredError("DATABASE_URL is not configured.")

    with psycopg.connect(settings.database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                update users
                set role = %s,
                    updated_at = now()
                where id = %s::uuid
                    and organization_id = %s::uuid
                returning
                    id::text,
                    email,
                    name,
                    job_title,
                    role
                """,
                (
                    role,
                    user_id,
                    organization_id
                )
            )

            row = cursor.fetchone()
            return _row_to_team_member(row) if row else None


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
                (profile.auth_user_id,)
            )
            existing_row = cursor.fetchone()

            if existing_row:
                cursor.execute(
                    """
                    update users
                    set
                        email = %s,
                        name = coalesce(%s, name),
                        avatar_url = coalesce(%s, avatar_url),
                        job_title = coalesce(%s, job_title),
                        updated_at = now()
                    where auth_user_id = %s::uuid
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
                        profile.email,
                        profile.name,
                        profile.avatar_url,
                        profile.job_title,
                        profile.auth_user_id
                    )
                )

                return _row_to_user_profile(cursor.fetchone())

            if profile.organization_id:
                organization_id = profile.organization_id
                _ensure_organization(
                    cursor,
                    organization_id,
                    _workspace_name_for_profile(profile)
                )
            else:
                cursor.execute(
                    """
                    insert into organizations (name)
                    values (%s)
                    returning id::text
                    """,
                    (_workspace_name_for_profile(profile),)
                )
                organization_id = cursor.fetchone()[0]

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
                    organization_id,
                    profile.auth_user_id,
                    profile.email,
                    profile.name,
                    profile.avatar_url,
                    profile.job_title,
                    profile.role
                )
            )

            return _row_to_user_profile(cursor.fetchone())
