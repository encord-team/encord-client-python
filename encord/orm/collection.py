import uuid
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional, Union
from uuid import UUID

from encord.orm.base_dto import BaseDTO, Field
from encord.orm.label_row import LabelRowMetadataDTO


class GetCollectionParams(BaseDTO):
    """Query parameters for listing Collections in a top-level folder.

    Args:
        top_level_folder_uuid: Optional UUID of the top-level folder to restrict results to.
            If omitted, Collections from all accessible top-level folders
            may be returned.
        collection_uuids: Optional list of Collection UUIDs to filter by. If provided,
            only Collections with these UUIDs are returned.
        page_token: Token for fetching the next page of results from a previous call.
        page_size: Maximum number of Collections to return in a single page.
    """

    top_level_folder_uuid: Optional[UUID] = Field(default=None, alias="topLevelFolderUuid")
    collection_uuids: Optional[List[UUID]] = Field(default=[], alias="uuids")
    page_token: Optional[str] = Field(default=None, alias="pageToken")
    page_size: Optional[int] = Field(default=None, alias="pageSize")


class CreateCollectionParams(BaseDTO):
    """Parameters for creating a new Collection in a top-level folder.

    Args:
        top_level_folder_uuid: Optional UUID of the top-level folder in which to create the
            Collection. If omitted, the default folder for the user or
            Project context may be used.
    """

    top_level_folder_uuid: Optional[UUID] = Field(default=None, alias="topLevelFolderUuid")


class GetCollectionItemsParams(BaseDTO):
    """Query parameters for listing items inside a Collection.

    Args:
        include_client_metadata: Optionally include client metadata into the result of this query.
        page_token: Token for fetching the next page of Collection items from a previous call.
        page_size: Maximum number of items to return in a single page.
    """

    include_client_metadata: Optional[bool] = Field(default=None, alias="includeClientMetadata")
    page_token: Optional[str] = Field(default=None, alias="pageToken")
    page_size: Optional[int] = Field(default=None, alias="pageSize")


class CreateCollectionPayload(BaseDTO):
    """Payload for creating a new Collection.

    Args:
        name: Human-readable name of the Collection.
        description: Optional free-text description of the Collection and its
            intended use.
    """

    name: str
    description: Optional[str] = ""


class UpdateCollectionPayload(BaseDTO):
    """Payload for updating an existing collection.

    Any field set to ``None`` is left unchanged on the server.

    Args:
        name: New name for the Collection. If omitted or ``None``, the name
            is not updated.
        description: New description for the Collection. If omitted or ``None``,
            the description is not updated.
    """

    name: Optional[str] = None
    description: Optional[str] = None


class Collection(BaseDTO):
    """Represents a top-level Collection of items in Index.

    Collections are logical groupings of storage items
    that can be used for data curation and downstream
    workflows.

    Args:
        uuid: Unique identifier of the Collection.
        top_level_folder_uuid: UUID of the top-level folder that owns this Collection.
        name: Human-readable name of the Collection.
        description: Optional free-text description of the Collection.
        created_at: Timestamp when the Collection was created.
        last_edited_at: Timestamp when the Collection was last modified.
    """

    uuid: uuid.UUID
    top_level_folder_uuid: UUID = Field(alias="topLevelFolderUuid")
    name: str
    description: Optional[str]
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    last_edited_at: Optional[datetime] = Field(default=None, alias="lastEditedAt")


class GetCollectionsResponse(BaseDTO):
    """Response payload for listing Collections.

    Args:
        results: List of Collections matching the query parameters.
    """

    results: List[Collection]


class CollectionBulkItemRequest(BaseDTO):
    """Request payload for bulk operations on Collection items.

    Args:
        item_uuids: UUIDs of items to include in the bulk operation. For example,
            to add or remove them from a Collection).
    """

    item_uuids: List[uuid.UUID]


class CollectionBulkItemResponse(BaseDTO):
    """Response payload for bulk operations on Collection items.

    Args:
        failed_items: UUIDs of items for which the bulk operation failed.
    """

    failed_items: List[uuid.UUID]


class CollectionBulkPresetRequest(BaseDTO):
    """Request payload for applying a preset to a Collection in bulk.

    Args:
        preset_uuid: UUID of the preset to apply to the Collection.
    """

    preset_uuid: uuid.UUID


class ProjectCollectionType(Enum):
    """Type of a project Collection.

    **Values**:

    - **FRAME:** The Collection groups frames or data items.
    - **LABEL:** The Collection groups labels or annotations.
    """

    FRAME = "FRAME"
    LABEL = "LABEL"


