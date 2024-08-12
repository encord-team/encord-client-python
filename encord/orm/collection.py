import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from encord.orm.base_dto import BaseDTO, Field

class GetCollectionParams(BaseDTO):
    top_level_folder_uuid: Optional[UUID] = Field(default=None, alias="topLevelFolderUuid")
    collection_uuids: Optional[List[UUID]] = Field(default=[], alias="uuids")

class CreateCollectionParams(BaseDTO):
    top_level_folder_uuid: Optional[UUID] = Field(default=None, alias="topLevelFolderUuid")

class CreateCollectionPayload(BaseDTO):
    name: str
    description: Optional[str] = ""

class UpdateCollectionPayload(BaseDTO):
    name: str | None = None
    description: str | None = None


class Collection(BaseDTO):
    uuid: uuid.UUID
    name: str
    description: Optional[str]
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    last_edited_at: Optional[datetime] = Field(default=None, alias="lastEditedAt")

class GetCollectionsResponse(BaseDTO):
    results: List[Collection]
