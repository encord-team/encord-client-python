import uuid
from typing import Dict, Type, Any
from uuid import UUID

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

    @classmethod
    def from_dict(cls: Type[T], d: Dict[str, Any]) -> T | None:
        if d is None:
            d = {
                "metadata_schema": {},
                "organisation_id": -1,
                "uuid": uuid.uuid4()
            }
        return cls(**d)


class ClientMetadataSchemaPayload(BaseDTO):
    metadata_schema: Dict[str, ClientMetadataSchemaTypes]

    def to_dict(self) -> Dict[str, Any]:
        return self.metadata_schema
