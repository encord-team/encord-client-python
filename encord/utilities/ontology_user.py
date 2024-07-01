"""
---
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
from enum import IntEnum


class OntologyUserRole(IntEnum):
    ADMIN = 0
    USER = 1


@dataclass(frozen=True)
class OntologyWithUserRole:
    """
    This is a helper class denoting the relationship between the current user an an ontology
    """

    user_role: int
    user_email: str
    ontology: dict
