from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Type, TypeVar, Union

from encord.common.enum import StringEnum
from encord.objects.attributes import (
    Attribute,
    ChecklistAttribute,
    RadioAttribute,
    TextAttribute,
)
from encord.objects.options import FlatOption, NestableOption, Option

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

T = TypeVar("T", bound=Attribute)

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
