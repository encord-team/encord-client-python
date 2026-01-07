from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from itertools import chain
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Literal,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    cast,
)

from pydantic import parse_obj_as

from encord.common.range_manager import RangeManager
from encord.common.time_parser import format_datetime_to_long_string
from encord.constants.enums import SpaceType
from encord.exceptions import LabelRowError
from encord.objects.answers import NumericAnswerValue
from encord.objects.attributes import (
    Attribute,
    ChecklistAttribute,
    NumericAttribute,
    RadioAttribute,
    TextAttribute,
    _get_attribute_by_hash,
)
from encord.objects.coordinates import (
    GeometricCoordinates,
    add_coordinates_to_frame_object_dict,
    get_geometric_coordinates_from_frame_object_dict,
)
from encord.objects.frames import Frames, Ranges, frames_class_to_frames_list, ranges_list_to_ranges, ranges_to_list
from encord.objects.internal_helpers import _infer_attribute_from_answer
from encord.objects.label_utils import create_frame_classification_dict, create_frame_object_dict
from encord.objects.ontology_object_instance import AnswersForFrames, DynamicAnswerManager, check_coordinate_type
from encord.objects.spaces.annotation.base_annotation import _AnnotationData, _AnnotationMetadata
from encord.objects.spaces.annotation.geometric_annotation import (
    _FrameClassificationAnnotation,
    _GeometricAnnotationData,
    _GeometricFrameObjectAnnotation,
)
from encord.objects.spaces.annotation.global_annotation import _GlobalClassificationAnnotation
from encord.objects.spaces.base_space import Space
from encord.objects.spaces.multiframe_space.multiframe_space import MultiFrameSpace
from encord.objects.spaces.types import SpaceInfo, VideoSpaceInfo
from encord.objects.types import (
    AttributeDict,
    ClassificationAnswer,
    DynamicAttributeObject,
    FrameClassification,
    FrameObject,
    LabelBlob,
    ObjectAnswer,
    ObjectAnswerForGeometric,
    SpaceFrameData,
    _is_global_classification_on_space,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from encord.objects import Classification, ClassificationInstance, Option
    from encord.objects.ontology_labels_impl import LabelRowV2
    from encord.objects.ontology_object import Object, ObjectInstance

FrameOverlapStrategy = Union[Literal["error"], Literal["replace"]]


class VideoSpace(MultiFrameSpace):
    """Video space implementation for frame-based video annotations."""

    pass
