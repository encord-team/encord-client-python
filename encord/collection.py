import uuid
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from encord.exceptions import (
    AuthorisationError,
)
from encord.http.v2.api_client import ApiClient
from encord.orm.collection import Collection as OrmCollection
from encord.orm.collection import (
    CreateCollectionParams,
    CreateCollectionPayload,
    GetCollectionParams,
    GetCollectionsResponse,
    UpdateCollectionPayload,
)


class Collection:
    """
    Represents collections in Index.
    Collections are a logical grouping of data items that can be used to
    create datasets and perform various data curation flows.
    """

    def __init__(self, client: ApiClient, orm_collection: OrmCollection):
        self._client = client
        self._collection_instance = orm_collection

    @property
    def uuid(self) -> uuid.UUID:
        """
        Get the collection uuid (i.e. the collection ID).

        Returns:
            str: The collection uuid.
        """
        return self._collection_instance.uuid

    @property
    def name(self) -> str:
        """
        Get the collection name

        Returns:
            str: The collection name.
        """
        return self._collection_instance.name

    @property
    def description(self) -> Optional[str]:
        """
        Get the collection description

        Returns:
            Optional[str]: The collection description.
        """
        return self._collection_instance.description

    @property
    def created_at(self) -> Optional[datetime]:
        """
        Get the collection creation timestamp

        Returns:
            Optional[datetime]: The collection creation timestamp.
        """
        return self._collection_instance.created_at

    @property
    def last_edited_at(self) -> Optional[datetime]:
        """
        Get the collection last edit timestamp

        Returns:
            Optional[datetime]: The collection last edit timestamp.
        """
        return self._collection_instance.last_edited_at

    @staticmethod
    def _get_collection(api_client: ApiClient, collection_uuid: UUID) -> "Collection":
        params = GetCollectionParams(uuids=[collection_uuid])
        orm_item = api_client.get(
            "index/collections",
            params=params,
            result_type=GetCollectionsResponse,
        )
        if len(orm_item.results) > 0:
            return Collection(api_client, orm_item.results[0])
        raise AuthorisationError("Collection not found")

    @staticmethod
    def _get_collections(
        api_client: ApiClient, top_level_folder_uuid: UUID | None, collection_uuids
    ) -> "List[Collection]":
        params = GetCollectionParams(topLevelFolderUuid=top_level_folder_uuid, uuids=collection_uuids)
        orm_item = api_client.get(
            "index/collections",
            params=params,
            result_type=GetCollectionsResponse,
        )
        collections = [Collection(api_client, item) for item in orm_item.results]
        return collections

    @staticmethod
    def _delete_collection(api_client: ApiClient, collection_uuid: UUID) -> None:
        api_client.delete(
            f"index/collections/{collection_uuid}",
            params=None,
            result_type=None,
        )

    @staticmethod
    def _create_collection(
        api_client: ApiClient, top_level_folder_uuid: UUID, name: str, description: str = ""
    ) -> UUID:
        params = CreateCollectionParams(topLevelFolderUuid=top_level_folder_uuid)
        payload = CreateCollectionPayload(name=name, description=description)
        orm_item = api_client.post(
            "index/collections",
            params=params,
            payload=payload,
            result_type=UUID,
        )
        return orm_item

    @staticmethod
    def _update_collection(
        api_client: ApiClient, collection_uuid: UUID, name: str | None = None, description: str | None = None
    ) -> None:
        payload = UpdateCollectionPayload(name=name, description=description)
        api_client.patch(
            f"index/collections/{collection_uuid}",
            params=None,
            payload=payload,
            result_type=None,
        )
