"""
---
title: "OntologyObject DEPRECATED"
slug: "sdk-ref-ontology-object-deprecated"
hidden: false
metadata:
  title: "OntologyObject DEPRECATED"
  description: "Encord SDK OntologyObject DEPRECATED."
category: "64e481b57b6027003f20aaa0"
---
"""

from dataclasses import dataclass

from encord.project_ontology.object_type import ObjectShape


@dataclass
class OntologyObject:
    """
    DEPRECATED: prefer using :class:`encord.ontology.Ontology`

    A dataclass which holds an object for of the :class:`encord.project_ontology.Ontology`.
    """

    #: A unique (to the ontology) identifier of the classification.
    id: str
    #: The color which is displayed in the web-app.
    color: str
    #: The name of the object.
    name: str
    #: The shape of the object. E.g., polygon, polyline, and bounding_box.
    shape: ObjectShape
    #: An 8-character hex string uniquely defining the option.
    feature_node_hash: str