class GetProjectCollectionParams(BaseDTO):
    """Query parameters for listing project collections.

    Args:
        project_hash: UUID of the project whose Collections should be listed.
        collection_uuids: Optional list of project Collection UUIDs to filter by.
        page_token: Token for fetching the next page of project Collections from
            a previous call.
        page_size: Maximum number of project Collections to return in a single page.
    """

    project_hash: Optional[uuid.UUID] = Field(default=None, alias="projectHash")
    collection_uuids: Optional[List[uuid.UUID]] = Field(default=[], alias="uuids")
    page_token: Optional[str] = Field(default=None, alias="pageToken")
    page_size: Optional[int] = Field(default=None, alias="pageSize")


class CreateProjectCollectionParams(BaseDTO):
    """Parameters for creating a new project Collection.

    Args:
        project_hash: UUID of the Project in which to create the Collection.
    """

    project_hash: Optional[uuid.UUID] = Field(default=None, alias="projectHash")


class CreateProjectCollectionPayload(CreateCollectionPayload):
    """Payload for creating a new Project Collection.

    Inherits the generic collection creation fields and adds the Project
    Collection type.

    Args:
        collection_type: Type of the Project Collection (frame-based or label-based).
    """

    collection_type: ProjectCollectionType


class ProjectCollection(BaseDTO):
    """Represents a Collection that is scoped to a specific project.

    Project Collections are logical groupings of files or labels from a
    single Project that can be used for sampling, review, or other
    curation workflows.

    Args:
        collection_uuid: UUID of the underlying Collection.
        name: Human-readable name of the Project Collection.
        description: Optional description of the Project Collection.
        created_at: Timestamp when the Project Collection was created.
        last_edited_at: Timestamp when the Project Collection was last modified.
        project_uuid: UUID of the project this Collection belongs to.
        collection_type: Type of the project Collection (frame-based or label-based).
    """

    collection_uuid: UUID
    name: str
    description: Optional[str]
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    last_edited_at: Optional[datetime] = Field(default=None, alias="lastEditedAt")
    project_uuid: UUID
    collection_type: ProjectCollectionType


class GetProjectCollectionsResponse(BaseDTO):
    """Response payload for listing Project Collections.

    Args:
        results: List of Project Collections matching the query parameters.
    """

    results: List[ProjectCollection]


class ProjectDataCollectionInstance(BaseDTO):
    """Represents a single frame instance in a Project data Collection.

    Args:
        frame: Frame index within the data item that is part of the Collection.
    """

    frame: int


class ProjectLabelCollectionInstance(BaseDTO):
    """Represents a single label instance in a Project label Collection.

    Args:
        frame: Frame index within the data item for which the annotation
            was created.
        annotation_id: Identifier of the annotation included in the Collection.
    """

    frame: int
    annotation_id: str


class ProjectDataCollectionItemResponse(BaseDTO):
    """Response item describing frames included in a Project data Collection.

    Args:
        label_row_metadata: Metadata describing the label row associated with the frames.
        instances: List of frame instances that are part of the Collection.
    """

    label_row_metadata: LabelRowMetadataDTO
    instances: List[ProjectDataCollectionInstance]


class ProjectLabelCollectionItemResponse(BaseDTO):
    """Response item describing labels included in a Project label Collection.

    Args:
        label_row_metadata: Metadata describing the label row associated with the labels.
        instances: List of label instances that are part of the Collection.
    """

    label_row_metadata: LabelRowMetadataDTO
    instances: List[ProjectLabelCollectionInstance]


class ProjectDataCollectionItemRequest(BaseDTO):
    """Request payload describing a frame to be added to a Project data Collection.

    Args:
        data_uuid: UUID (or string identifier) of the data item containing the frame.
        frame: Frame index within the data item to include in the Collection.
    """

    data_uuid: Union[str, UUID]
    frame: int


class ProjectLabelCollectionItemRequest(BaseDTO):
    """Request payload describing a label to be added to a Project label Collection.

    Args:
        data_uuid: UUID (or string identifier) of the data item containing the label.
        frame: Frame index within the data item for which the annotation
            was created.
        annotation_id: Identifier of the annotation to include in the Collection.
    """

    data_uuid: Union[str, UUID]
    frame: int
    annotation_id: str


class ProjectCollectionBulkItemRequest(BaseDTO):
    """Request payload for bulk operations on Project Collection items.

    Args:
        items: List of data or label Collection item requests to include in
            the bulk operation.
    """

    items: List[Union[ProjectDataCollectionItemRequest, ProjectLabelCollectionItemRequest]]


class ProjectCollectionBulkItemResponse(BaseDTO):
    """Response payload for bulk operations on Project Collection items.

    Attributes:
        failed_items: Items for which the bulk operation failed. Each entry contains
            the original request that could not be processed successfully.
    """

    failed_items: List[Union[ProjectDataCollectionItemRequest, ProjectLabelCollectionItemRequest]]
