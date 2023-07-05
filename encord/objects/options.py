from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Type, TypeVar

from encord.objects.attributes import Attribute
from encord.objects.common import NestedID, OntologyNestedElement


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
