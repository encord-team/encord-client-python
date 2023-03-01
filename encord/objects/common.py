from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, List, Optional, Tuple, Type, TypeVar, Union

from encord.exceptions import OntologyError
from encord.objects.utils import (
    _decode_nested_uid,
    check_type,
    filter_by_type,
    short_uuid_str,
)
from encord.orm.project import StringEnum

NestedID = List[int]


class PropertyType(StringEnum):
    RADIO = "radio"
    TEXT = "text"
    CHECKLIST = "checklist"


class Shape(StringEnum):
    BOUNDING_BOX = "bounding_box"
    POLYGON = "polygon"
    POINT = "point"
    SKELETON = "skeleton"
    POLYLINE = "polyline"
    ROTATABLE_BOUNDING_BOX = "rotatable_bounding_box"


@dataclass
class Attribute(ABC):
    """
    Base class for shared Attribute fields
    """

    uid: NestedID
    feature_node_hash: str
    name: str
    required: bool
    dynamic: bool
    """
    The `dynamic` member is part of every attribute. However it can only be true for top level (not nested) attributes
    that are part of an :class:`encord.objects.ontology_object.Object`.
    """

    @abstractmethod
    def get_property_type(self) -> PropertyType:
        pass

    @classmethod
    @abstractmethod
    def has_options_field(cls) -> bool:
        pass

    @abstractmethod
    def get_child_by_hash(
        self,
        feature_node_hash: str,
        type_: Union[AttributeTypes, OptionTypes, None] = None,
    ) -> Union[AttributeClasses, OptionClasses]:
        """
        Returns the first child node of this ontology tree node with the matching feature node hash. If there is
        more than one child with the same feature node hash in the ontology tree node, then the ontology would be in
        an invalid state. Throws if nothing is found or if the type is not matched.

        Args:
            feature_node_hash: the feature_node_hash of the child node to search for in the ontology.
            type_: The expected type of the item. If the found child does not match the type, an error will be thrown.
        """
        raise NotImplementedError("This method is not implemented for this class")

    def get_child_by_title(
        self,
        title: str,
        type_: Union[AttributeTypes, OptionTypes, None] = None,
    ) -> Union[AttributeClasses, OptionClasses]:
        """
        Returns a child node of this ontology tree node with the matching title and matching type if specified. If more
        than one child in this Object have the same title, then an error will be thrown. If no item is found, an error
        will be thrown as well.

        Args:
            title: The exact title of the child node to search for in the ontology.
            type_: The expected type of the child node. Only a node that matches this type will be returned.
        """
        found_items = self.get_children_by_title(title, type_)
        _handle_wrong_number_of_found_items(found_items, title, type_)
        return found_items[0]

    @abstractmethod
    def get_children_by_title(
        self,
        title: str,
        type_: Union[AttributeTypes, OptionTypes, None] = None,
    ) -> List[Union[AttributeClasses, OptionClasses]]:
        """
        Returns all the child nodes of this ontology tree node with the matching title and matching type if specified.
        Title in ontologies do not need to be unique, however, we recommend unique titles when creating ontologies.

        Args:
            title: The exact title of the child node to search for in the ontology.
            type_: The expected type of the item. Only nodes that match this type will be returned.
        """
        raise NotImplementedError("This method is not implemented for this class")

    def to_dict(self) -> dict:
        ret = self._encode_base()

        options = self._encode_options()
        if options is not None:
            ret["options"] = options

        return ret

    @classmethod
    def from_dict(cls, d: dict) -> Attribute:
        property_type = d["type"]
        common_attribute_fields = cls._decode_common_attribute_fields(d)
        if property_type == "radio":
            options_ret: List[NestableOption] = list()
            if "options" in d:
                for options_dict in d["options"]:
                    options_ret.append(NestableOption.from_dict(options_dict))

            return RadioAttribute(
                **common_attribute_fields,
                options=options_ret,
            )

        elif property_type == "checklist":
            options_ret: List[FlatOption] = list()
            if "options" in d:
                for options_dict in d["options"]:
                    options_ret.append(FlatOption.from_dict(options_dict))

            return ChecklistAttribute(
                **common_attribute_fields,
                options=options_ret,
            )

        elif property_type == "text":
            return TextAttribute(
                **common_attribute_fields,
            )

        raise TypeError(
            f"Attribute is ill-formed: '{d}'. Expected to see either "
            f"attribute specific fields or option specific fields. Got both or none of them."
        )

    def _encode_base(self) -> dict:
        ret = dict()
        ret["id"] = _decode_nested_uid(self.uid)
        ret["name"] = self.name
        ret["type"] = self.get_property_type().value
        ret["featureNodeHash"] = self.feature_node_hash
        ret["required"] = self.required
        ret["dynamic"] = self.dynamic

        return ret

    def _encode_options(self) -> Optional[list]:
        if not self.has_options_field() or not self.options:
            return None

        self: OptionAttribute

        ret = list()
        for option in self.options:
            ret.append(option.to_dict())
        return ret

    @staticmethod
    def _decode_common_attribute_fields(attribute_dict: dict) -> dict:
        return {
            "uid": _attribute_id_from_json_str(attribute_dict["id"]),
            "feature_node_hash": attribute_dict["featureNodeHash"],
            "name": attribute_dict["name"],
            "required": attribute_dict["required"],
            "dynamic": attribute_dict.get("dynamic", False),
        }


