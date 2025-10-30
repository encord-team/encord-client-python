import logging
from datetime import datetime
from typing import Iterator, List, Optional, Sequence, Tuple, Union
from uuid import UUID

import encord.orm.storage as orm_storage
from encord.client import EncordClientProject
from encord.exceptions import (
    AuthorisationError,
)
from encord.filter_preset import FilterPreset
from encord.http.v2.api_client import ApiClient
from encord.objects.ontology_labels_impl import LabelRowV2
from encord.ontology import Ontology
from encord.orm.collection import Collection as OrmCollection
from encord.orm.collection import (
    CollectionBulkItemRequest,
    CollectionBulkItemResponse,
    CollectionBulkPresetRequest,
    CreateCollectionParams,
    CreateCollectionPayload,
    CreateProjectCollectionParams,
    CreateProjectCollectionPayload,
    GetCollectionItemsParams,
    GetCollectionParams,
    GetCollectionsResponse,
    GetProjectCollectionParams,
    ProjectCollectionBulkItemRequest,
    ProjectCollectionBulkItemResponse,
    ProjectCollectionType,
    ProjectDataCollectionInstance,
    ProjectDataCollectionItemRequest,
    ProjectDataCollectionItemResponse,
    ProjectLabelCollectionInstance,
    ProjectLabelCollectionItemRequest,
    ProjectLabelCollectionItemResponse,
    UpdateCollectionPayload,
)
from encord.orm.collection import ProjectCollection as OrmProjectCollection
from encord.orm.label_row import LabelRowMetadata, label_row_metadata_dto_to_label_row_metadata
from encord.storage import StorageItem, StorageItemInaccessible

log = logging.getLogger(__name__)


