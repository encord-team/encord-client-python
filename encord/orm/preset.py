import uuid
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from encord.orm.base_dto import BaseDTO, Field


class GetPresetParams(BaseDTO):
    top_level_folder_uuid: Optional[UUID] = Field(default=None, alias="topLevelFolderUuid")
    collection_uuids: Optional[List[UUID]] = Field(default=[], alias="uuids")

class Preset(BaseDTO):
    uuid: uuid.UUID
    name: str
    description: Optional[str]
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    last_updated_at: Optional[datetime] = Field(default=None, alias="lastUpdatedAt")

class PresetFilter(BaseDTO):
    local_filters: Optional[dict] = Field(default=None, alias="localFilters")
    global_filters: Optional[dict] = Field(default=None, alias="globalFilters")

class GetPresetsResponse(BaseDTO):
    results: List[Preset]