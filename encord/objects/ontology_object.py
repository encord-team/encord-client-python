"""
---
title: "Objects - Ontology Object"
slug: "sdk-ref-objects-ont-object"
hidden: false
metadata:
  title: "Objects - Ontology Object"
  description: "Encord SDK Objects - Ontology Object."
category: "64e481b57b6027003f20aaa0"
---
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Type

from encord.objects.attributes import (
    Attribute,
    AttributeType,
    _add_attribute,
    attribute_from_dict,
    attributes_to_list_dict,
)
from encord.objects.common import Shape
from encord.objects.ontology_element import OntologyElement


@dataclass
class Object(OntologyElement):
    uid: int
    name: str
    color: str
    shape: Shape
    feature_node_hash: str
    required: bool = False
    attributes: List[Attribute] = field(default_factory=list)

    @property
    def title(self) -> str:
        """
        Returns the name of the object, used as the title.
        """
        return self.name

    @property
    def children(self) -> Sequence[OntologyElement]:
        """
        Returns the attributes of the object as its children.
        """
        return self.attributes

    def create_instance(self) -> ObjectInstance:
        """
        Create a :class:`encord.objects.ObjectInstance` to be used with a label row.

        Returns:
            ObjectInstance: An instance of the object to be used in labeling.
        """
        return ObjectInstance(self)

    @classmethod
    def from_dict(cls, d: dict) -> Object:
        """
        Create an Object from a dictionary.

        Args:
            d: A dictionary representing the object.

        Returns:
            Object: The created Object instance.

        Raises:
            TypeError: If the shape in the dictionary is not recognized.
        """
        shape_opt = Shape.from_string(d["shape"])
        if shape_opt is None:
            raise TypeError(f"The shape '{d['shape']}' of the object '{d}' is not recognised")

        attributes_ret: List[Attribute] = [
            attribute_from_dict(attribute_dict) for attribute_dict in d.get("attributes", [])
        ]
        return Object(
            uid=int(d["id"]),
            name=d["name"],
            color=d["color"],
            shape=shape_opt,
            feature_node_hash=d["featureNodeHash"],
            attributes=attributes_ret,
            required=bool(d.get("required", False)),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Object to a dictionary.

        Returns:
            Dict[str, Any]: The dictionary representation of the object.
        """
        ret: Dict[str, Any] = {
            "id": str(self.uid),
            "name": self.name,
            "color": self.color,
            "shape": self.shape.value,
            "featureNodeHash": self.feature_node_hash,
            "required": self.required,
        }
        if attributes_list := attributes_to_list_dict(self.attributes):
            ret["attributes"] = attributes_list

        return ret

    def add_attribute(
        self,
        cls: Type[AttributeType],
        name: str,
        local_uid: Optional[int] = None,
        feature_node_hash: Optional[str] = None,
        required: bool = False,
        dynamic: bool = False,
    ) -> AttributeType:
        """
        Adds an attribute to the object.

        Args:
            cls: The attribute type, one of `RadioAttribute`, `ChecklistAttribute`, `TextAttribute`.
            name: The user-visible name of the attribute.
            local_uid: Integer identifier of the attribute. Normally auto-generated;
                       omit this unless the aim is to create an exact clone of an existing ontology.
            feature_node_hash: Global identifier of the attribute. Normally auto-generated;
                               omit this unless the aim is to create an exact clone of an existing ontology.
            required: Whether the label editor would mark this attribute as 'required'.
            dynamic: Whether the attribute can have a different answer for the same object across different frames.

        Returns:
            AttributeType: The created attribute that can be further specified with options, where appropriate.

        Raises:
            ValueError: If the specified `local_uid` or `feature_node_hash` violate uniqueness constraints.
        """
        return _add_attribute(self.attributes, cls, name, [self.uid], local_uid, feature_node_hash, required, dynamic)


from encord.objects.ontology_object_instance import ObjectInstance