class Collection:
    """Represents collections in Index.
    Collections are a logical grouping of data items that can be used to
    create datasets and perform various data curation flows.
    """

    def __init__(self, client: ApiClient, orm_collection: OrmCollection):
        self._client = client
        self._collection_instance = orm_collection

    @property
    def uuid(self) -> UUID:
        """Get the collection unique identifier (UUID).

        Returns:
            UUID: The collection UUID.
        """
        return self._collection_instance.uuid

    @property
    def name(self) -> str:
        """Get the collection name.

        Returns:
            str: The collection name.
        """
        return self._collection_instance.name

    @property
    def description(self) -> Optional[str]:
        """Get the collection description.

        Returns:
            Optional[str]: The collection description, or None if not available.
        """
        return self._collection_instance.description

    @property
    def created_at(self) -> Optional[datetime]:
        """Get the collection creation timestamp.

        Returns:
            Optional[datetime]: The timestamp when the collection was created, or None if not available.
        """
        return self._collection_instance.created_at

    @property
    def last_edited_at(self) -> Optional[datetime]:
        """Get the collection last edit timestamp.

        Returns:
            Optional[datetime]: The timestamp when the collection was last edited, or None if not available.
        """
        return self._collection_instance.last_edited_at

    @property
    def top_level_folder_uuid(self) -> UUID:
        """Get the uuid of the top level folder that the collection is on.

        Returns:
            UUID: the uuid of the top level folder that the collection is on
        """
        return self._collection_instance.top_level_folder_uuid

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
        top_level_folder_uuid: Union[UUID, None],
        collection_uuids: Union[List[UUID], None],
        page_size: Optional[int] = None,
    ) -> Iterator["Collection"]:
        params = GetCollectionParams(
            topLevelFolderUuid=top_level_folder_uuid, uuids=collection_uuids, pageSize=page_size
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

    def update_collection(self, name: Optional[str] = None, description: Optional[str] = None) -> None:
        """Update the collection's name and/or description.

        Args:
           name (Optional[str]): The new name for the collection.
           description (Optional[str]): The new description for the collection.
        """
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
    ) -> Iterator[StorageItem]:
        """List storage items in the collection.

        Args:
            page_size (Optional[int]): The number of items to fetch per page.

        Returns:
            Iterator[StorageItem]: An iterator containing storage items in the collection.
        """
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
    ) -> Iterator[Union[StorageItem, StorageItemInaccessible]]:
        """List storage items in the collection, including those that are inaccessible.

        Args:
            page_size (Optional[int]): The number of items to fetch per page.

        Returns:
            Iterator[Union[StorageItem, StorageItemInaccessible]]: An iterator containing both accessible
            and inaccessible storage items in the collection.
        """
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

    def add_items(self, storage_item_uuids: Sequence[Union[UUID, str]]) -> CollectionBulkItemResponse:
        """Add storage items to the collection.

        Args:
            storage_item_uuids (Sequence[Union[UUID, str]]): The list of storage item UUIDs to be added.
            Either UUIDs or string representations of UUIDs are accepted.

        Returns:
            CollectionBulkItemResponse: The response after adding items to the collection.
        """
        uuid_list = [item if isinstance(item, UUID) else UUID(item) for item in storage_item_uuids]
        res = self._client.post(
            f"index/collections/{self.uuid}/add-items",
            params=None,
            payload=CollectionBulkItemRequest(item_uuids=uuid_list),
            result_type=CollectionBulkItemResponse,
        )
        return res

    def remove_items(self, storage_item_uuids: Sequence[Union[UUID, str]]) -> CollectionBulkItemResponse:
        """Remove storage items from the collection.

        Args:
            storage_item_uuids (Sequence[Union[UUID, str]]): The list of storage item UUIDs to be removed.
            Either UUIDs or string representations of UUIDs are accepted.

        Returns:
            CollectionBulkItemResponse: The response after removing items from the collection.
        """
        uuid_list = [item if isinstance(item, UUID) else UUID(item) for item in storage_item_uuids]
        res = self._client.post(
            f"index/collections/{self.uuid}/remove-items",
            params=None,
            payload=CollectionBulkItemRequest(item_uuids=uuid_list),
            result_type=CollectionBulkItemResponse,
        )
        return res

    def add_preset_items(self, filter_preset: Union[FilterPreset, UUID, str]) -> None:
        """Async operation to add storage items matching a filter preset to the collection.

        Args:
             filter_preset (Union[FilterPreset, UUID, str]): The filter preset or its UUID/ID used to filter items.
        """
        if isinstance(filter_preset, FilterPreset):
            preset_uuid = filter_preset.uuid
        elif isinstance(filter_preset, str):
            preset_uuid = UUID(filter_preset)
        else:
            preset_uuid = filter_preset
        self._client.post(
            f"index/collections/{self.uuid}/add-preset-items",
            params=None,
            payload=CollectionBulkPresetRequest(preset_uuid=preset_uuid),
            result_type=None,
        )
        log.info(
            f"Submitted request to add items matching filter_preset:{preset_uuid} to collection:{self.uuid}."
            f"It is an async operation and can take some time to complete."
        )

    def remove_preset_items(self, filter_preset: Union[FilterPreset, UUID, str]) -> None:
        """Async operation to remove storage items matching a filter preset from the collection.

        Args:
            filter_preset (Union[FilterPreset, UUID, str]): The filter preset or its UUID/ID used to filter items.
        """
        if isinstance(filter_preset, FilterPreset):
            preset_uuid = filter_preset.uuid
        elif isinstance(filter_preset, str):
            preset_uuid = UUID(filter_preset)
        else:
            preset_uuid = filter_preset
        self._client.post(
            f"index/collections/{self.uuid}/remove-preset-items",
            params=None,
            payload=CollectionBulkPresetRequest(preset_uuid=preset_uuid),
            result_type=None,
        )
        log.info(
            f"Submitted request to remove items matching filter_preset:{preset_uuid} from collection:{self.uuid}."
            f"It is an async operation and can take some time to complete."
        )


