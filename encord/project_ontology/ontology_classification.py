"""
---
title: "OntologyClassification DEPRECATED"
slug: "sdk-ref-ontology-classification-deprecated"
hidden: false
metadata:
  title: "OntologyClassification DEPRECATED"
  description: "Encord SDK OntologyClassification DEPRECATED."
category: "64e481b57b6027003f20aaa0"
---
"""

from dataclasses import dataclass
from typing import List

from encord.project_ontology.classification_attribute import ClassificationAttribute


@dataclass
class OntologyClassification:
    """
    DEPRECATED: prefer using :class:`encord.ontology.Ontology`

    A dataclass which holds classifications of the :class:`encord.project_ontology.Ontology`.
    """

    #: A unique (to the ontology) identifier of the classification.
    id: str
    #: An 8-character hex string uniquely defining the option.
    feature_node_hash: str
    #: A List of attributes for the classification.
    attributes: List[ClassificationAttribute]
