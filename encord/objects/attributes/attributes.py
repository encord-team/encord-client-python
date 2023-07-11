from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from encord.objects.attributes.attribute import Attribute
from encord.objects.common import NestedID, PropertyType
from encord.objects.ontology_element import OntologyElement
from encord.objects.options import FlatOption, NestableOption, _add_option


class RadioAttribute(Attribute[NestableOption]):
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


class ChecklistAttribute(Attribute[FlatOption]):
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


def attributes_to_list_dict(attributes: List[Attribute]) -> list:
    return [attribute.to_dict() for attribute in attributes]


def attribute_from_dict(d: Dict[str, Any]) -> Attribute:
    """Convenience functions as you cannot call static member on union types."""

    property_type = d["type"]
    common_attribute_fields = Attribute._decode_common_attribute_fields(d)
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
