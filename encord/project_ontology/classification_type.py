"""
---
title: "ClassificationType DEPRECATED"
slug: "sdk-ref-classification-type-deprecated"
hidden: false
metadata:
  title: "ClassificationType DEPRECATED"
  description: "Encord SDK ClassificationType DEPRECATED."
category: "64e481b57b6027003f20aaa0"
---
"""

from enum import Enum


class ClassificationType(Enum):
    """
    DEPRECATED: prefer using :class:`encord.ontology.Ontology`

    Enum used to define classification type in ontologies.
    """

    #: Single select option
    RADIO = "radio"
    #: Text option for free text input.
    TEXT = "text"
    #: Multi select option
    CHECKLIST = "checklist"
