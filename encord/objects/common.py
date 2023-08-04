from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Union

from encord.common.enum import StringEnum
from encord.objects.attributes import (  # pylint: disable=unused-import
    Attribute,
    ChecklistAttribute,
    RadioAttribute,
    TextAttribute,
)

# Following imports need to be here for backwards compatibility
from encord.objects.ontology_element import NestedID  # pylint: disable=unused-import
from encord.objects.options import (  # pylint: disable=unused-import
    FlatOption,
    NestableOption,
    Option,
)


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
