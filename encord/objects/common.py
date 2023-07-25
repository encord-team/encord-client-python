from __future__ import annotations

import re
from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from encord.common.enum import StringEnum
from encord.objects.ontology_element import (
    OntologyElement,
    OntologyNestedElement,
    _get_element_by_hash,
)
from encord.objects.utils import _decode_nested_uid, short_uuid_str

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
    BITMASK = "bitmask"


OptionType = TypeVar("OptionType", bound="Option")


class Attribute(OntologyNestedElement, Generic[OptionType]):
    """
    Base class for shared Attribute fields
    """

    name: str
    required: bool
    dynamic: bool
    """
    The `dynamic` member is part of every attribute. However it can only be true for top level (not nested) attributes
    that are part of an :class:`encord.objects.ontology_object.Object`.
    """

    def __init__(self, uid: NestedID, feature_node_hash: str, name: str, required: bool, dynamic: bool):
        super().__init__(uid=uid, feature_node_hash=feature_node_hash)
        self.name = name
        self.required = required
        self.dynamic = dynamic

    @property
    def options(self) -> Sequence[OptionType]:
        return []

    @property
    def title(self) -> str:
        return self.name

    @staticmethod
    @abstractmethod
    def get_property_type() -> PropertyType:
        pass

    @staticmethod
    @abstractmethod
    def _get_property_type_name() -> str:
        pass

    @abstractmethod
    def _encode_options(self) -> Optional[List[dict]]:
        pass

    def to_dict(self) -> Dict[str, Any]:
        ret = self._encode_base()

        options = self._encode_options()
        if options is not None:
            ret["options"] = options

        return ret

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Attribute:
        property_type = d["type"]
        common_attribute_fields = cls._decode_common_attribute_fields(d)
        if property_type == RadioAttribute._get_property_type_name():
            return RadioAttribute(
                **common_attribute_fields,
                options=[NestableOption.from_dict(x) for x in d.get("options", [])],
            )

        elif property_type == ChecklistAttribute._get_property_type_name():
            return ChecklistAttribute(
                **common_attribute_fields,
                options=[FlatOption.from_dict(x) for x in d.get("options", [])],
            )

        elif property_type == TextAttribute._get_property_type_name():
            return TextAttribute(
                **common_attribute_fields,
            )

        raise TypeError(
            f"Attribute is ill-formed: '{d}'. Expected to see either "
            f"attribute specific fields or option specific fields. Got both or none of them."
        )

    def _encode_base(self) -> Dict[str, Any]:
        ret: Dict[str, Any] = dict()
        ret["id"] = _decode_nested_uid(self.uid)
        ret["name"] = self.name
        ret["type"] = self._get_property_type_name()
        ret["featureNodeHash"] = self.feature_node_hash
        ret["required"] = self.required
        ret["dynamic"] = self.dynamic

        return ret

    @staticmethod
    def _decode_common_attribute_fields(attribute_dict: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "uid": _attribute_id_from_json_str(attribute_dict["id"]),
            "feature_node_hash": attribute_dict["featureNodeHash"],
            "name": attribute_dict["name"],
            "required": attribute_dict["required"],
            "dynamic": attribute_dict.get("dynamic", False),
        }

    def __eq__(self, other: object):
        return (
            isinstance(other, Attribute) and self.uid == other.uid and self.feature_node_hash == other.feature_node_hash
        )


class RadioAttribute(Attribute["NestableOption"]):
    _options: List[NestableOption]

    def __init__(
        self,
        uid: NestedID,
        feature_node_hash: str,
        name: str,
        required: bool,
        dynamic: bool,
        options: Optional[List[NestableOption]] = None,
    ):
        super().__init__(uid, feature_node_hash, name, required, dynamic)
        self._options = options if options is not None else []

    @property
    def options(self) -> Sequence[NestableOption]:
        return self._options

    @property
    def children(self) -> Sequence[OntologyElement]:
        return self._options

    @staticmethod
    def get_property_type() -> PropertyType:
        return PropertyType.RADIO

    @staticmethod
    def _get_property_type_name() -> str:
        return PropertyType.RADIO.value

    def _encode_options(self) -> Optional[List[Dict[str, Any]]]:
        if len(self._options) == 0:
            return None
        return [option.to_dict() for option in self._options]

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
        return _add_option(self._options, NestableOption, label, self.uid, local_uid, feature_node_hash, value)


class ChecklistAttribute(Attribute["FlatOption"]):
    _options: List[FlatOption]

    def __init__(
        self,
        uid: NestedID,
        feature_node_hash: str,
        name: str,
        required: bool,
        dynamic: bool,
        options: Optional[List[FlatOption]] = None,
    ):
        super().__init__(uid, feature_node_hash, name, required, dynamic)
        self._options = options if options is not None else []

    @staticmethod
    def get_property_type() -> PropertyType:
        return PropertyType.CHECKLIST

    @staticmethod
    def _get_property_type_name() -> str:
        return PropertyType.CHECKLIST.value

    def _encode_options(self) -> Optional[List[Dict[str, Any]]]:
        if len(self._options) == 0:
            return None
        return [option.to_dict() for option in self._options]

    @property
    def options(self) -> Sequence[FlatOption]:
        return self._options

    @property
    def children(self) -> Sequence[OntologyElement]:
        return self._options

    def add_option(
        self,
        label: str,
        value: Optional[str] = None,
        local_uid: Optional[int] = None,
        feature_node_hash: Optional[str] = None,
    ) -> FlatOption:
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
        return _add_option(self._options, FlatOption, label, self.uid, local_uid, feature_node_hash, value)


