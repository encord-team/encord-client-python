from datetime import datetime
from typing import Literal
from uuid import UUID

from encord.orm.base_dto import BaseDTO

OrganisationUserRoleName = Literal["ADMIN", "MEMBER", "TASKER", "WORKFORCE_MANAGER"]
OrganisationMemberType = Literal["internal", "external"]


class AddOrganisationUserPayload(BaseDTO):
    email: str
    role_mnemonic_name: OrganisationUserRoleName
    member_type: OrganisationMemberType


class OrganisationUser(BaseDTO):
    """A member of the organization.

    ``role_mnemonic_name`` and ``member_type`` are plain strings rather than the
    constrained types used when adding a user, so that listing keeps working if
    the backend introduces new roles or member types.

    Args:
        email: Email address of the user.
        role_mnemonic_name: Mnemonic name of the user's organization role, for example ``"MEMBER"``.
        role_uuid: Identifier of the user's organization role.
        member_type: Whether the user is an ``"internal"`` member of the
            organization or an ``"external"`` collaborator.
        created_at: When the user joined the organization.
        last_edited_at: When the user's membership was last modified.
    """

    email: str
    role_mnemonic_name: str
    role_uuid: UUID
    member_type: str
    created_at: datetime
    last_edited_at: datetime
