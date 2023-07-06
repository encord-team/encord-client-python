from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from encord.common.enum import StringEnum
from encord.objects.utils import (
    check_type,
    checked_cast,
    does_type_match,
    short_uuid_str,
)

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


def _attribute_id_from_json_str(attribute_id: str) -> NestedID:
    nested_ids = attribute_id.split(".")
    return [int(x) for x in nested_ids]


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