class ProjectCollection:
    """Represents Active collections inside a Project.
    Active Project Collections are a logical grouping of frames (images or video frames) or
    annotations (objects and classifications) that can be used to perform various data curation flows.
    """

    def __init__(
        self,
        project_uuid: UUID,
        project_client: EncordClientProject,
        ontology: Ontology,
        orm_collection: OrmProjectCollection,
    ):
        self._project_uuid = project_uuid
        self._client = project_client._api_client
        self._project_client = project_client
        self._ontology = ontology
        self._collection_instance = orm_collection

    @property
    def uuid(self) -> UUID:
        """Get the collection unique identifier (UUID).

        Returns:
            UUID: The collection UUID.
        """
        return self._collection_instance.collection_uuid

    @property
    def name(self) -> str:
        """Get the collection name.

        Returns:
            str: The collection name.
        """
        return self._collection_instance.name

    @property
    def description(self) -> Optional[str]:
        """Get the collection description.

        Returns:
            Optional[str]: The collection description, or None if not available.
        """
        return self._collection_instance.description

    @property
    def created_at(self) -> Optional[datetime]:
        """Get the collection creation timestamp.

        Returns:
            Optional[datetime]: The timestamp when the collection was created, or None if not available.
        """
        return self._collection_instance.created_at

    @property
    def last_edited_at(self) -> Optional[datetime]:
        """Get the collection last edit timestamp.

        Returns:
            Optional[datetime]: The timestamp when the collection was last edited, or None if not available.
        """
        return self._collection_instance.last_edited_at

    @property
    def collection_type(self) -> ProjectCollectionType:
        """Get the type of the collection.

        Returns:
            ProjectCollectionType: The type of the collection.
        """
        return self._collection_instance.collection_type

    @property
    def project_hash(self) -> UUID:
        """Get the project hash of the collection.

        Returns:
            UUID: The project hash of the collection.
        """
        return self._collection_instance.project_uuid

    @staticmethod
    def _get_collection(
        project_client: EncordClientProject,
        ontology: Ontology,
        project_uuid: UUID,
        collection_uuid: UUID,
    ) -> "ProjectCollection":
        params = GetProjectCollectionParams(uuids=[collection_uuid])
        orm_items = list(
            project_client._api_client.get_paged_iterator(
                f"active/{project_uuid}/collections",
                params=params,
                result_type=OrmProjectCollection,
            )
        )
        if len(orm_items) > 0:
            return ProjectCollection(
                project_uuid=project_uuid,
                project_client=project_client,
                ontology=ontology,
                orm_collection=orm_items[0],
            )
        raise AuthorisationError("No collection found")

    @staticmethod
    def _list_collections(
        project_client: EncordClientProject,
        ontology: Ontology,
        project_uuid: UUID,
        collection_uuids: Union[List[UUID], None],
        page_size: Optional[int] = None,
    ) -> Iterator["ProjectCollection"]:
        params = GetProjectCollectionParams(projectHash=project_uuid, uuids=collection_uuids, pageSize=page_size)
        paged_collections = project_client._api_client.get_paged_iterator(
            f"active/{project_uuid}/collections",
            params=params,
            result_type=OrmProjectCollection,
        )
        for collection in paged_collections:
            yield ProjectCollection(
                project_uuid=project_uuid,
                project_client=project_client,
                ontology=ontology,
                orm_collection=collection,
            )

    @staticmethod
    def _delete_collection(client: ApiClient, project_uuid: UUID, collection_uuid: UUID) -> None:
        client.delete(
            f"active/{project_uuid}/collections/{collection_uuid}",
            params=None,
            result_type=None,
        )

    @staticmethod
    def _create_collection(
        client: ApiClient,
        project_uuid: UUID,
        name: str,
        description: str = "",
        collection_type: ProjectCollectionType = ProjectCollectionType.FRAME,
    ) -> UUID:
        params = CreateProjectCollectionParams(projectHash=project_uuid)
        payload = CreateProjectCollectionPayload(name=name, description=description, collection_type=collection_type)
        return client.post(
            f"active/{project_uuid}/collections",
            params=params,
            payload=payload,
            result_type=UUID,
            allow_retries=False,
        )

    def update_collection(self, name: Optional[str] = None, description: Optional[str] = None) -> None:
        """Update the collection's name and/or description.

        Args:
           name (Optional[str]): The new name for the collection.
           description (Optional[str]): The new description for the collection.
        """
        payload = UpdateCollectionPayload(name=name, description=description)
        self._client.patch(
            f"active/{self._project_uuid}/collections/{self.uuid}",
            params=None,
            payload=payload,
            result_type=None,
        )

    def list_frames(
        self,
        page_size: Optional[int] = None,
    ) -> Iterator[Tuple[LabelRowV2, List[ProjectDataCollectionInstance]]]:
        """List frames in the collection.

        Args:
            page_size (Optional[int]): The number of items to fetch per page.

        Returns:
            Iterator[Tuple[LabelRowV2, List[ProjectDataCollectionInstance]]]: An list of tuples containing label
            row and corresponding frame instances in the collection.
        """
        params = GetCollectionItemsParams(pageSize=page_size)
        paged_items = self._client.get_paged_iterator(
            f"active/{self._project_uuid}/collections/{self.uuid}/items",
            params=params,
            result_type=ProjectDataCollectionItemResponse,
        )

        for item in paged_items:
            yield (
                LabelRowV2(
                    label_row_metadata_dto_to_label_row_metadata(item.label_row_metadata),
                    self._project_client,
                    self._ontology,
                ),
                item.instances,
            )

    def list_annotations(
        self,
        page_size: Optional[int] = None,
    ) -> Iterator[Tuple[LabelRowV2, List[ProjectLabelCollectionInstance]]]:
        """List annotations in the collection.

        Args:
            page_size (Optional[int]): The number of items to fetch per page.

        Returns:
            Iterator[Tuple[LabelRowV2, List[ProjectLabelCollectionInstance]]]: An list of tuples containing label
            row and corresponding label instances in the collection.
        """
        params = GetCollectionItemsParams(pageSize=page_size)
        paged_items = self._client.get_paged_iterator(
            f"active/{self._project_uuid}/collections/{self.uuid}/items?getLabels=true",
            params=params,
            result_type=ProjectLabelCollectionItemResponse,
        )

        for item in paged_items:
            yield (
                LabelRowV2(
                    label_row_metadata_dto_to_label_row_metadata(item.label_row_metadata),
                    self._project_client,
                    self._ontology,
                ),
                item.instances,
            )

    def add_items(
        self, items: List[Union[ProjectDataCollectionItemRequest, ProjectLabelCollectionItemRequest]]
    ) -> ProjectCollectionBulkItemResponse:
        """Add data items to the collection.

        Args:
            items (Sequence[ProjectDataCollectionItemRequest | ProjectLabelCollectionItemRequest]): The list of data items to be added.

        Returns:
            ProjectCollectionBulkItemResponse: The response after adding items to the collection.
        """
        res = self._client.post(
            f"active/{self._project_uuid}/collections/{self.uuid}/add-items",
            params=None,
            payload=ProjectCollectionBulkItemRequest(items=items),
            result_type=ProjectCollectionBulkItemResponse,
        )
        return res

    def remove_items(
        self, items: List[Union[ProjectDataCollectionItemRequest, ProjectLabelCollectionItemRequest]]
    ) -> ProjectCollectionBulkItemResponse:
        """Remove data items from the collection.

        Args:
            items (Sequence[ProjectDataCollectionItemRequest | ProjectLabelCollectionItemRequest]): The list of data items to be removed.

        Returns:
            ProjectCollectionBulkItemResponse: The response after removing items from the collection.
        """
        res = self._client.post(
            f"active/{self._project_uuid}/collections/{self.uuid}/remove-items",
            params=None,
            payload=ProjectCollectionBulkItemRequest(items=items),
            result_type=ProjectCollectionBulkItemResponse,
        )
        return res

    def add_preset_items(self, filter_preset: Union[FilterPreset, UUID, str]) -> None:
        """Async operation to add storage items matching a filter preset to the collection.

        Args:
             filter_preset (Union[FilterPreset, UUID, str]): The filter preset or its UUID/ID used to filter items.
        """
        if isinstance(filter_preset, FilterPreset):
            preset_uuid = filter_preset.uuid
        elif isinstance(filter_preset, str):
            preset_uuid = UUID(filter_preset)
        else:
            preset_uuid = filter_preset
        self._client.post(
            f"active/{self._project_uuid}/collections/{self.uuid}/add-preset-items",
            params=None,
            payload=CollectionBulkPresetRequest(preset_uuid=preset_uuid),
            result_type=None,
        )
        log.info(
            f"Submitted request to add items matching filter_preset:{preset_uuid} to collection:{self.uuid}."
            f"It is an async operation and can take some time to complete."
        )

    def remove_preset_items(self, filter_preset: Union[FilterPreset, UUID, str]) -> None:
        """Async operation to remove storage items matching a filter preset from the collection.

        Args:
            filter_preset (Union[FilterPreset, UUID, str]): The filter preset or its UUID/ID used to filter items.
        """
        if isinstance(filter_preset, FilterPreset):
            preset_uuid = filter_preset.uuid
        elif isinstance(filter_preset, str):
            preset_uuid = UUID(filter_preset)
        else:
            preset_uuid = filter_preset
        self._client.post(
            f"active/{self._project_uuid}/collections/{self.uuid}/remove-preset-items",
            params=None,
            payload=CollectionBulkPresetRequest(preset_uuid=preset_uuid),
            result_type=None,
        )
        log.info(
            f"Submitted request to remove items matching filter_preset:{preset_uuid} from collection:{self.uuid}."
            f"It is an async operation and can take some time to complete."
        )
