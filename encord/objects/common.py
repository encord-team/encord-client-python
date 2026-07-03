from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Union

from encord.common.enum import StringEnum
from encord.objects.attributes import (  # pylint: disable=unused-import
    Attribute as Attribute,
)
from encord.objects.attributes import (
    ChecklistAttribute as ChecklistAttribute,
)
from encord.objects.attributes import (
    RadioAttribute as RadioAttribute,
)
from encord.objects.attributes import (
    TextAttribute as TextAttribute,
)

# Following imports need to be here for backwards compatibility
from encord.objects.ontology_element import NestedID as NestedID  # pylint: disable=unused-import
from encord.objects.options import (  # pylint: disable=unused-import
    FlatOption as FlatOption,
)
from encord.objects.options import (
    NestableOption as NestableOption,
)
from encord.objects.options import (
    Option as Option,
)


class PropertyType(StringEnum):
    """
    Enumeration of supported classification and attribute types

    Values:
        radio
        text
        checklist
        numeric
    """

    RADIO = "radio"
    TEXT = "text"
    CHECKLIST = "checklist"
    NUMERIC = "numeric"


class Shape(StringEnum):
    """
    Enumeration of supported geometric and data shapes for labeling.

    Values:
        bounding_box
        polygon
        point
        skeleton
        polyline
        rotatable_bounding_box
        bitmask
        audio
        time_range
        text
        cuboid
        cuboid_2d
        segmentation
        circle
        ellipse
    """

    BOUNDING_BOX = "bounding_box"
    POLYGON = "polygon"
    POINT = "point"
    SKELETON = "skeleton"
    POLYLINE = "polyline"
    ROTATABLE_BOUNDING_BOX = "rotatable_bounding_box"
    BITMASK = "bitmask"
    AUDIO = "audio"
    TIME_RANGE = "time_range"
    TEXT = "text"
    CUBOID = "cuboid"
    CUBOID_2D = "cuboid_2d"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"
    SEGMENTATION = "segmentation"


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
