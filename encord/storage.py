import json
from typing import Any, Dict, Optional
from uuid import UUID

import encord.orm.storage as orm_storage
from encord.http.v2.api_client import ApiClient


class StorageFolder:
    def __init__(self, api_client: ApiClient, orm_folder: orm_storage.StorageFolder):
        self._api_client = api_client
        self._orm_folder = orm_folder
        self._parsed_metadata: Optional[Dict[str, Any]] = None

    @property
    def uuid(self) -> UUID:
        return self._orm_folder.uuid

    @property
    def parent_uuid(self) -> Optional[UUID]:
        return self._orm_folder.parent

    @property
    def parent(self) -> Optional["StorageFolder"]:
        parent_uuid = self._orm_folder.parent
        return None if parent_uuid is None else self._get_folder(self._api_client, parent_uuid)

    @property
    def name(self) -> str:
        return self._orm_folder.name

    @property
    def description(self) -> str:
        return self._orm_folder.description

    @property
    def client_metadata(self) -> Optional[Dict[str, Any]]:
        if self._parsed_metadata is None:
            if self._orm_folder.client_metadata is not None:
                self._parsed_metadata = json.loads(self._orm_folder.client_metadata)
        return self._parsed_metadata

    def delete(self):
        self._api_client.delete(f"storage/folders/{self.uuid}", params=None, result_type=None)

    @staticmethod
    def _get_folder(api_client: ApiClient, folder_uuid: UUID) -> "StorageFolder":
        orm_folder = api_client.get(
            f"storage/folders/{folder_uuid}", params=None, result_type=orm_storage.StorageFolder
        )
        return StorageFolder(api_client, orm_folder)
