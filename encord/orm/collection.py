import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from encord.orm.base_dto import BaseDTO, Field
from encord.orm.label_row import LabelRowMetadataDTO


class GetCollectionParams(BaseDTO):
    top_level_folder_uuid: Optional[uuid.UUID] = Field(default=None, alias="topLevelFolderUuid")
    collection_uuids: Optional[List[uuid.UUID]] = Field(default=[], alias="uuids")
    page_token: Optional[str] = Field(default=None, alias="pageToken")
    page_size: Optional[int] = Field(default=None, alias="pageSize")


class CreateCollectionParams(BaseDTO):
    top_level_folder_uuid: Optional[uuid.UUID] = Field(default=None, alias="topLevelFolderUuid")


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
    name: str
    description: Optional[str]
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    last_edited_at: Optional[datetime] = Field(default=None, alias="lastEditedAt")


class GetCollectionsResponse(BaseDTO):
    results: List[Collection]


class CollectionBulkItemRequest(BaseDTO):
    item_uuids: List[uuid.UUID]


class CollectionBulkItemResponse(BaseDTO):
    failed_items: List[uuid.UUID]


class CollectionBulkPresetRequest(BaseDTO):
    preset_uuid: uuid.UUID


class ProjectCollectionType(Enum):
    FRAME = "FRAME"
    LABEL = "LABEL"


class GetProjectCollectionParams(BaseDTO):
    project_hash: Optional[uuid.UUID] = Field(default=None, alias="projectHash")
    collection_uuids: Optional[List[uuid.UUID]] = Field(default=[], alias="uuids")
    page_token: Optional[str] = Field(default=None, alias="pageToken")
    page_size: Optional[int] = Field(default=None, alias="pageSize")


class CreateProjectCollectionParams(BaseDTO):
    project_hash: Optional[uuid.UUID] = Field(default=None, alias="projectHash")


class CreateProjectCollectionPayload(CreateCollectionPayload):
    collection_type: ProjectCollectionType


class ProjectCollection(Collection):
    collection_type: ProjectCollectionType


class GetProjectCollectionsResponse(BaseDTO):
    results: List[ProjectCollection]


class ProjectCollectionItemFrameSpec(BaseDTO):
    frame_index: int


class ProjectCollectionItemObjectSpec(BaseDTO):
    frame_index: int
    object_hash: str


class ProjectCollectionItemClassificationSpec(BaseDTO):
    frame_index: int
    classification_hash: str


ProjectCollectionItemSpec = (
    ProjectCollectionItemFrameSpec | ProjectCollectionItemObjectSpec | ProjectCollectionItemClassificationSpec
)


class ProjectCollectionItem(BaseDTO):
    label_row_metadata: LabelRowMetadataDTO
    specs: list[ProjectCollectionItemSpec]


class ProjectCollectionBulkItemRequest(BaseDTO):
    label_hash: uuid.UUID
    specs: list[ProjectCollectionItemSpec]
