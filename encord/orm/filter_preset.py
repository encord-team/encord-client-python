import uuid
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from encord.orm.base_dto import BaseDTO, Field, dto_validator


class GetPresetParams(BaseDTO):
    top_level_folder_uuid: Optional[UUID] = Field(default=None, alias="topLevelFolderUuid")
    preset_uuids: Optional[List[UUID]] = Field(default=[], alias="uuids")
    page_token: Optional[str] = Field(default=None, alias="pageToken")
    page_size: Optional[int] = Field(default=None, alias="pageSize")


class FilterPreset(BaseDTO):
    uuid: uuid.UUID
    name: str
    description: Optional[str]
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    last_updated_at: Optional[datetime] = Field(default=None, alias="lastUpdatedAt")


class GetProjectFilterPresetParams(BaseDTO):
    preset_uuids: Optional[List[uuid.UUID]] = Field(default=[])
    page_token: Optional[str] = Field(default=None)
    page_size: Optional[int] = Field(default=None)


class ProjectFilterPreset(BaseDTO):
    preset_uuid: uuid.UUID = Field(alias="presetUuid")
    name: str
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)


class FilterDefinition(BaseDTO):
    filters: List[Dict] = Field(default_factory=list)


# Note alias is strictly required as these are stored in the Annotate DB as unstructured objects
# Stored not in camelCase like most Models
class IndexFilterPresetDefinition(BaseDTO):
    local_filters: Dict[str, FilterDefinition] = Field(
        default_factory=lambda: {str(uuid.UUID(int=0)): FilterDefinition()},
        alias="local_filters",
    )
    global_filters: FilterDefinition = Field(default_factory=FilterDefinition, alias="global_filters")


class ActiveFilterPresetDefinition(BaseDTO):
    local_filters: Dict[str, FilterDefinition] = Field(
        default_factory=lambda: {str(uuid.UUID(int=0)): FilterDefinition()},
    )
    global_filters: FilterDefinition = Field(default_factory=FilterDefinition)


class GetPresetsResponse(BaseDTO):
    results: List[FilterPreset]


class CreatePresetParams(BaseDTO):
    top_level_folder_uuid: UUID = Field(default=UUID(int=0), alias="topLevelFolderUuid")


class IndexCreatePresetPayload(BaseDTO):
    name: str
    filter_preset_json: Dict
    description: Optional[str] = ""


class ActiveCreatePresetPayload(BaseDTO):
    name: str
    filter_preset_json: Dict


class IndexUpdatePresetPayload(BaseDTO):
    name: Optional[str] = None
    description: Optional[str] = ""
    filter_preset: Optional[IndexFilterPresetDefinition] = None


class ActiveUpdatePresetPayload(BaseDTO):
    name: Optional[str] = None
    filter_preset: Optional[ActiveFilterPresetDefinition] = None
