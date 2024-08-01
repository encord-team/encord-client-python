"""
---
title: "Objects - Classification"
slug: "sdk-ref-objects-classification"
hidden: false
metadata:
  title: "Objects - Classification"
  description: "Encord SDK Objects - Classification."
category: "64e481b57b6027003f20aaa0"
---
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Type, TypeVar

from encord.objects.attributes import (
    Attribute,
    AttributeType,
    _add_attribute,
    attribute_from_dict,
    attributes_to_list_dict,
)
from encord.objects.ontology_element import OntologyElement


@dataclass
class Classification(OntologyElement):
    """
    Represents a whole-image classification as part of the Ontology structure. Wraps a single Attribute that describes
    the image in general rather than an individual object.

    Attributes:
        uid (int): The unique identifier for the classification.
        feature_node_hash (str): A unique hash identifying the feature node.
        attributes (List[Attribute]): A list of attributes associated with this classification.
    """

    uid: int
    feature_node_hash: str
    attributes: List[Attribute]

    @property
    def title(self) -> str:
        """
        Returns the title of the classification, which is the name of the first attribute.

        Returns:
            str: The title of the classification.
        """
        return self.attributes[0].name

    @property
    def children(self) -> Sequence[OntologyElement]:
        """
        Returns the attributes of the classification as children elements.

        Returns:
            Sequence[OntologyElement]: The attributes of the classification.
        """
        return self.attributes

    def create_instance(self) -> ClassificationInstance:
        """
        Create a ClassificationInstance to be used with a label row.

        Returns:
            ClassificationInstance: An instance of ClassificationInstance.
        """
        return ClassificationInstance(self)

    @classmethod
    def from_dict(cls, d: dict) -> Classification:
        """
        Create a Classification instance from a dictionary.

        Args:
            d (dict): A dictionary containing classification information.

        Returns:
            Classification: An instance of Classification.
        """
        attributes_ret: List[Attribute] = [attribute_from_dict(attribute_dict) for attribute_dict in d["attributes"]]
        return Classification(
            uid=int(d["id"]),
            feature_node_hash=d["featureNodeHash"],
            attributes=attributes_ret,
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Classification instance to a dictionary.

        Returns:
            Dict[str, Any]: A dictionary representation of the classification.

        Raises:
            ValueError: If the classification does not have any attributes.
        """
        ret: Dict[str, Any] = {
            "id": str(self.uid),
            "featureNodeHash": self.feature_node_hash,
        }
        if attributes_list := attributes_to_list_dict(self.attributes):
            ret["attributes"] = attributes_list
        else:
            raise ValueError(f"Classification {str(self.uid)} requires attribute before use")

        return ret

    def add_attribute(
        self,
        cls: Type[AttributeType],
        name: str,
        local_uid: Optional[int] = None,
        feature_node_hash: Optional[str] = None,
        required: bool = False,
    ) -> AttributeType:
        """
        Adds an attribute to the classification.

        Args:
            cls (Type[AttributeType]): The attribute type, one of `RadioAttribute`, `ChecklistAttribute`, `TextAttribute`.
            name (str): The user-visible name of the attribute.
            local_uid (Optional[int]): Integer identifier of the attribute. Normally auto-generated; omit this unless
                                       the aim is to create an exact clone of an existing ontology.
            feature_node_hash (Optional[str]): Global identifier of the attribute. Normally auto-generated; omit this
                                               unless the aim is to create an exact clone of an existing ontology.
            required (bool): Whether the label editor would mark this attribute as 'required'.

        Returns:
            AttributeType: The created attribute that can be further specified with Options, where appropriate.

        Raises:
            ValueError: If the classification already has an attribute assigned.
        """
        if self.attributes:
            raise ValueError("Classification should have exactly one root attribute")
        return _add_attribute(self.attributes, cls, name, [self.uid], local_uid, feature_node_hash, required)

    def __hash__(self):
        return hash(self.feature_node_hash)


from encord.objects.classification_instance import ClassificationInstance
