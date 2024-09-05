import uuid
from datetime import datetime
from typing import Iterable, Iterator, List, Optional, Union
from uuid import UUID

import encord.orm.storage as orm_storage
from encord.exceptions import (
    AuthorisationError,
)
from encord.http.v2.api_client import ApiClient
from encord.orm.collection import Collection as OrmCollection
from encord.orm.collection import (
    CreateCollectionParams,
    CreateCollectionPayload,
    GetCollectionItemsParams,
    GetCollectionParams,
    GetCollectionsResponse,
    UpdateCollectionPayload,
)
from encord.storage import StorageItem, StorageItemInaccessible


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
        Get the collection unique identifier (UUID).

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
        raise AuthorisationError("No collection found")

    @staticmethod
    def _list_collections(
        api_client: ApiClient,
        top_level_folder_uuid: UUID | None,
        collection_uuid_list: List[UUID] | None,
        page_size: Optional[int] = None,
    ) -> "Iterable[Collection]":
        params = GetCollectionParams(
            topLevelFolderUuid=top_level_folder_uuid, uuids=collection_uuid_list, pageSize=page_size
        )
        paged_items = api_client.get_paged_iterator(
            "index/collections",
            params=params,
            result_type=OrmCollection,
        )
        for item in paged_items:
            yield Collection(api_client, item)

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

    def update_collection(self, name: str | None = None, description: str | None = None) -> None:
        payload = UpdateCollectionPayload(name=name, description=description)
        self._client.patch(
            f"index/collections/{self.uuid}",
            params=None,
            payload=payload,
            result_type=None,
        )

    def list_items(
        self,
        page_size: Optional[int] = None,
    ) -> Iterable[StorageItem]:
        params = GetCollectionItemsParams(pageSize=page_size)
        paged_items = self._client.get_paged_iterator(
            f"index/collections/{self.uuid}/accessible-items",
            params=params,
            result_type=orm_storage.StorageItem,
        )
        for item in paged_items:
            yield StorageItem(api_client=self._client, orm_item=item)

    def list_items_include_inaccessible(
        self, page_size: Optional[int] = None
    ) -> Iterable[StorageItem | StorageItemInaccessible]:
        params = GetCollectionItemsParams(pageSize=page_size)
        paged_items: Iterator[Union[orm_storage.StorageItem, orm_storage.StorageItemInaccessible]] = (
            self._client.get_paged_iterator(
                f"index/collections/{self.uuid}/all-items",
                params=params,
                result_type=Union[orm_storage.StorageItem, orm_storage.StorageItemInaccessible],  # type: ignore[arg-type]
            )
        )
        for item in paged_items:
            if isinstance(item, orm_storage.StorageItem):
                yield StorageItem(api_client=self._client, orm_item=item)
            else:
                yield StorageItemInaccessible(orm_item=item)
