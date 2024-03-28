import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Type
from uuid import UUID, uuid4

from encord.common.enum import StringEnum
from encord.orm.base_dto import BaseDTO
from encord.orm.base_dto.base_dto_interface import T


class ClientMetadataSchemaTypes(StringEnum):
    NUMBER = "number"
    STRING = "string"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    GEOSPATIAL = "geospatial"


class ClientMetadataSchema(BaseDTO):
    uuid: UUID
    metadata_schema: Dict[str, ClientMetadataSchemaTypes]
    organisation_id: int
    created_at: datetime
    updated_at: datetime


class ClientMetadataSchemaPayload(BaseDTO):
    metadata_schema: Dict[str, ClientMetadataSchemaTypes]

    def to_dict(self, by_alias=True, exclude_none=True) -> Dict[str, Any]:
        return self.metadata_schema
