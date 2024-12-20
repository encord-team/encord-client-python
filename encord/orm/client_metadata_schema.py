from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from encord.common.enum import StringEnum
from encord.orm.base_dto import BaseDTO


class ClientMetadataSchemaTypes(StringEnum):
    NUMBER = "number"
    STRING = "string"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    GEOSPATIAL = "geospatial"
    ENUM = "enum"
    EMBEDDING = "embedding"
    LONG_STRING = "long_string"


class ClientMetadataSchema(BaseDTO):
    uuid: UUID
    metadata_schema: dict[str, ClientMetadataSchemaTypes]
    organisation_id: int
    created_at: datetime
    updated_at: datetime


class ClientMetadataSchemaPayload(BaseDTO):
    metadata_schema: dict[str, ClientMetadataSchemaTypes]

    def to_dict(self, by_alias=True, exclude_none=True) -> dict[str, Any]:
        return self.metadata_schema
