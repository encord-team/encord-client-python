"""
---
title: "Objects - Options"
slug: "sdk-ref-objects-options"
hidden: false
metadata:
  title: "Objects - Options"
  description: "Encord SDK Objects - Options."
category: "64e481b57b6027003f20aaa0"
---
"""

from __future__ import annotations

import re
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, TypeVar
from collections.abc import Iterable, Sequence

from encord.common.deprecated import deprecated
from encord.objects.ontology_element import (
    OntologyElement,
    OntologyNestedElement,
    _build_identifiers,
    _decode_nested_uid,
    _get_element_by_hash,
    _nested_id_from_json_str,
)


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
    def attributes(self) -> list[Attribute]:
        raise NotImplementedError("This method is not implemented for this class")

    def to_dict(self) -> dict[str, Any]:
        ret: dict[str, Any] = dict()
        ret["id"] = _decode_nested_uid(self.uid)
        ret["label"] = self.label
        ret["value"] = self.value
        ret["featureNodeHash"] = self.feature_node_hash

        if nested_options := self._encode_nested_options():
            ret["options"] = nested_options

        return ret

    @abstractmethod
    def _encode_nested_options(self) -> list:
        pass

    @staticmethod
    def _decode_common_option_fields(option_dict: dict[str, Any]) -> dict[str, Any]:
        return {
            "uid": _nested_id_from_json_str(option_dict["id"]),
            "label": option_dict["label"],
            "value": option_dict["value"],
            "feature_node_hash": option_dict["featureNodeHash"],
        }


@dataclass
class FlatOption(Option):
    def is_nestable(self) -> bool:
        return False

    @property
    def attributes(self) -> list[Attribute]:
        return []

    @classmethod
    def from_dict(cls, d: dict) -> FlatOption:
        return FlatOption(**cls._decode_common_option_fields(d))

    def _encode_nested_options(self) -> list:
        return []


AttributeType = TypeVar("AttributeType", bound="Attribute")


@dataclass
class NestableOption(Option):
    nested_options: list[Attribute] = field(default_factory=list)

    def is_nestable(self) -> bool:
        return True

    @property
    def attributes(self) -> list[Attribute]:
        return self.nested_options

    @property
    def children(self) -> Sequence[OntologyElement]:
        return self.nested_options

    def _encode_nested_options(self) -> list:
        return attributes_to_list_dict(self.nested_options)

    @classmethod
    def from_dict(cls, d: dict) -> NestableOption:
        nested_options_ret = [attribute_from_dict(nested_option) for nested_option in d.get("options", [])]
        return NestableOption(
            **cls._decode_common_option_fields(d),
            nested_options=nested_options_ret,
        )

    @deprecated(version="0.1.100", alternative=".add_nested_attribute")
    def add_nested_option(
        self,
        cls: type[AttributeType],
        name: str,
        local_uid: int | None = None,
        feature_node_hash: str | None = None,
        required: bool = False,
    ) -> AttributeType:
        """
        This method is deprecated, please use :meth:`.add_nested_option` instead.
        There is no functional difference between these methods.
        """
        return self.add_nested_attribute(
            cls=cls, name=name, local_uid=local_uid, feature_node_hash=feature_node_hash, required=required
        )

    def add_nested_attribute(
        self,
        cls: type[AttributeType],
        name: str,
        local_uid: int | None = None,
        feature_node_hash: str | None = None,
        required: bool = False,
    ) -> AttributeType:
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


OT = TypeVar("OT", bound=Option)


def _add_option(
    options: list[OT],
    cls: type[OT],
    label: str,
    parent_uid: list[int],
    local_uid: int | None = None,
    feature_node_hash: str | None = None,
    value: str | None = None,
) -> OT:
    local_uid, feature_node_hash = _build_identifiers(options, local_uid, feature_node_hash)
    if not value:
        value = re.sub(r"\s", "_", label).lower()
    option = cls(uid=parent_uid + [local_uid], feature_node_hash=feature_node_hash, label=label, value=value)
    options.append(option)
    return option


def _get_option_by_hash(feature_node_hash: str, options: Iterable[Option]) -> Option | None:
    return _get_element_by_hash(feature_node_hash, options, type_=Option)


from encord.objects.attributes import (
    Attribute,
    _add_attribute,
    attribute_from_dict,
    attributes_to_list_dict,
)
