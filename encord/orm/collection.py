import uuid
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from encord.orm.base_dto import BaseDTO, Field


class GetCollectionParams(BaseDTO):
    top_level_folder_uuid: Optional[UUID] = Field(default=None, alias="topLevelFolderUuid")
    collection_uuids: Optional[List[UUID]] = Field(default=[], alias="uuids")
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
