from __future__ import annotations

import re
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Tuple, Type, TypeVar, Union

from encord.objects.utils import _decode_nested_uid
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


@dataclass
class _AttributeBase(ABC):
    """
    Base class for shared Attribute fields
    """

    uid: NestedID
    feature_node_hash: str
    name: str
    required: bool

    @abstractmethod
    def get_property_type(self) -> PropertyType:
        pass

    @classmethod
    @abstractmethod
    def has_options_field(self) -> bool:
        pass

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
        }


@dataclass
class RadioAttribute(_AttributeBase):
    """
    This class is currently in BETA. Its API might change in future minor version releases.
    """

    options: List[NestableOption] = field(default_factory=list)

    def get_property_type(self) -> PropertyType:
        return PropertyType.RADIO

    @classmethod
    def has_options_field(self) -> bool:
        return True

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
class ChecklistAttribute(_AttributeBase):
    """
    This class is currently in BETA. Its API might change in future minor version releases.
    """

    options: List[FlatOption] = field(default_factory=list)

    def get_property_type(self) -> PropertyType:
        return PropertyType.CHECKLIST

    @classmethod
    def has_options_field(self) -> bool:
        return True

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
class TextAttribute(_AttributeBase):
    """
    This class is currently in BETA. Its API might change in future minor version releases.
    """

    def get_property_type(self) -> PropertyType:
        return PropertyType.TEXT

    @classmethod
    def has_options_field(self) -> bool:
        return False


Attribute = Union[RadioAttribute, ChecklistAttribute, TextAttribute]
"""
This class is currently in BETA. Its API might change in future minor version releases. 
"""
OptionAttribute = Union[RadioAttribute, ChecklistAttribute]
"""
This class is currently in BETA. Its API might change in future minor version releases. 
"""


def _attribute_id_from_json_str(attribute_id: str) -> NestedID:
    nested_ids = attribute_id.split(".")
    return [int(x) for x in nested_ids]


def attribute_from_dict(d: dict) -> Attribute:
    """Convenience functions as you cannot call static member on union types."""
    return _AttributeBase.from_dict(d)


def attributes_to_list_dict(attributes: List[Attribute]) -> list:
    attributes_list = list()
    for attribute in attributes:
        attributes_list.append(attribute.to_dict())

    return attributes_list


class OptionType(Enum):
    FLAT = auto()
    NESTABLE = auto()


@dataclass
class _OptionBase(ABC):
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
class FlatOption(_OptionBase):
    """
    This class is currently in BETA. Its API might change in future minor version releases.
    """

    def get_option_type(self) -> OptionType:
        return OptionType.FLAT

    @classmethod
    def from_dict(cls, d: dict) -> FlatOption:
        return FlatOption(**cls._decode_common_option_fields(d))

    def _encode_nested_options(self) -> list:
        return []


@dataclass
class NestableOption(_OptionBase):
    """
    This class is currently in BETA. Its API might change in future minor version releases.
    """

    nested_options: List[Attribute] = field(default_factory=list)

    def get_option_type(self) -> OptionType:
        return OptionType.NESTABLE

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


Option = Union[FlatOption, NestableOption]
"""
This class is currently in BETA. Its API might change in future minor version releases. 
"""


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
        feature_node_hash = str(uuid.uuid4())[:8]
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
) -> T:
    local_uid, feature_node_hash = __build_identifiers(attributes, local_uid, feature_node_hash)

    constructor_params = {
        "name": name,
        "uid": parent_uid + [local_uid],
        "feature_node_hash": feature_node_hash,
        "required": required,
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
