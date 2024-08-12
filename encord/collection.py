import uuid
from datetime import datetime
from pathlib import Path
from typing import Collection, Dict, Iterable, List, Optional, TextIO, Union
from uuid import UUID
from encord.http.v2.api_client import ApiClient
from encord.orm.collection import Collection as OrmCollection, GetCollectionParams, GetCollectionsResponse, \
    CreateCollectionParams, CreateCollectionPayload, UpdateCollectionPayload
from encord.exceptions import (
    AuthenticationError,
    AuthorisationError,
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
    def collection_hash(self) -> uuid.UUID:
        """
        Get the collection hash (i.e. the collection ID).

        Returns:
            str: The collection hash.
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

    @staticmethod
    def _get_collection(api_client: ApiClient, collection_uuid: UUID) -> "Collection":
        params = GetCollectionParams(collection_uuids=[collection_uuid])
        orm_item = api_client.get(
            f"index/collections",
            params=params,
            result_type=GetCollectionsResponse,
        )
        if len(orm_item.results) > 0:
            return Collection(api_client, orm_item.results[0])
        raise AuthorisationError("Collection not found")

    @staticmethod
    def _get_collections(api_client: ApiClient, top_level_folder_uuid: UUID | None, collection_uuids) -> "List[Collection]":
        params = GetCollectionParams(top_level_folder_uuid=top_level_folder_uuid, collection_uuids=collection_uuids)
        orm_item = api_client.get(
            f"index/collections",
            params=params,
            result_type=GetCollectionsResponse,
        )
        collections = [Collection(api_client, item) for item in orm_item.results ]
        return collections

    @staticmethod
    def _delete_collection(api_client: ApiClient, collection_uuid: UUID) -> None:
        orm_item = api_client.delete(
            f"index/collections/{collection_uuid}",
            params=None,
            result_type=None,
        )
        print("response is: ", orm_item)

    @staticmethod
    def _create_collection(api_client: ApiClient, top_level_folder_uuid: UUID, name: str, description: str = "") -> UUID:
        params = CreateCollectionParams(top_level_folder_uuid=top_level_folder_uuid)
        payload = CreateCollectionPayload(name=name, description=description)
        orm_item = api_client.post(
            f"index/collections",
            params=params,
            payload=payload,
            result_type=UUID,
        )
        print("response is: ", orm_item)
        return orm_item

    @staticmethod
    def _update_collection(api_client: ApiClient, collection_uuid: UUID, name: str | None = None,
                           description: str | None = None) -> None:
        payload = UpdateCollectionPayload(name=name, description=description)
        orm_item = api_client.patch(
            f"index/collections/{collection_uuid}",
            params=None,
            payload=payload,
            result_type=None,
        )
        print("response is: ", orm_item)

