"""---
title: "Group"
slug: "sdk-ref-group"
hidden: false
metadata:
  title: "Group"
  description: "Encord SDK Group class."
category: "64e481b57b6027003f20aaa0"
---
"""

import logging
from datetime import datetime
from typing import Iterator, List, Optional
from uuid import UUID

from encord.http.v2.api_client import ApiClient
from encord.http.v2.payloads import Page
from encord.orm.group import (
    AddGroupUsersPayload,
    CreateGroupPayload,
    EditGroupPayload,
    GroupUser,
    RemoveGroupUsersPayload,
)
from encord.orm.group import Group as OrmGroup

log = logging.getLogger(__name__)


class Group:
    """Represents a group of users within an organization.

    Groups can be granted access to projects, datasets, ontologies, and storage
    folders, and are a convenient way to manage permissions for several users at
    once. Obtain instances of this class via
    :meth:`encord.user_client.EncordUserClient.create_group`,
    :meth:`encord.user_client.EncordUserClient.get_group`, or
    :meth:`encord.user_client.EncordUserClient.list_groups`.
    """

    def __init__(self, api_client: ApiClient, orm_group: OrmGroup):
        self._client = api_client
        self._group_instance = orm_group

    @property
    def group_hash(self) -> UUID:
        """Get the group unique identifier (UUID).

        Returns:
            UUID: The group UUID.
        """
        return self._group_instance.group_hash

    @property
    def name(self) -> str:
        """Get the group name.

        Returns:
            str: The group name.
        """
        return self._group_instance.name

    @property
    def description(self) -> str:
        """Get the group description.

        Returns:
            str: The group description.
        """
        return self._group_instance.description

    @property
    def created_at(self) -> datetime:
        """Get the group creation timestamp.

        Returns:
            datetime: The timestamp when the group was created.
        """
        return self._group_instance.created_at

    @staticmethod
    def _create_group(api_client: ApiClient, name: str, description: str = "") -> "Group":
        payload = CreateGroupPayload(name=name, description=description)
        orm_group = api_client.post(
            "organisation/groups",
            params=None,
            payload=payload,
            result_type=OrmGroup,
        )
        return Group(api_client, orm_group)

    @staticmethod
    def _list_groups(api_client: ApiClient) -> Iterator["Group"]:
        page = api_client.get(
            "user/current-organisation/groups",
            params=None,
            result_type=Page[OrmGroup],
        )
        for orm_group in page.results:
            yield Group(api_client, orm_group)

    @staticmethod
    def _get_group(api_client: ApiClient, group_hash: UUID) -> "Group":
        orm_group = api_client.get(
            f"organisation/groups/{group_hash}",
            params=None,
            result_type=OrmGroup,
        )
        return Group(api_client, orm_group)

    @staticmethod
    def _delete_group(api_client: ApiClient, group_hash: UUID) -> None:
        api_client.delete(
            f"organisation/groups/{group_hash}",
            params=None,
            result_type=None,
        )

    def update_group(self, name: Optional[str] = None, description: Optional[str] = None) -> None:
        """Update the group's name and/or description.

        At least one of ``name`` or ``description`` must be provided. Fields left
        as ``None`` are not modified.

        Args:
            name: The new name for the group.
            description: The new description for the group.
        """
        if name is None and description is None:
            raise ValueError("At least one of 'name' or 'description' must be provided.")
        payload = EditGroupPayload(name=name, description=description)
        self._group_instance = self._client.patch(
            f"organisation/groups/{self.group_hash}",
            params=None,
            payload=payload,
            result_type=OrmGroup,
        )

    def list_users(self) -> Iterator[GroupUser]:
        """List the users belonging to the group.

        Returns:
            Iterator[GroupUser]: The users that belong to the group.
        """
        page = self._client.get(
            f"organisation/groups/{self.group_hash}/users",
            params=None,
            result_type=Page[GroupUser],
        )
        yield from page.results

    def add_users(self, user_emails: List[str]) -> List[GroupUser]:
        """Add users to the group by email address.

        All emails must belong to existing members of the organization; the
        request fails with an authorization error if any do not. To add
        someone to the organization first, see
        :meth:`encord.user_client.EncordUserClient.add_organisation_user`.

        Args:
            user_emails: The email addresses of the users to add.

        Returns:
            List[GroupUser]: The full list of users in the group after the addition.
        """
        payload = AddGroupUsersPayload(user_emails=user_emails)
        page = self._client.post(
            f"organisation/groups/{self.group_hash}/users",
            params=None,
            payload=payload,
            result_type=Page[GroupUser],
        )
        return page.results

    def remove_users(self, user_emails: List[str]) -> None:
        """Remove users from the group by email address.

        Emails that are not in the group are ignored.

        Args:
            user_emails: The email addresses of the users to remove.
        """
        payload = RemoveGroupUsersPayload(user_emails=user_emails)
        self._client.post(
            f"organisation/groups/{self.group_hash}/users/bulk-delete",
            params=None,
            payload=payload,
            result_type=None,
        )
