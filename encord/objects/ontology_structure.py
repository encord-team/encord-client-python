from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, cast
from uuid import uuid4

from encord.exceptions import OntologyError
from encord.objects.classification import Classification
from encord.objects.common import Shape
from encord.objects.constants import AVAILABLE_COLORS
from encord.objects.ontology_element import (
    OntologyElement,
    OntologyElementT,
    OntologyNestedElement,
    _assert_singular_result_list,
    _get_element_by_hash,
)
from encord.objects.ontology_object import Object
from encord.objects.utils import checked_cast, does_type_match


@dataclass
class OntologyStructure:
    objects: List[Object] = field(default_factory=list)
    classifications: List[Classification] = field(default_factory=list)

    def get_child_by_hash(
        self,
        feature_node_hash: str,
        type_: Optional[Type[OntologyElementT]] = None,
    ) -> OntologyElementT:
        """
        Returns the first child node of this ontology tree node with the matching feature node hash. If there is
        more than one child with the same feature node hash in the ontology tree node, then the ontology would be in
        an invalid state. Throws if nothing is found or if the type is not matched.

        Args:
            feature_node_hash: the feature_node_hash of the child node to search for in the ontology.
            type_: The expected type of the item. If the found child does not match the type, an error will be thrown.
        """
        for object_ in self.objects:
            if object_.feature_node_hash == feature_node_hash:
                return checked_cast(object_, type_)

            found_item = _get_element_by_hash(feature_node_hash, object_.attributes)
            if found_item is not None:
                return checked_cast(found_item, type_)

        for classification in self.classifications:
            if classification.feature_node_hash == feature_node_hash:
                return checked_cast(classification, type_)
            found_item = _get_element_by_hash(feature_node_hash, classification.attributes)
            if found_item is not None:
                return checked_cast(found_item, type_)

        raise OntologyError(f"Item not found: can't find an item with a hash {feature_node_hash} in the ontology.")

    def get_child_by_title(
        self,
        title: str,
        type_: Optional[Type[OntologyElementT]] = None,
    ) -> OntologyElementT:
        """
        Returns a child node of this ontology tree node with the matching title and matching type if specified. If more
        than one child in this Object have the same title, then an error will be thrown. If no item is found, an error
        will be thrown as well.

        Args:
            title: The exact title of the child node to search for in the ontology.
            type_: The expected type of the child node. Only a node that matches this type will be returned.
        """
        found_items = self.get_children_by_title(title, type_)
        _assert_singular_result_list(found_items, title, type_)
        return found_items[0]

    def get_children_by_title(
        self,
        title: str,
        type_: Optional[Type[OntologyElementT]] = None,
    ) -> List[OntologyElementT]:
        """
        Returns all the child nodes of this ontology tree node with the matching title and matching type if specified.
        Title in ontologies do not need to be unique, however, we recommend unique titles when creating ontologies.

        Args:
            title: The exact title of the child node to search for in the ontology.
            type_: The expected type of the item. Only nodes that match this type will be returned.
        """
        ret: List[OntologyElement] = []
        for object_ in self.objects:
            if object_.title == title and does_type_match(object_, type_):
                ret.append(object_)

            if type_ is None or issubclass(type_, OntologyNestedElement):
                found_items = object_.get_children_by_title(title, type_=type_)
                ret.extend(found_items)

        for classification in self.classifications:
            if classification.title == title and does_type_match(classification, type_):
                ret.append(classification)

            if type_ is None or issubclass(type_, OntologyNestedElement):
                found_items = classification.get_children_by_title(title, type_=type_)
                ret.extend(found_items)

        # type checks in the code above guarantee the type conformity of the return value
        # but there is no obvious way to tell that to mypy, so just casting here for now
        return cast(List[OntologyElementT], ret)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> OntologyStructure:
        """
        Args:
            d: a JSON blob of an "ontology structure" (e.g. from Encord web app)

        Raises:
            KeyError: If the dict is missing a required field.
        """
        objects_ret = [Object.from_dict(object_dict) for object_dict in d["objects"]]
        classifications_ret = [
            Classification.from_dict(classification_dict) for classification_dict in d["classifications"]
        ]
        return OntologyStructure(objects=objects_ret, classifications=classifications_ret)

    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Returns:
            The dict equivalent to the ontology.

        Raises:
            KeyError: If the dict is missing a required field.
        """
        ret: Dict[str, List[Dict[str, Any]]] = dict()
        ontology_objects: List[Dict[str, Any]] = list()
        ret["objects"] = ontology_objects
        for ontology_object in self.objects:
            ontology_objects.append(ontology_object.to_dict())

        ontology_classifications: List[Dict[str, Any]] = list()
        ret["classifications"] = ontology_classifications
        for ontology_classification in self.classifications:
            ontology_classifications.append(ontology_classification.to_dict())

        return ret

    def add_object(
        self,
        name: str,
        shape: Shape,
        uid: Optional[int] = None,
        color: Optional[str] = None,
        feature_node_hash: Optional[str] = None,
    ) -> Object:
        """
        Adds an object class definition to the structure.

        .. code::

            structure = ontology_structure.OntologyStructure()

            eye = structure.add_object(
                name="Eye",
            )
            nose = structure.add_object(
                name="Nose",
            )
            nose_detail = nose.add_attribute(
                encord.objects.common.ChecklistAttribute,
            )
            nose_detail.add_option(feature_node_hash="2bc17c88", label="Is it a cute nose?")
            nose_detail.add_option(feature_node_hash="86eaa4f2", label="Is it a wet nose? ")

        Args:
            name: the user-visible name of the object
            shape: the kind of object (bounding box, polygon, etc). See :py:class:`encord.objects.common.Shape` enum for possible values
            uid: integer identifier of the object. Normally auto-generated;
                    omit this unless the aim is to create an exact clone of existing structure
            color: the color of the object in the label editor. Normally auto-assigned, should be in '#1A2B3F' syntax.
            feature_node_hash: global identifier of the object. Normally auto-generated;
                    omit this unless the aim is to create an exact clone of existing structure

        Returns:
            the created object class that can be further customised with attributes.
        """
        if uid is None:
            if self.objects:
                uid = max([obj.uid for obj in self.objects]) + 1
            else:
                uid = 1
        else:
            if any([obj.uid == uid for obj in self.objects]):
                raise ValueError(f"Duplicate uid '{uid}'")

        if color is None:
            color_index = 0
            if self.objects:
                try:
                    color_index = AVAILABLE_COLORS.index(self.objects[-1].color) + 1
                    if color_index >= len(AVAILABLE_COLORS):
                        color_index = 0
                except ValueError:
                    pass
            color = AVAILABLE_COLORS[color_index]

        if feature_node_hash is None:
            feature_node_hash = str(uuid4())[:8]

        if any([obj.feature_node_hash == feature_node_hash for obj in self.objects]):
            raise ValueError(f"Duplicate feature_node_hash '{feature_node_hash}'")

        obj = Object(uid=uid, name=name, color=color, shape=shape, feature_node_hash=feature_node_hash)
        self.objects.append(obj)
        return obj

    def add_classification(
        self,
        uid: Optional[int] = None,
        feature_node_hash: Optional[str] = None,
    ) -> Classification:
        """
        Adds an classification definition to the ontology.

        .. code::

            structure = ontology_structure.OntologyStructure()

            cls = structure.add_classification(feature_node_hash="a39d81c0")
            cat_standing = cls.add_attribute(
                encord.objects.common.RadioAttribute,
                feature_node_hash="a6136d14",
                name="Is the cat standing?",
                required=True,
            )
            cat_standing.add_option(feature_node_hash="a3aeb48d", label="Yes")
            cat_standing.add_option(feature_node_hash="d0a4b373", label="No")

        Args:
            uid: integer identifier of the object. Normally auto-generated;
                    omit this unless the aim is to create an exact clone of existing structure
            feature_node_hash: global identifier of the object. Normally auto-generated;
                    omit this unless the aim is to create an exact clone of existing structure

        Returns:
            the created classification node. Note that classification attribute should be further specified by calling its `add_attribute()` method.
        """
        if uid is None:
            if self.classifications:
                uid = max([cls.uid for cls in self.classifications]) + 1
            else:
                uid = 1
        else:
            if any([cls.uid == uid for cls in self.classifications]):
                raise ValueError(f"Duplicate uid '{uid}'")

        if feature_node_hash is None:
            feature_node_hash = str(uuid4())[:8]

        if any([cls.feature_node_hash == feature_node_hash for cls in self.classifications]):
            raise ValueError(f"Duplicate feature_node_hash '{feature_node_hash}'")

        cls = Classification(uid=uid, feature_node_hash=feature_node_hash, attributes=list())
        self.classifications.append(cls)
        return cls
