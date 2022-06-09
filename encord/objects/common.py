from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Union

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
    options: List[NestableOption] = field(default_factory=list)

    def get_property_type(self) -> PropertyType:
        return PropertyType.RADIO

    def has_options_field(self) -> bool:
        return True


@dataclass
class ChecklistAttribute(_AttributeBase):
    options: List[FlatOption] = field(default_factory=list)

    def get_property_type(self) -> PropertyType:
        return PropertyType.CHECKLIST

    def has_options_field(self) -> bool:
        return True


@dataclass
class TextAttribute(_AttributeBase):
    def get_property_type(self) -> PropertyType:
        return PropertyType.TEXT

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
    def get_option_type(self) -> OptionType:
        return OptionType.FLAT

    @classmethod
    def from_dict(cls, d: dict) -> FlatOption:
        return FlatOption(**cls._decode_common_option_fields(d))

    def _encode_nested_options(self) -> list:
        return []


@dataclass
class NestableOption(_OptionBase):
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


Option = Union[FlatOption, NestableOption]
"""
This class is currently in BETA. Its API might change in future minor version releases. 
"""
