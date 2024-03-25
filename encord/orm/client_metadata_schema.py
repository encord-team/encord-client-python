from datetime import datetime
from typing import Dict
from uuid import UUID

from encord.common.enum import StringEnum
from encord.orm.base_dto import BaseDTO


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
