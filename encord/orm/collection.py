import uuid
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional, Union
from uuid import UUID

from encord.orm.base_dto import BaseDTO, Field
from encord.orm.label_row import LabelRowMetadataDTO


class GetCollectionParams(BaseDTO):
    top_level_folder_uuid: Optional[UUID] = Field(default=None, alias="topLevelFolderUuid")
    collection_uuids: Optional[list[UUID]] = Field(default=[], alias="uuids")
    page_token: Optional[str] = Field(default=None, alias="pageToken")
    page_size: Optional[int] = Field(default=None, alias="pageSize")


class CreateCollectionParams(BaseDTO):
    top_level_folder_uuid: Optional[UUID] = Field(default=None, alias="topLevelFolderUuid")


class GetCollectionItemsParams(BaseDTO):
    page_token: Optional[str] = Field(default=None, alias="pageToken")
    page_size: Optional[int] = Field(default=None, alias="pageSize")


class CreateCollectionPayload(BaseDTO):
    name: str
    description: Optional[str] = ""


class UpdateCollectionPayload(BaseDTO):
    name: Optional[str] = None
    description: Optional[str] = None


class Collection(BaseDTO):
    uuid: uuid.UUID
    top_level_folder_uuid: UUID = Field(alias="topLevelFolderUuid")
    name: str
    description: Optional[str]
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    last_edited_at: Optional[datetime] = Field(default=None, alias="lastEditedAt")


class GetCollectionsResponse(BaseDTO):
    results: list[Collection]


class CollectionBulkItemRequest(BaseDTO):
    item_uuids: list[uuid.UUID]


class CollectionBulkItemResponse(BaseDTO):
    failed_items: list[uuid.UUID]


class CollectionBulkPresetRequest(BaseDTO):
    preset_uuid: uuid.UUID


class ProjectCollectionType(Enum):
    FRAME = "FRAME"
    LABEL = "LABEL"


class GetProjectCollectionParams(BaseDTO):
    project_hash: Optional[uuid.UUID] = Field(default=None, alias="projectHash")
    collection_uuids: Optional[list[uuid.UUID]] = Field(default=[], alias="uuids")
    page_token: Optional[str] = Field(default=None, alias="pageToken")
    page_size: Optional[int] = Field(default=None, alias="pageSize")


class CreateProjectCollectionParams(BaseDTO):
    project_hash: Optional[uuid.UUID] = Field(default=None, alias="projectHash")


class CreateProjectCollectionPayload(CreateCollectionPayload):
    collection_type: ProjectCollectionType


class ProjectCollection(BaseDTO):
    collection_uuid: UUID
    name: str
    description: Optional[str]
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    last_edited_at: Optional[datetime] = Field(default=None, alias="lastEditedAt")
    project_uuid: UUID
    collection_type: ProjectCollectionType


class GetProjectCollectionsResponse(BaseDTO):
    results: list[ProjectCollection]


class ProjectDataCollectionInstance(BaseDTO):
    frame: int


class ProjectLabelCollectionInstance(BaseDTO):
    frame: int
    annotation_id: str


class ProjectDataCollectionItemResponse(BaseDTO):
    label_row_metadata: LabelRowMetadataDTO
    instances: list[ProjectDataCollectionInstance]


class ProjectLabelCollectionItemResponse(BaseDTO):
    label_row_metadata: LabelRowMetadataDTO
    instances: list[ProjectLabelCollectionInstance]


class ProjectDataCollectionItemRequest(BaseDTO):
    data_uuid: Union[str, UUID]
    frame: int


class ProjectLabelCollectionItemRequest(BaseDTO):
    data_uuid: Union[str, UUID]
    frame: int
    annotation_id: str


class ProjectCollectionBulkItemRequest(BaseDTO):
    items: list[Union[ProjectDataCollectionItemRequest, ProjectLabelCollectionItemRequest]]


class ProjectCollectionBulkItemResponse(BaseDTO):
    failed_items: list[Union[ProjectDataCollectionItemRequest, ProjectLabelCollectionItemRequest]]