@dataclass
class RadioAttribute(Attribute):
    """
    This class is currently in BETA. Its API might change in future minor version releases.
    """

    options: List[NestableOption] = field(default_factory=list)

    def get_property_type(self) -> PropertyType:
        return PropertyType.RADIO

    @classmethod
    def has_options_field(cls) -> bool:
        return True

    def get_child_by_hash(
        self,
        feature_node_hash: str,
        type_: Union[AttributeTypes, OptionTypes, None] = None,
    ) -> Union[AttributeClasses, OptionClasses]:
        """
        Returns the first child node of this ontology tree node with the matching feature node hash. If there is
        more than one child with the same feature node hash in the ontology tree node, then the ontology would be in
        an invalid state. Throws if nothing is found or if the type is not matched.

        Args:
            feature_node_hash: the feature_node_hash of the child node to search for in the ontology.
            type_: The expected type of the item. If the found child does not match the type, an error will be thrown.
        """
        found_item = _get_option_by_hash(feature_node_hash, self.options)
        if found_item is None:
            raise OntologyError("Item not found.")
        check_type(found_item, type_)
        return found_item

    def get_children_by_title(
        self,
        title: str,
        type_: Union[AttributeTypes, OptionTypes, None] = None,
    ) -> List[Union[AttributeClasses, OptionClasses]]:
        """
        Returns all the child nodes of this ontology tree node with the matching title and matching type if specified.
        Title in ontologies do not need to be unique, however, we recommend unique titles when creating ontologies.

        Args:
            title: The exact title of the child node to search for in the ontology.
            type_: The expected type of the item. Only nodes that match this type will be returned.
        """
        found_items = _get_options_by_title(title, self.options)
        return filter_by_type(found_items, type_)  # noqa

    def add_option(
        self,
        label: str,
        value: Optional[str] = None,
        local_uid: Optional[int] = None,
        feature_node_hash: Optional[str] = None,
    ) -> NestableOption:
        """
        Args:
            label: user-visible name of the option
            value: internal unique value; optional; normally mechanically constructed from the label
            local_uid: integer identifier of the option. Normally auto-generated;
                    omit this unless the aim is to create an exact clone of existing ontology
            feature_node_hash: global identifier of the option. Normally auto-generated;
                    omit this unless the aim is to create an exact clone of existing ontology

        Returns:
            a `NestableOption` instance attached to the attribute. This can be further specified by adding nested attributes.
        """
        return _add_option(self.options, NestableOption, label, self.uid, local_uid, feature_node_hash, value)


