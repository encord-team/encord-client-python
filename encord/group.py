from typing import Any, Dict, Optional
from uuid import UUID

import encord.orm.group as orm_group
from encord.http.v2.api_client import ApiClient


class Group:
    def __init__(self, api_client: ApiClient, orm_group: orm_group.Group):
        self._api_client = api_client
        self._orm_group = orm_group
        self._parsed_metadata: Optional[Dict[str, Any]] = None

    @property
    def uuid(self) -> UUID:
        return self._orm_group.group_hash

    @property
    def name(self) -> str:
        return self._orm_group.name

    @property
    def description(self) -> str:
        return self._orm_group.description

    @staticmethod
    def _get_groups(api_client: ApiClient) -> "Group":
        orm_folder = api_client.get(
            f"/user/current_organisation/groups", params=None, result_type=orm_group.Group
        )
        return Group(api_client, orm_folder)
