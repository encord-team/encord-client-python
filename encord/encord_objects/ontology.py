from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Union

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


def _decode_nested_uid(nested_uid: list) -> str:
    return ".".join([str(uid) for uid in nested_uid])


def _attribute_id_from_json_str(attribute_id: str) -> NestedID:
    nested_ids = attribute_id.split(".")
    return [int(x) for x in nested_ids]


@dataclass
class _AttributeBase(ABC):
    """
    Just a trick to forward declare the Attribute dataclass for better typing support.
    Do not instantiate this dataclass directly.
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
OptionAttribute = Union[RadioAttribute, ChecklistAttribute]


@dataclass
class Classification:
    uid: int
    feature_node_hash: str
    attributes: List[Attribute]

    @classmethod
    def from_dict(cls, d: dict) -> Classification:
        attributes_ret: List[Attribute] = list()
        for attribute_dict in d["attributes"]:
            attributes_ret.append(attribute_from_dict(attribute_dict))

        return Classification(
            uid=int(d["id"]),
            feature_node_hash=d["featureNodeHash"],
            attributes=attributes_ret,
        )

    def to_dict(self) -> dict:
        ret = dict()
        ret["id"] = str(self.uid)
        ret["featureNodeHash"] = self.feature_node_hash

        attributes_list = attributes_to_list_dict(self.attributes)
        if attributes_list:
            ret["attributes"] = attributes_list

        return ret


@dataclass
class Object:
    uid: int
    name: str
    color: str
    shape: Shape
    # DENIS: rename this?
    feature_node_hash: str
    attributes: List[Attribute] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> Object:
        shape_opt = Shape.from_string(d["shape"])
        if shape_opt is None:
            raise TypeError(f"The shape '{d['shape']}' of the object '{d}' is not recognised")

        attributes_ret: List[Attribute] = list()
        if "attributes" in d:
            for attribute_dict in d["attributes"]:
                attributes_ret.append(attribute_from_dict(attribute_dict))

        object_ret = Object(
            uid=int(d["id"]),
            name=d["name"],
            color=d["color"],
            shape=shape_opt,
            feature_node_hash=d["featureNodeHash"],
            attributes=attributes_ret,
        )

        return object_ret

    def to_dict(self) -> dict:
        ret = dict()
        ret["id"] = str(self.uid)
        ret["name"] = self.name
        ret["color"] = self.color
        ret["shape"] = self.shape.value
        ret["featureNodeHash"] = self.feature_node_hash

        attributes_list = attributes_to_list_dict(self.attributes)
        if attributes_list:
            ret["attributes"] = attributes_list

        return ret


@dataclass
class Ontology:
    # could add the project_uid here
    objects: List[Object] = field(default_factory=list)
    classifications: List[Classification] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> Ontology:
        """
        Args:
            d: a JSON blob of an "editor

        Raises:
            KeyError: If the dict is missing a required field.
        """
        objects_ret: List[Object] = list()
        for object_dict in d["objects"]:
            objects_ret.append(Object.from_dict(object_dict))

        classifications_ret: List[Classification] = list()
        for classification_dict in d["classifications"]:
            classifications_ret.append(Classification.from_dict(classification_dict))

        return Ontology(objects=objects_ret, classifications=classifications_ret)

    def to_dict(self) -> dict:
        """
        Args:
            ontology_instance: an ontology.Ontology object

        Returns:
            The dict equivalent to the ontology which can be inserted as an `editor` row
                within the `projects` table.

        Raises:
            KeyError: If the dict is missing a required field.
        """
        ret = dict()
        ontology_objects = list()
        ret["objects"] = ontology_objects
        for ontology_object in self.objects:
            ontology_objects.append(ontology_object.to_dict())

        ontology_classifications = list()
        ret["classifications"] = ontology_classifications
        for ontology_classification in self.classifications:
            ontology_classifications.append(ontology_classification.to_dict())

        return ret