@dataclass
class ChecklistAttribute(Attribute):
    """
    This class is currently in BETA. Its API might change in future minor version releases.
    """

    options: List[FlatOption] = field(default_factory=list)

    def get_property_type(self) -> PropertyType:
        return PropertyType.CHECKLIST

    @classmethod
    def has_options_field(cls) -> bool:
        return True

    def get_child_by_hash(
        self,
        feature_node_hash: str,
        type_: Union[AttributeTypes, OptionTypes, None] = None,
    ) -> Union[AttributeClasses, OptionClasses]:
        """
        Returns the first child node of this ontology tree node with the matching feature node hash. If there is
        more than one child with the same feature node hash in the ontology tree node, then the ontology would be in
        an invalid state. Throws if nothing is found or if the type is not matched.

        Args:
            feature_node_hash: the feature_node_hash of the child node to search for in the ontology.
            type_: The expected type of the item. If the found child does not match the type, an error will be thrown.
        """
        found_item = _get_option_by_hash(feature_node_hash, self.options)
        if found_item is None:
            raise OntologyError("Item not found.")
        check_type(found_item, type_)
        return found_item

    def get_children_by_title(
        self,
        title: str,
        type_: Union[AttributeTypes, OptionTypes, None] = None,
    ) -> List[Union[AttributeClasses, OptionClasses]]:
        """
        Returns all the child nodes of this ontology tree node with the matching title and matching type if specified.
        Title in ontologies do not need to be unique, however, we recommend unique titles when creating ontologies.

        Args:
            title: The exact title of the child node to search for in the ontology.
            type_: The expected type of the item. Only nodes that match this type will be returned.
        """
        found_items = _get_options_by_title(title, self.options)
        return filter_by_type(found_items, type_)  # noqa

    def add_option(
        self,
        label: str,
        value: Optional[str] = None,
        local_uid: Optional[int] = None,
        feature_node_hash: Optional[str] = None,
    ):
        """
        Args:
            label: user-visible name of the option
            value: internal unique value; optional; normally mechanically constructed from the label
            local_uid: integer identifier of the option. Normally auto-generated;
                    omit this unless the aim is to create an exact clone of existing ontology
            feature_node_hash: global identifier of the option. Normally auto-generated;
                    omit this unless the aim is to create an exact clone of existing ontology
        Returns:
            a `FlatOption` instance attached to the attribute.
        """
        return _add_option(self.options, FlatOption, label, self.uid, local_uid, feature_node_hash, value)


@dataclass
class TextAttribute(Attribute):
    """
    This class is currently in BETA. Its API might change in future minor version releases.
    """

    def get_property_type(self) -> PropertyType:
        return PropertyType.TEXT

    @classmethod
    def has_options_field(cls) -> bool:
        return False

    def get_child_by_hash(
        self,
        feature_node_hash: str,
        type_: Union[AttributeTypes, OptionTypes, None] = None,
    ) -> Union[AttributeClasses, OptionClasses]:
        """
        Returns the first child node of this ontology tree node with the matching feature node hash. If there is
        more than one child with the same feature node hash in the ontology tree node, then the ontology would be in
        an invalid state. Throws if nothing is found or if the type is not matched.

        For TextAttributes this will always throw as they have no children.

        Args:
            feature_node_hash: the feature_node_hash of the child node to search for in the ontology.
            type_: The expected type of the item. If the found child does not match the type, an error will be thrown.
        """
        raise OntologyError("No nested options available for text attributes.")

    def get_children_by_title(
        self,
        title: str,
        type_: Union[AttributeTypes, OptionTypes, None] = None,
    ) -> List[Union[AttributeClasses, OptionClasses]]:
        """
        Returns all the child nodes of this ontology tree node with the matching title and matching type if specified.
        Title in ontologies do not need to be unique, however, we recommend unique titles when creating ontologies.

        For TextAttributes this will always return an empty list.

        Args:
            title: The exact title of the child node to search for in the ontology.
            type_: The expected type of the item. Only nodes that match this type will be returned.
        """
        return []


OptionAttribute = Union[RadioAttribute, ChecklistAttribute]
"""
This class is currently in BETA. Its API might change in future minor version releases. 
"""


def _attribute_id_from_json_str(attribute_id: str) -> NestedID:
    nested_ids = attribute_id.split(".")
    return [int(x) for x in nested_ids]


def attribute_from_dict(d: dict) -> Attribute:
    """Convenience functions as you cannot call static member on union types."""
    return Attribute.from_dict(d)


def attributes_to_list_dict(attributes: List[Attribute]) -> list:
    attributes_list = list()
    for attribute in attributes:
        attributes_list.append(attribute.to_dict())

    return attributes_list


class OptionType(Enum):
    FLAT = auto()
    NESTABLE = auto()


