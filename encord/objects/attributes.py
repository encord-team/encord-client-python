from __future__ import annotations

from abc import abstractmethod
from typing import Any, Dict, Generic, List, Optional, Sequence, Type, TypeVar

from encord.objects.ontology_element import (
    OntologyElement,
    OntologyNestedElement,
    __build_identifiers,
    _get_element_by_hash,
    _nested_id_from_json_str,
)
from encord.objects.utils import _decode_nested_uid

OptionType = TypeVar("OptionType", bound="Option")
AttributeType = TypeVar("AttributeType", bound="Attribute")


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
            "uid": _nested_id_from_json_str(attribute_dict["id"]),
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


def attribute_from_dict(d: Dict[str, Any]) -> Attribute:
    """Convenience functions as you cannot call static member on union types."""
    return Attribute.from_dict(d)


def _add_attribute(
    attributes: List[Attribute],
    cls: Type[AttributeType],
    name: str,
    parent_uid: List[int],
    local_uid: Optional[int] = None,
    feature_node_hash: Optional[str] = None,
    required: bool = False,
    dynamic: bool = False,
) -> AttributeType:
    local_uid, feature_node_hash = __build_identifiers(attributes, local_uid, feature_node_hash)
    attr = cls(
        name=name, uid=parent_uid + [local_uid], feature_node_hash=feature_node_hash, required=required, dynamic=dynamic
    )

    attributes.append(attr)
    return attr


def _get_attribute_by_hash(feature_node_hash: str, attributes: List[Attribute]) -> Optional[Attribute]:
    return _get_element_by_hash(feature_node_hash, attributes, type_=Attribute)


def attributes_to_list_dict(attributes: List[Attribute]) -> List[Dict[str, Any]]:
    return [attribute.to_dict() for attribute in attributes]


from encord.objects.common import NestedID, PropertyType
from encord.objects.options import (  # pylint: disable=unused-import
    FlatOption,
    NestableOption,
    Option,
    _add_option,
)
