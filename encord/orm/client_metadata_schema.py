"""
---
title: "Custom Metadata Scema"
slug: "sdk-ref-custom-metadata-schema"
hidden: false
metadata:
  title: "Custom Metadata Schema"
  description: "Encord SDK Custom Metadata Schema."
category: "64e481b57b6027003f20aaa0"
---
"""

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