@dataclass
class Option(ABC):
    """
    Base class for shared Option fields
    """

    uid: NestedID
    feature_node_hash: str
    label: str
    value: str

    @abstractmethod
    def get_option_type(self) -> OptionType:
        pass

    @abstractmethod
    def get_child_by_hash(
        self,
        feature_node_hash: str,
        type_: Union[AttributeTypes, OptionTypes, None] = None,
    ) -> Union[AttributeClasses, OptionClasses]:
        """
        Returns the first child node of this ontology tree node with the matching feature node hash. If there is
        more than one child with the same feature node hash in the ontology tree node, then the ontology would be in
        an invalid state. Throws if nothing is found or if the type is not matched.

        Args:
            feature_node_hash: the feature_node_hash of the child node to search for in the ontology.
            type_: The expected type of the item. If the found child does not match the type, an error will be thrown.
        """
        raise NotImplementedError("This method is not implemented for this class")

    def get_child_by_title(
        self,
        title: str,
        type_: Union[AttributeTypes, OptionTypes, None] = None,
    ) -> Union[AttributeClasses, OptionClasses]:
        """
        Returns a child node of this ontology tree node with the matching title and matching type if specified. If more
        than one child in this Object have the same title, then an error will be thrown. If no item is found, an error
        will be thrown as well.

        Args:
            title: The exact title of the child node to search for in the ontology.
            type_: The expected type of the child node. Only a node that matches this type will be returned.
        """
        found_items = self.get_children_by_title(title, type_)
        _handle_wrong_number_of_found_items(found_items, title, type_)
        return found_items[0]

    @abstractmethod
    def get_children_by_title(
        self,
        title: str,
        type_: Union[AttributeTypes, OptionTypes, None] = None,
    ) -> List[Union[AttributeClasses, OptionClasses]]:
        """
        Returns all the child nodes of this ontology tree node with the matching title and matching type if specified.
        Title in ontologies do not need to be unique, however, we recommend unique titles when creating ontologies.

        Args:
            title: The exact title of the child node to search for in the ontology.
            type_: The expected type of the item. Only nodes that match this type will be returned.
        """
        raise NotImplementedError("This method is not implemented for this class")

    def to_dict(self) -> dict:
        ret = dict()
        ret["id"] = _decode_nested_uid(self.uid)
        ret["label"] = self.label
        ret["value"] = self.value
        ret["featureNodeHash"] = self.feature_node_hash

        nested_options = self._encode_nested_options()
        if nested_options:
            ret["options"] = nested_options

        return ret

    @abstractmethod
    def _encode_nested_options(self) -> list:
        pass

    @staticmethod
    def _decode_common_option_fields(option_dict: dict) -> dict:
        return {
            "uid": _attribute_id_from_json_str(option_dict["id"]),
            "label": option_dict["label"],
            "value": option_dict["value"],
            "feature_node_hash": option_dict["featureNodeHash"],
        }


@dataclass
class FlatOption(Option):
    """
    This class is currently in BETA. Its API might change in future minor version releases.
    """

    def get_option_type(self) -> OptionType:
        return OptionType.FLAT

    def get_child_by_hash(
        self,
        feature_node_hash: str,
        type_: Union[AttributeTypes, OptionTypes, None] = None,
    ) -> Union[AttributeClasses, OptionClasses]:
        """
        Returns the first child node of this ontology tree node with the matching feature node hash. If there is
        more than one child with the same feature node hash in the ontology tree node, then the ontology would be in
        an invalid state. Throws if nothing is found or if the type is not matched.

        For FlatOptions this will always throw as they have no children.

        Args:
            feature_node_hash: the feature_node_hash of the child node to search for in the ontology.
            type_: The expected type of the item. If the found child does not match the type, an error will be thrown.
        """
        raise OntologyError("No nested attributes for flat options.")

    def get_children_by_title(
        self,
        title: str,
        type_: Union[AttributeTypes, OptionTypes, None] = None,
    ) -> List[Union[AttributeClasses, OptionClasses]]:
        """
        Returns all the child nodes of this ontology tree node with the matching title and matching type if specified.
        Title in ontologies do not need to be unique, however, we recommend unique titles when creating ontologies.

        For FlatOptions this will always return an empty list.

        Args:
            title: The exact title of the child node to search for in the ontology.
            type_: The expected type of the item. Only nodes that match this type will be returned.
        """
        return []

    @classmethod
    def from_dict(cls, d: dict) -> FlatOption:
        return FlatOption(**cls._decode_common_option_fields(d))

    def _encode_nested_options(self) -> list:
        return []


