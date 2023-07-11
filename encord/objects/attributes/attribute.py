from __future__ import annotations

from abc import abstractmethod
from typing import Any, Dict, Generic, List, Optional, Sequence, Type, TypeVar

from encord.objects.common import NestedID, PropertyType, _attribute_id_from_json_str
from encord.objects.internal_helpers import __build_identifiers
from encord.objects.ontology_element import OntologyNestedElement
from encord.objects.utils import _decode_nested_uid

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


AttributeT = TypeVar("AttributeT", bound=Attribute)


def _add_attribute(
    attributes: List[Attribute],
    cls: Type[AttributeT],
    name: str,
    parent_uid: List[int],
    local_uid: Optional[int] = None,
    feature_node_hash: Optional[str] = None,
    required: bool = False,
    dynamic: bool = False,
) -> AttributeT:
    local_uid, feature_node_hash = __build_identifiers(attributes, local_uid, feature_node_hash)
    attr = cls(
        name=name, uid=parent_uid + [local_uid], feature_node_hash=feature_node_hash, required=required, dynamic=dynamic
    )

    attributes.append(attr)
    return attr