class TextAttribute(Attribute["FlatOption"]):
    def __init__(self, uid: NestedID, feature_node_hash: str, name: str, required: bool, dynamic: bool):
        super().__init__(uid, feature_node_hash, name, required, dynamic)

    @staticmethod
    def get_property_type() -> PropertyType:
        return PropertyType.TEXT

    @staticmethod
    def _get_property_type_name() -> str:
        return PropertyType.TEXT.value

    def _encode_options(self) -> Optional[List[Dict[str, Any]]]:
        return None


def _attribute_id_from_json_str(attribute_id: str) -> NestedID:
    nested_ids = attribute_id.split(".")
    return [int(x) for x in nested_ids]


def attribute_from_dict(d: Dict[str, Any]) -> Attribute:
    """Convenience functions as you cannot call static member on union types."""
    return Attribute.from_dict(d)


def attributes_to_list_dict(attributes: List[Attribute]) -> list:
    attributes_list = list()
    for attribute in attributes:
        attributes_list.append(attribute.to_dict())

    return attributes_list


@dataclass
class Option(OntologyNestedElement):
    """
    Base class for shared Option fields
    """

    label: str
    value: str

    @property
    def title(self) -> str:
        return self.label

    @abstractmethod
    def is_nestable(self) -> bool:
        raise NotImplementedError("This method is not implemented for this class")

    @property
    @abstractmethod
    def attributes(self) -> List[Attribute]:
        raise NotImplementedError("This method is not implemented for this class")

    def to_dict(self) -> Dict[str, Any]:
        ret: Dict[str, Any] = dict()
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
    def _decode_common_option_fields(option_dict: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "uid": _attribute_id_from_json_str(option_dict["id"]),
            "label": option_dict["label"],
            "value": option_dict["value"],
            "feature_node_hash": option_dict["featureNodeHash"],
        }


@dataclass
class FlatOption(Option):
    def is_nestable(self) -> bool:
        return False

    @property
    def attributes(self) -> List[Attribute]:
        return []

    @classmethod
    def from_dict(cls, d: dict) -> FlatOption:
        return FlatOption(**cls._decode_common_option_fields(d))

    def _encode_nested_options(self) -> list:
        return []


@dataclass
class NestableOption(Option):
    nested_options: List[Attribute] = field(default_factory=list)

    def is_nestable(self) -> bool:
        return True

    @property
    def attributes(self) -> List[Attribute]:
        return self.nested_options

    @property
    def children(self) -> Sequence[OntologyElement]:
        return self.nested_options

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
    existent_items: Iterable[OntologyNestedElement],
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
    attr = cls(
        name=name, uid=parent_uid + [local_uid], feature_node_hash=feature_node_hash, required=required, dynamic=dynamic
    )

    attributes.append(attr)
    return attr


OT = TypeVar("OT", bound=Option)


def _add_option(
    options: List[OT],
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
    option = cls(uid=parent_uid + [local_uid], feature_node_hash=feature_node_hash, label=label, value=value)
    options.append(option)
    return option


def _get_option_by_hash(feature_node_hash: str, options: Iterable[Option]) -> Optional[Option]:
    return _get_element_by_hash(feature_node_hash, options, type_=Option)


def _get_attribute_by_hash(feature_node_hash: str, attributes: List[Attribute]) -> Optional[Attribute]:
    return _get_element_by_hash(feature_node_hash, attributes, type_=Attribute)


OptionAttribute = Union[RadioAttribute, ChecklistAttribute]
AttributeTypes = Union[
    Type[RadioAttribute],
    Type[ChecklistAttribute],
    Type[TextAttribute],
    Type[Attribute],
]
OptionTypes = Union[Type[FlatOption], Type[NestableOption], Type[Option]]

# Two types below are kept for the backwards compatibility
# Please don't use them, as they are going to be removed in the future versions
AttributeClasses = Union[RadioAttribute, ChecklistAttribute, TextAttribute, Attribute]
OptionClasses = Union[FlatOption, NestableOption, Option]


class DeidentifyRedactTextMode(Enum):
    REDACT_ALL_TEXT = "REDACT_ALL_TEXT"
    REDACT_NO_TEXT = "REDACT_NO_TEXT"
    REDACT_SENSITIVE_TEXT = "REDACT_SENSITIVE_TEXT"


class SaveDeidentifiedDicomConditionType(Enum):
    NOT_SUBSTR = "NOT_SUBSTR"
    IN = "IN"


@dataclass
class SaveDeidentifiedDicomConditionIn:
    value: List[str]
    dicom_tag: str
    condition_type: SaveDeidentifiedDicomConditionType = SaveDeidentifiedDicomConditionType.IN

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "dicom_tag": self.dicom_tag,
            "condition_type": self.condition_type.value,
        }


@dataclass
class SaveDeidentifiedDicomConditionNotSubstr:
    value: str
    dicom_tag: str
    condition_type: SaveDeidentifiedDicomConditionType = SaveDeidentifiedDicomConditionType.NOT_SUBSTR

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "dicom_tag": self.dicom_tag,
            "condition_type": self.condition_type.value,
        }


SaveDeidentifiedDicomCondition = Union[
    SaveDeidentifiedDicomConditionNotSubstr,
    SaveDeidentifiedDicomConditionIn,
]