@dataclass
class NestableOption(Option):
    """
    This class is currently in BETA. Its API might change in future minor version releases.
    """

    nested_options: List[Attribute] = field(default_factory=list)

    def get_option_type(self) -> OptionType:
        return OptionType.NESTABLE

    def get_child_by_hash(
        self,
        feature_node_hash: str,
        type_: Union[AttributeTypes, OptionTypes, None] = None,
    ) -> Union[AttributeClasses, OptionClasses]:
        """
        Returns the first child node of this ontology tree node with the matching feature node hash. If there is
        more than one child with the same feature node hash in the ontology tree node, then the ontology would be in
        an invalid state. Throws if nothing is found or if the type is not matched.

        Args:
            feature_node_hash: the feature_node_hash of the child node to search for in the ontology.
            type_: The expected type of the item. If the found child does not match the type, an error will be thrown.
        """
        found_item = _get_attribute_by_hash(feature_node_hash, self.nested_options)
        if found_item is None:
            raise OntologyError("Item not found.")
        check_type(found_item, type_)
        return found_item

    def get_children_by_title(
        self,
        title: str,
        type_: Union[AttributeTypes, OptionTypes, None] = None,
    ) -> List[Union[AttributeClasses, OptionClasses]]:
        """
        Returns all the child nodes of this ontology tree node with the matching title and matching type if specified.
        Title in ontologies do not need to be unique, however, we recommend unique titles when creating ontologies.

        Args:
            title: The exact title of the child node to search for in the ontology.
            type_: The expected type of the item. Only nodes that match this type will be returned.
        """
        found_items = _get_attributes_by_title(title, self.nested_options)
        return filter_by_type(found_items, type_)  # noqa

    def _encode_nested_options(self) -> list:
        return attributes_to_list_dict(self.nested_options)

    @classmethod
    def from_dict(cls, d: dict) -> NestableOption:
        nested_options_ret: List[Attribute] = list()
        if "options" in d:
            for nested_option in d["options"]:
                nested_options_ret.append(attribute_from_dict(nested_option))
        return NestableOption(
            **cls._decode_common_option_fields(d),
            nested_options=nested_options_ret,
        )

    def add_nested_option(
        self,
        cls: Type[T],
        name: str,
        local_uid: Optional[int] = None,
        feature_node_hash: Optional[str] = None,
        required: bool = False,
    ) -> T:
        """
        Adds a nested attribute to a RadioAttribute option.

        Args:
            cls: attribute type, one of `RadioAttribute`, `ChecklistAttribute`, `TextAttribute`
            name: the user-visible name of the attribute
            local_uid: integer identifier of the attribute. Normally auto-generated;
                    omit this unless the aim is to create an exact clone of existing ontology
            feature_node_hash: global identifier of the object. Normally auto-generated;
                    omit this unless the aim is to create an exact clone of existing ontology
            required: whether the label editor would mark this attribute as 'required'

        Returns:
            the created attribute that can be further specified with Options, where appropriate

        Raises:
            ValueError: if specified `local_uid` or `feature_node_hash` violate uniqueness constraints
        """
        return _add_attribute(self.nested_options, cls, name, self.uid, local_uid, feature_node_hash, required)

    def __hash__(self):
        return hash(self.feature_node_hash)


def __build_identifiers(
    existent_items: Union[Attribute, Option],
    local_uid: Optional[int] = None,
    feature_node_hash: Optional[str] = None,
) -> Tuple[int, str]:
    if local_uid is None:
        if existent_items:
            local_uid = max([item.uid[-1] for item in existent_items]) + 1
        else:
            local_uid = 1
    else:
        if any([item.uid[-1] == local_uid for item in existent_items]):
            raise ValueError(f"Duplicate uid '{local_uid}'")

    if feature_node_hash is None:
        feature_node_hash = short_uuid_str()
    elif any([item.feature_node_hash == feature_node_hash for item in existent_items]):
        raise ValueError(f"Duplicate feature_node_hash '{feature_node_hash}'")

    return local_uid, feature_node_hash


