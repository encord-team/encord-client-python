"""---
title: "Utilities - Ontology Helper"
slug: "sdk-ref-utilities-ont-helper"
hidden: false
metadata:
  title: "Utilities - Ontology Helper"
  description: "Encord SDK Utilities - Ontology Helper."
category: "64e481b57b6027003f20aaa0"
---
"""

from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from typing import Optional, Union
from uuid import UUID

from encord.orm.base_dto import BaseDTO


class OntologyUserRole(IntEnum):
    ADMIN = 0
    USER = 1


class OntologyWithUserRole(BaseDTO):
    """An on-the-wire representation from /v2/public/ontologies endpoints"""

    ontology_uuid: UUID
    title: str
    description: str
    editor: dict
    created_at: datetime
    last_edited_at: datetime
    user_role: Optional[OntologyUserRole]


class OntologiesFilterParams(BaseDTO):
    """Filter parameters for the /v2/public/ontologies endpoint"""

    title_eq: Optional[str] = None
    title_like: Optional[str] = None
    desc_eq: Optional[str] = None
    desc_like: Optional[str] = None
    created_before: Optional[Union[str, datetime]] = None
    created_after: Optional[Union[str, datetime]] = None
    edited_before: Optional[Union[str, datetime]] = None
    edited_after: Optional[Union[str, datetime]] = None
    include_org_access: bool = False