T = TypeVar("T", bound=Attribute)


def _add_attribute(
    attributes: List[Attribute],
    cls: Type[T],
    name: str,
    parent_uid: List[int],
    local_uid: Optional[int] = None,
    feature_node_hash: Optional[str] = None,
    required: bool = False,
    dynamic: bool = False,
) -> T:
    local_uid, feature_node_hash = __build_identifiers(attributes, local_uid, feature_node_hash)

    constructor_params = {
        "name": name,
        "uid": parent_uid + [local_uid],
        "feature_node_hash": feature_node_hash,
        "required": required,
        "dynamic": dynamic,
    }

    if cls.has_options_field():
        constructor_params["options"] = []
    attr = cls(**constructor_params)
    attributes.append(attr)
    return attr


OT = TypeVar("OT", bound=Option)


def _add_option(
    options: List[Option],
    cls: Type[OT],
    label: str,
    parent_uid: List[int],
    local_uid: Optional[int] = None,
    feature_node_hash: Optional[str] = None,
    value: Optional[str] = None,
) -> OT:

    local_uid, feature_node_hash = __build_identifiers(options, local_uid, feature_node_hash)
    if not value:
        value = re.sub(r"[\s]", "_", label).lower()
    option = cls(parent_uid + [local_uid], feature_node_hash, label, value)
    options.append(option)
    return option


def _get_option_by_hash(
    feature_node_hash: str, options: List[Option]
) -> Union[RadioAttribute, ChecklistAttribute, TextAttribute, NestableOption, FlatOption, None]:
    for option_ in options:
        if option_.feature_node_hash == feature_node_hash:
            return option_

        if option_.get_option_type() == OptionType.NESTABLE:
            found_item = _get_attribute_by_hash(feature_node_hash, option_.nested_options)
            if found_item is not None:
                return found_item

    return None


def _get_attribute_by_hash(
    feature_node_hash: str, attributes: List[Attribute]
) -> Union[RadioAttribute, ChecklistAttribute, TextAttribute, NestableOption, FlatOption, None]:
    for attribute in attributes:
        if attribute.feature_node_hash == feature_node_hash:
            return attribute

        if attribute.has_options_field():
            found_item = _get_option_by_hash(feature_node_hash, attribute.options)
            if found_item is not None:
                return found_item
    return None


def _get_options_by_title(
    title: str, options: List[Option]
) -> List[Union[RadioAttribute, ChecklistAttribute, TextAttribute, NestableOption, FlatOption]]:
    ret = []
    for option_ in options:
        if option_.label == title:
            ret.append(option_)

        if option_.get_option_type() == OptionType.NESTABLE:
            found_items = _get_attributes_by_title(title, option_.nested_options)
            ret.extend(found_items)

    return ret


def _get_attributes_by_title(
    title: str, attributes: List[Attribute]
) -> List[Union[RadioAttribute, ChecklistAttribute, TextAttribute, NestableOption, FlatOption]]:
    ret = []
    for attribute in attributes:
        if attribute.name == title:
            ret.append(attribute)

        if attribute.has_options_field():
            found_items = _get_options_by_title(title, attribute.options)
            ret.extend(found_items)
    return ret


def _handle_wrong_number_of_found_items(
    found_items: List[Union[RadioAttribute, ChecklistAttribute, TextAttribute, NestableOption, FlatOption]],
    title: str,
    type_: Any,
) -> None:
    if len(found_items) == 0:
        raise OntologyError(f"No item was found in the ontology with the given title `{title}` and type `{type_}`")
    elif len(found_items) > 1:
        raise OntologyError(
            f"More than one item was found in the ontology with the given title `{title}` and type `{type_}`. "
            f"Use the `get_children_by_title` or `get_child_by_hash` function instead. "
            f"The found items are `{found_items}`."
        )


AttributeTypes = Union[
    Type[RadioAttribute],
    Type[ChecklistAttribute],
    Type[TextAttribute],
    Type[Attribute],
]
AttributeClasses = Union[RadioAttribute, ChecklistAttribute, TextAttribute, Attribute]
OptionTypes = Union[Type[FlatOption], Type[NestableOption], Type[Option]]
OptionClasses = Union[FlatOption, NestableOption, Option]
