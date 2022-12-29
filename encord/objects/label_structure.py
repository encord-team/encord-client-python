from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from copy import copy, deepcopy
from dataclasses import Field, dataclass, field
from datetime import datetime
from enum import Flag, auto
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    NoReturn,
    Optional,
    Set,
    Type,
    Union,
    overload,
)

import pytz
from dateutil.parser import parse

from encord.constants.enums import DataType
from encord.objects.classification import Classification
from encord.objects.common import (
    Attribute,
    ChecklistAttribute,
    FlatOption,
    NestableOption,
    Option,
    OptionType,
    PropertyType,
    RadioAttribute,
    Shape,
    TextAttribute,
)
from encord.objects.ontology_object import Object
from encord.objects.ontology_structure import OntologyStructure
from encord.objects.utils import short_uuid_str
from encord.orm.ontology import DATETIME_STRING_FORMAT

"""
DENIS:
I'd like to optimise the reads and writes.

For reads I needs some associations

For writes I need the builder pattern same as the OntologyStructure.

"""
# DENIS: think about better error codes for people to catch.

DEFAULT_CONFIDENCE = 1
DEFAULT_MANUAL_ANNOTATION = True


DATETIME_LONG_STRING_FORMAT = "%a, %d %b %Y %H:%M:%S %Z"


@dataclass
class Range:
    start: int
    end: int


Ranges = List[Range]

Frames = Union[int, Range, Ranges]


class _Answer(ABC):
    """Common fields amongst all answers
    DENIS: use this class instead of the Union below.
    """

    _ontology_attribute: Attribute

    def __init__(self, ontology_attribute: Attribute):
        self._answered = False
        self._ontology_attribute = ontology_attribute
        self._answer_uuid = short_uuid_str()
        self._is_manual_annotation = DEFAULT_MANUAL_ANNOTATION

    def is_answered(self) -> bool:
        return self._answered

    def unset(self) -> None:
        """Remove the value from the answer"""
        self._answered = False
        # DENIS: might be better to default everything again for more consistent states!

    @property
    def is_dynamic(self) -> bool:
        return self._ontology_attribute.dynamic

    @is_dynamic.setter
    def is_dynamic(self, value: bool) -> NoReturn:
        raise RuntimeError("Cannot set the is_dynamic value of the answer.")

    @property
    def is_manual_annotation(self) -> bool:
        return self._is_manual_annotation

    @is_manual_annotation.setter
    def is_manual_annotation(self, value: bool) -> None:
        self._is_manual_annotation = value

    @property
    def ontology_attribute(self):
        return deepcopy(self._ontology_attribute)

    @ontology_attribute.setter
    def ontology_attribute(self, v: Any) -> NoReturn:
        raise RuntimeError("Cannot reset the ontology attribute of an instantiated answer.")

    @abstractmethod
    def _to_encord_dict(self) -> Optional[Dict]:
        """Return None if the answer is not answered"""
        pass

    @abstractmethod
    def from_dict(self, d: Dict) -> None:
        pass


class TextAnswer(_Answer):
    def __init__(self, ontology_attribute: TextAttribute):
        super().__init__(ontology_attribute)
        self._value = None

    def set(self, value: str) -> TextAnswer:
        """Returns the object itself"""
        if not isinstance(value, str):
            raise ValueError("TextAnswer can only be set to a string.")
        self._value = value
        self._answered = True
        return self

    def get_value(self) -> Optional[str]:
        if not self.is_answered():
            return None
        else:
            return self._value

    def copy_from(self, text_answer: TextAnswer):
        if text_answer.ontology_attribute.feature_node_hash != self.ontology_attribute.feature_node_hash:
            raise ValueError(
                "Copying from a TextAnswer which is based on a different ontology Attribute is not possible."
            )
        other_is_answered = text_answer.is_answered()
        if not other_is_answered:
            self.unset()
        else:
            other_answer = text_answer.get_value()
            self.set(other_answer)

    def _to_encord_dict(self) -> Optional[Dict]:
        if not self.is_answered():
            return None
        else:
            return {
                "name": self.ontology_attribute.name,
                "value": _lower_snake_case(self.ontology_attribute.name),
                # DENIS: ^ this can be part of the ontology_attribute maybe?
                "answers": self._value,
                "featureHash": self.ontology_attribute.feature_node_hash,
                "manualAnnotation": self.is_manual_annotation,
            }

    def from_dict(self, d: Dict) -> None:
        if d["featureHash"] != self.ontology_attribute.feature_node_hash:
            raise ValueError("Cannot set the value of a TextAnswer based on a different ontology attribute.")

        self._answered = True
        self.set(d["answers"])
        self.is_manual_annotation = d["manualAnnotation"]

    def __hash__(self):
        return hash((self._value, type(self).__name__))


@dataclass
class RadioAnswer(_Answer):
    def __init__(self, ontology_attribute: RadioAttribute):
        super().__init__(ontology_attribute)
        self._value: Optional[NestableOption] = None

    def set(self, value: NestableOption):
        if not isinstance(value, NestableOption):
            raise ValueError("RadioAnswer can only be set to a NestableOption.")

        passed = False
        for child in self._ontology_attribute.options:
            if value.feature_node_hash == child.feature_node_hash:
                passed = True
        if not passed:
            raise ValueError(
                f"The supplied NestableOption `{value}` is not a child of the RadioAttribute that "
                f"is associated with this class: `{self._ontology_attribute}`"
            )
        self._answered = True
        self._value = value

    def get_value(self) -> Optional[NestableOption]:
        if not self.is_answered():
            return None
        else:
            return self._value

    def copy_from(self, radio_answer: RadioAnswer):
        if radio_answer.ontology_attribute.feature_node_hash != self.ontology_attribute.feature_node_hash:
            raise ValueError(
                "Copying from a RadioAnswer which is based on a different ontology Attribute is not possible."
            )
        other_is_answered = radio_answer.is_answered()
        if not other_is_answered:
            self.unset()
        else:
            other_answer = radio_answer.get_value()
            self.set(other_answer)

    def _to_encord_dict(self) -> Optional[Dict]:
        if not self.is_answered():
            return None
        else:
            nestable_option = self._value
            return {
                "name": self.ontology_attribute.name,
                "value": _lower_snake_case(self.ontology_attribute.name),
                # DENIS: ^ this can be part of the ontology_attribute maybe?
                "answers": [
                    {
                        "name": nestable_option.label,
                        "value": nestable_option.value,
                        "featureHash": nestable_option.feature_node_hash,
                    }
                ],
                "featureHash": self.ontology_attribute.feature_node_hash,
                "manualAnnotation": self.is_manual_annotation,
            }

    def from_dict(self, d: Dict) -> None:
        if d["featureHash"] != self.ontology_attribute.feature_node_hash:
            raise ValueError("Cannot set the value of a TextAnswer based on a different ontology attribute.")

        self._answered = True
        answers = d["answers"]
        if len(answers) != 1:
            raise ValueError("RadioAnswers must have exactly one answer.")

        answer = answers[0]
        nestable_option = _get_option_by_hash(answer["featureHash"], self.ontology_attribute.options)
        self.set(nestable_option)
        self.is_manual_annotation = d["manualAnnotation"]

    def __hash__(self):
        return hash((self._value, type(self).__name__))


@dataclass
class ChecklistAnswer(_Answer):
    """
    Checkboxes behave slightly different from the other answer types. When the checkbox is unanswered, it will be
    the equivalent of not having selected any checkbox answer in the Encord platform.
    The initial state will be every checkbox unchecked.
    """

    def __init__(self, ontology_attribute: ChecklistAttribute):
        super().__init__(ontology_attribute)
        self._ontology_options_feature_hashes: Set[str] = self._initialise_ontology_options_feature_hashes()
        self._feature_hash_to_answer_map: Dict[str, bool] = self._initialise_feature_hash_to_answer_map()

    def check_options(self, values: Iterable[FlatOption]):
        self._answered = True
        for value in values:
            self._verify_flat_option(value)
            self._feature_hash_to_answer_map[value.feature_node_hash] = True

    def uncheck_options(self, values: Iterable[FlatOption]):
        self._answered = True
        for value in values:
            self._verify_flat_option(value)
            self._feature_hash_to_answer_map[value.feature_node_hash] = False

    def set_options(self, values: Iterable[FlatOption]):
        for value in values:
            if not isinstance(value, FlatOption):
                raise ValueError("ChecklistAnswer can only be set to FlatOptions.")

        self._answered = True
        for key in self._feature_hash_to_answer_map.keys():
            self._feature_hash_to_answer_map[key] = False
        for value in values:
            self._verify_flat_option(value)
            self._feature_hash_to_answer_map[value.feature_node_hash] = True

    def get_options(self) -> List[FlatOption]:
        if not self.is_answered():
            return []
        else:
            return [
                option
                for option in self._ontology_attribute.options
                if self._feature_hash_to_answer_map[option.feature_node_hash]
            ]

    def get_value(self, value: FlatOption) -> bool:
        return self._feature_hash_to_answer_map[value.feature_node_hash]

    def copy_from(self, checklist_answer: ChecklistAnswer):
        if checklist_answer.ontology_attribute.feature_node_hash != self.ontology_attribute.feature_node_hash:
            raise ValueError(
                "Copying from a ChecklistAnswer which is based on a different ontology Attribute is not possible."
            )
        other_is_answered = checklist_answer.is_answered()
        if not other_is_answered:
            self.unset()
        else:
            self._answered = True
            for feature_node_hash in self._feature_hash_to_answer_map.keys():
                option = _get_option_by_hash(feature_node_hash, self.ontology_attribute.options)
                other_answer = checklist_answer.get_value(option)
                self._feature_hash_to_answer_map[feature_node_hash] = other_answer

    def _initialise_feature_hash_to_answer_map(self) -> Dict[str, bool]:
        ret: Dict[str, bool] = {}
        for child in self._ontology_attribute.options:
            ret[child.feature_node_hash] = False
        return ret

    def _initialise_ontology_options_feature_hashes(self) -> Set[str]:
        ret: Set[str] = set()
        for child in self._ontology_attribute.options:
            ret.add(child.feature_node_hash)
        return ret

    def _verify_flat_option(self, value: FlatOption) -> None:
        if value.feature_node_hash not in self._ontology_options_feature_hashes:
            raise RuntimeError(
                f"The supplied FlatOption `{value}` is not a child of the ChecklistAttribute that "
                f"is associated with this class: `{self._ontology_attribute}`"
            )

    def _to_encord_dict(self) -> Optional[Dict]:
        if not self.is_answered():
            return None
        else:
            checked_options = []
            ontology_attribute: ChecklistAttribute = self._ontology_attribute
            for option in ontology_attribute.options:
                if self.get_value(option):
                    checked_options.append(option)

            answers = []
            for option in checked_options:
                answers.append(
                    {
                        "name": option.label,
                        "value": option.value,
                        "featureHash": option.feature_node_hash,
                    }
                )
            return {
                "name": self.ontology_attribute.name,
                "value": _lower_snake_case(self.ontology_attribute.name),
                # DENIS: ^ this can be part of the ontology_attribute maybe?
                "answers": answers,
                "featureHash": self.ontology_attribute.feature_node_hash,
                "manualAnnotation": self.is_manual_annotation,
            }

    def from_dict(self, d: Dict) -> None:
        if d["featureHash"] != self.ontology_attribute.feature_node_hash:
            raise ValueError("Cannot set the value of a ChecklistAnswer based on a different ontology attribute.")

        answers = d["answers"]
        if len(answers) == 0:
            return

        for answer in answers:
            flat_option = _get_option_by_hash(answer["featureHash"], self.ontology_attribute.options)
            self.check_options([flat_option])

        self.is_manual_annotation = d["manualAnnotation"]
        self._answered = True

    def __hash__(self):
        flat_values = [(key, value) for key, value in self._feature_hash_to_answer_map.items()]
        flat_values.sort()
        return hash((tuple(flat_values), type(self).__name__))


Answer = Union[TextAnswer, RadioAnswer, ChecklistAnswer]
"""These ones are answers for dynamic and static things.
DENIS: call these `AttribureAnswer` here.
"""


class _DynamicAnswer:
    """
    A specialised view of the dynamic answers. Allows convenient interaction with the dynamic properties.
    """

    def __init__(self, parent: ObjectInstance, frame: int, attribute: Attribute):
        self._parent = parent
        self._frame = frame
        self._attribute = attribute

    @property
    def frame(self) -> int:
        return self._frame

    @frame.setter
    def frame(self, v: Any) -> NoReturn:
        raise RuntimeError("Cannot set the frame of an instantiated DynamicAnswer object.")

    def copy_to_frames(self, frames: Iterable[int]):
        current_answer = self._get_current_answer()

        for frame in frames:
            answer = self._parent._get_dynamic_answer(frame, self._attribute)
            self._parent._reset_dynamic_answer_at_frame(current_answer, answer, frame)

    def in_frames(self) -> Set[int]:
        current_answer = self._get_current_answer()
        return self._parent._get_frames_for_dynamic_answer(current_answer)

    def is_answered_for_current_frame(self) -> bool:
        current_answer = self._get_current_answer()
        return current_answer.is_answered()

    def _get_current_answer(self) -> Answer:
        """Get the current answer at the current frame from the parent."""
        answer = self._parent._get_dynamic_answer(self._frame, self._attribute)
        return answer


class DynamicTextAnswer(_DynamicAnswer):
    def __init__(self, parent: ObjectInstance, frame: int, attribute: Attribute):
        super().__init__(parent, frame, attribute)

    def set(self, value: str):

        current_answer = self._get_current_answer()
        new_answer = _get_default_answer_from_attribute(current_answer.ontology_attribute)
        new_answer.copy_from(current_answer)
        new_answer.set(value)

        self._parent._reset_dynamic_answer_at_frame(new_answer, current_answer, self._frame)

    def get_value(self) -> bool:
        current_answer = self._get_current_answer()
        return current_answer.get_value()


class DynamicRadioAnswer(_DynamicAnswer):
    def __init__(self, parent: ObjectInstance, frame: int, attribute: Attribute):
        super().__init__(parent, frame, attribute)

    def set(self, value: NestableOption):
        current_answer = self._get_current_answer()
        new_answer = _get_default_answer_from_attribute(current_answer.ontology_attribute)
        new_answer.copy_from(current_answer)
        new_answer.set(value)

        self._parent._reset_dynamic_answer_at_frame(new_answer, current_answer, self._frame)

    def get_value(self) -> Optional[NestableOption]:
        current_answer = self._get_current_answer()
        return current_answer.get_value()


class DynamicChecklistAnswer(_DynamicAnswer):
    def __init__(self, parent: ObjectInstance, frame: int, attribute: Attribute):
        super().__init__(parent, frame, attribute)

    def check_options(self, values: Iterable[FlatOption]) -> None:
        current_answer = self._get_current_answer()
        new_answer = _get_default_answer_from_attribute(current_answer.ontology_attribute)
        new_answer.copy_from(current_answer)
        new_answer.check_options(values)

        self._parent._reset_dynamic_answer_at_frame(new_answer, current_answer, self._frame)

    def uncheck_options(self, values: Iterable[FlatOption]) -> None:
        current_answer = self._get_current_answer()
        new_answer = _get_default_answer_from_attribute(current_answer.ontology_attribute)
        new_answer.copy_from(current_answer)
        new_answer.uncheck_options(values)

        self._parent._reset_dynamic_answer_at_frame(new_answer, current_answer, self._frame)

    def get_value(self, value: FlatOption) -> bool:
        # DENIS: maybe call this `is_checked(value)`
        current_answer = self._get_current_answer()
        return current_answer.get_value(value)


DynamicAnswer = Union[DynamicTextAnswer, DynamicChecklistAnswer]


def _get_default_answers_from_attributes(attributes: List[Attribute]) -> List[Answer]:
    """DENIS: I believe this only works for static answers."""
    ret: List[Answer] = list()
    for attribute in attributes:
        if not attribute.dynamic:
            answer = _get_default_answer_from_attribute(attribute)
            ret.append(answer)
        # DENIS: test the weird edge case of dynamic attributes which are nested.

        if attribute.has_options_field():
            for option in attribute.options:
                if option.get_option_type() == OptionType.NESTABLE:
                    other_attributes = _get_default_answers_from_attributes(option.nested_options)
                    ret.extend(other_attributes)

    return ret


def _get_default_answer_from_attribute(attribute: Attribute) -> Answer:
    property_type = attribute.get_property_type()
    if property_type == PropertyType.TEXT:
        return TextAnswer(attribute)
    elif property_type == PropertyType.RADIO:
        return RadioAnswer(attribute)
    elif property_type == PropertyType.CHECKLIST:
        return ChecklistAnswer(attribute)
    else:
        raise RuntimeError(f"Got an attribute with an unexpected property type: {attribute}")


@dataclass(frozen=True)
class BoundingBoxCoordinates:
    """All the values are percentages relative to the total image size."""

    height: float
    width: float
    top_left_x: float
    top_left_y: float

    @staticmethod
    def from_dict(d: dict) -> BoundingBoxCoordinates:
        """Get BoundingBoxCoordinates from an encord dict"""
        bounding_box_dict = d["boundingBox"]
        return BoundingBoxCoordinates(
            height=bounding_box_dict["h"],
            width=bounding_box_dict["w"],
            top_left_x=bounding_box_dict["x"],
            top_left_y=bounding_box_dict["y"],
        )

    def to_dict(self) -> dict:
        return {
            "h": self.height,
            "w": self.width,
            "x": self.top_left_x,
            "y": self.top_left_y,
        }


@dataclass(frozen=True)
class RotatableBoundingBoxCoordinates:
    """All the values are percentages relative to the total image size."""

    height: float
    width: float
    top_left_x: float
    top_left_y: float
    theta: float  # angle of rotation originating at center of box


@dataclass(frozen=True)
class PointCoordinate:
    """All coordinates are a percentage relative to the total image size."""

    x: float
    y: float


@dataclass(frozen=True)
class PolygonCoordinates:
    values: List[PointCoordinate]

    @staticmethod
    def from_dict(d: dict) -> PolygonCoordinates:
        polygon_dict = d["polygon"]
        values: List[PointCoordinate] = []

        sorted_dict_value_tuples = sorted((int(key), value) for key, value in polygon_dict.items())
        sorted_dict_values = [item[1] for item in sorted_dict_value_tuples]

        for value in sorted_dict_values:
            point_coordinate = PointCoordinate(
                x=value["x"],
                y=value["y"],
            )
            values.append(point_coordinate)

        return PolygonCoordinates(values=values)

    def to_dict(self) -> dict:
        ret = {}
        for idx, value in enumerate(self.values):
            ret[str(idx)] = {"x": value.x, "y": value.y}
        return ret


@dataclass(frozen=True)
class PolylineCoordinates:
    values: List[PointCoordinate]


class Visibility(Flag):
    """
    An item is invisible if it is outside the frame. It is occluded
    if it is covered by something in the frame, but it would otherwise
    be in the frame. Else it is visible.
    """

    VISIBLE = auto()
    INVISIBLE = auto()
    OCCLUDED = auto()


@dataclass(frozen=True)
class SkeletonCoordinate:
    x: float
    y: float

    # `name` and `color` can be removed as they are part of the ontology.
    # The frontend must first be aware of how to merge with ontology.
    name: str
    color: str

    # `featureHash` and `value` seem to appear when visibility is
    # present. They might not have any meaning. Remove if confirmed that
    # Frontend does not need it.
    feature_hash: Optional[str] = None
    value: Optional[str] = None

    visibility: Optional[Visibility] = None


@dataclass(frozen=True)
class SkeletonCoordinates:
    values: List[SkeletonCoordinate]


Coordinates = Union[
    BoundingBoxCoordinates,
    RotatableBoundingBoxCoordinates,
    PointCoordinate,
    PolygonCoordinates,
    PolylineCoordinates,
    SkeletonCoordinates,
]

# DENIS: guard this with a unit test.
ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS: Dict[Shape, Type[Coordinates]] = {
    Shape.BOUNDING_BOX: BoundingBoxCoordinates,
    Shape.ROTATABLE_BOUNDING_BOX: RotatableBoundingBoxCoordinates,
    Shape.POINT: PointCoordinate,
    Shape.POLYGON: PolygonCoordinates,
    Shape.POLYLINE: PolylineCoordinates,
    Shape.SKELETON: SkeletonCoordinates,
}


@dataclass(frozen=True)
class ObjectFrameReadOnlyInstanceInfo:
    """Trying to set this will not have any effects on the data in the Encord servers."""

    reviews: List[dict] = field(default_factory=list)
    # DENIS: can I type out this reviews thing?


@dataclass(frozen=True)
class ObjectFrameInstanceInfo:
    # DENIS: do we need the isDeleted field?
    created_at: datetime = datetime.now()
    created_by: Optional[str] = None
    """None defaults to the user of the SDK. DENIS: need to add this information somewhere."""
    last_edited_at: Optional[datetime] = None
    last_edited_by: Optional[str] = None
    """None defaults to the user of the SDK, DENIS: do we want this to be true for last_edited_by?"""
    confidence: float = 1
    manual_annotation: bool = True
    read_only_info: ObjectFrameReadOnlyInstanceInfo = ObjectFrameReadOnlyInstanceInfo()

    @staticmethod
    def from_dict(d: dict):
        read_only_info = ObjectFrameReadOnlyInstanceInfo(reviews=d["reviews"])
        if "lastEditedAt" in d:
            last_edited_at = parse(d["lastEditedAt"])
        else:
            last_edited_at = None

        return ObjectFrameInstanceInfo(
            created_at=parse(d["createdAt"]),
            created_by=d["createdBy"],
            last_edited_at=last_edited_at,
            last_edited_by=d.get("lastEditedBy"),
            confidence=d["confidence"],
            manual_annotation=d["manualAnnotation"],
            read_only_info=read_only_info,
        )


@dataclass(frozen=True)
class ObjectFrameInstanceData:
    coordinates: Coordinates
    object_frame_instance_info: ObjectFrameInstanceInfo


@dataclass
class AnswerForFrames:
    answer: Union[str, Option, Iterable[Option]]
    range: Set[int]  # either [1, 3, 4, 5] or [[1], [3,5]]
    # DENIS: change this to a list of `Frames`.


class _DynamicAnswerManager:
    def __init__(self, object_instance: ObjectInstance):
        """
        Manages the answers that are set for different frames.
        This can be part of the ObjectInstance class.
        """
        self._object_instance = object_instance
        # self._ontology_object = ontology_object
        self._frames_to_answers: Dict[int, Set[Answer]] = defaultdict(set)
        self._answers_to_frames: Dict[Answer, Set[int]] = defaultdict(set)

        self._dynamic_uninitialised_answer_options: Set[Answer] = self._get_dynamic_answers()
        # ^ these are like the static answers. Everything that is possibly an answer. However,
        # don't forget also nested-ness. In this case nested-ness should be ignored.
        # ^ I might not need this object but only need the _get_dynamic_answers object.

    def is_valid_dynamic_attribute(self, attribute: Attribute) -> bool:
        feature_node_hash = attribute.feature_node_hash

        for answer in self._dynamic_uninitialised_answer_options:
            if answer.ontology_attribute.feature_node_hash == feature_node_hash:
                return True
        return False

    def remove_answer(self, attribute: Attribute, frame: int) -> None:
        to_remove_answer = None

        for answer_object in self._frames_to_answers[frame]:
            # DENIS: ideally this would not be a log(n) operation, however these will not be extremely large.
            if answer_object.ontology_attribute == attribute:
                to_remove_answer = answer_object
                break

        if to_remove_answer is not None:
            self._frames_to_answers[frame].remove(to_remove_answer)
            self._answers_to_frames[to_remove_answer].remove(frame)
            if self._answers_to_frames[to_remove_answer] == set():
                del self._answers_to_frames[to_remove_answer]

    def set_answer(self, answer: Union[str, Option, Iterable[Option]], attribute: Attribute, frame: int) -> None:
        """DENIS: default the frames to all the frames in the object instance."""

        self.remove_answer(attribute, frame)

        default_answer = _get_default_answer_from_attribute(attribute)
        _set_answer_for_object(default_answer, answer)

        # DENIS: change this to handle type `Frames`.
        self._frames_to_answers[frame].add(default_answer)
        self._answers_to_frames[default_answer].add(frame)

    def get_answer(
        self,
        attribute: Attribute,
        answer: Union[str, Option, Iterable[Option], None] = None,
        frame: Optional[int] = None,
    ) -> List[AnswerForFrames]:
        """For a given attribute, return all the answers and frames given the filters."""
        if answer is None and frame is None:
            return self._get_all_answers_for_attribute(attribute)
        else:
            raise NotImplementedError("This is not implemented yet.")
        default_answer = _get_default_answer_from_attribute(attribute)
        _set_answer_for_object(default_answer, answer)

    def _get_all_answers_for_attribute(self, attribute: Attribute) -> List[AnswerForFrames]:
        """Return all the answers for a given attribute."""
        ret = []
        all_answers = [answer for answer in self._answers_to_frames if answer.ontology_attribute == attribute]
        for answer in all_answers:
            ret.append(AnswerForFrames(answer=_get_answer_from_object(answer), range=self._answers_to_frames[answer]))
        return ret

    def _get_dynamic_answers(self) -> Set[Answer]:
        ret: Set[Answer] = set()
        for attribute in self._object_instance.ontology_item.attributes:
            if attribute.dynamic:
                answer = _get_default_answer_from_attribute(attribute)
                ret.add(answer)
        return ret


class ObjectInstance:
    """This is per video/image_group/dicom/...

    should you be able to set the color per object?

    DENIS: I probably want to have a proper __repr__ here for debug-ability.
    """

    # DENIS: this needs to take an OntologyLabelObject to navigate around.
    def __init__(self, ontology_object: Object, *, object_hash: Optional[str] = None):
        self._ontology_object = ontology_object
        self._frames_to_instance_data: Dict[int, ObjectFrameInstanceData] = dict()
        # DENIS: do I need to make tests for memory requirements? As in, how much more memory does
        # this thing take over the label structure itself (for large ones it would be interesting)
        self._object_hash = object_hash or short_uuid_str()
        self._parent: Optional[LabelRow] = None
        """This member should only be manipulated by a LabelRow"""

        # self._static_answers: List[Answer] = self._get_static_answers()
        self._static_answer_map: Dict[str, Answer] = _get_static_answer_map(self._ontology_object.attributes)
        # feature_node_hash of attribute to the answer.

        self._dynamic_answer_manager = _DynamicAnswerManager(self)

        # self._frames_to_answers: Dict[int, Set[Answer]] = defaultdict(set)
        # self._answers_to_frames: Dict[Answer, Set[int]] = defaultdict(set)
        # # ^ for dynamic answer management => DENIS: may be better to have a manager class with the
        # # responsibility to manage this
        #
        # self._dynamic_uninitialised_answer_options: Set[Answer] = self._get_dynamic_answers()
        # # ^ read only for dynamic answers management.

    # def _get_dynamic_answer(self, frame: int, attribute: Attribute) -> Answer:
    #     """This should only be called from the DynamicAnswer"""
    #     answers = self._frames_to_answers[frame]
    #     for answer in answers:
    #         if answer.ontology_attribute.feature_node_hash == attribute.feature_node_hash:
    #             return answer
    #
    #     raise RuntimeError("The attribute is not a valid attribute for this ObjectInstance.")

    # def _get_frames_for_dynamic_answer(self, answer: Answer) -> Set[int]:
    #     return self._answers_to_frames[answer]
    #
    # def _set_dynamic_answer_to_frames(self, frames: Iterable[int], answer: Answer) -> None:
    #     self._answers_to_frames[answer].update(set(frames))
    #     for frame in frames:
    #         self._frames_to_answers[frame].add(answer)

    @overload
    def get_answer(self, attribute: TextAttribute) -> Optional[str]:
        ...

    @overload
    def get_answer(self, attribute: RadioAttribute) -> Optional[Option]:
        ...

    @overload
    def get_answer(self, attribute: ChecklistAttribute) -> Optional[List[Option]]:
        """Returns None only if the attribute is nested and the parent is unselected. Otherwise, if not
        yet answered it will return an empty list."""
        ...

    def get_answer(
        self,
        attribute: Attribute,
        answer: Union[str, Option, Iterable[Option], None] = None,
        frame: Optional[int] = None,
    ) -> Union[str, Option, Iterable[Option], None]:
        """
        Args:
            attribute: The ontology attribute to get the answer for.
            answer: A filter for a specific answer value. Only applies to dynamic attributes.
            frame: A filter for a specific frame. Only applies to dynamic attributes.
            DENIS: overthink the return type. Dynamic answers would have a different return type.
        """
        if attribute is None:
            attribute = self._ontology_object.attributes[0]
        elif not self._is_attribute_valid_child_of_object_instance(attribute):
            raise ValueError("The attribute is not a valid child of the classification.")
        elif not self._is_selectable_child_attribute(attribute):
            return None

        if attribute.dynamic:
            return self._dynamic_answer_manager.get_answer(attribute, answer, frame)

        static_answer = self._static_answer_map[attribute.feature_node_hash]

        return _get_answer_from_object(static_answer)

    @overload
    def set_answer(
        self,
        answer: str,
        attribute: TextAttribute,
        frames: Optional[Frames] = None,
        overwrite: bool = False,
    ) -> None:
        ...

    @overload
    def set_answer(
        self,
        answer: Option,
        attribute: RadioAttribute,
        frames: Optional[Frames] = None,
        overwrite: bool = False,
    ) -> None:
        ...

    @overload
    def set_answer(
        self,
        answer: Iterable[Option],
        attribute: ChecklistAttribute,
        frames: Optional[Frames] = None,
        overwrite: bool = False,
    ) -> None:
        ...

    def set_answer(
        self,
        answer: Union[str, Option, Iterable[Option]],
        attribute: Attribute,
        frames: Optional[Frames] = None,
        overwrite: bool = False,
    ) -> None:
        """
        We could make these functions part of a different class which this inherits from.

        Args:
            answer: The answer to set.
            attribute: The ontology attribute to set the answer for. If not provided, the first level attribute is used.
            frames: Only relevant for dynamic attributes. The frames to set the answer for. If not provided, the
                answer is set for all frames. If this is anything but `None` for non-dynamic attributes, this will
                throw a ValueError.
            overwrite: If `True`, the answer will be overwritten if it already exists. If `False`, this will throw
                a RuntimeError if the answer already exists. This argument is ignored for dynamic attributes.
        """
        if not self._is_attribute_valid_child_of_object_instance(attribute):
            raise ValueError("The attribute is not a valid child of the object.")
        elif not self._is_selectable_child_attribute(attribute):
            raise RuntimeError(
                "Setting a nested attribute is only possible if all parent attributes have been" "selected."
            )
        elif frames is not None and attribute.dynamic is False:
            raise ValueError("Setting frames is only possible for dynamic attributes.")

        """
        For classification index we get all the possible static answers upfront and then iterate over those.
        Here I could do the same thing for static answers
        for dynamic ones I can
        * extend the answers so they can have multiple answers and a range
        * create a new class which is a manager for one/all of the dynamic answers.  <-- try this
        * or manage them here somewhere.
        Essentially all these things are the same actually, I'm only talking about the levels of abstraction. 
        """

        if attribute.dynamic:
            # DENIS: do I want to do an overwrite?
            self._dynamic_answer_manager.set_answer(answer, attribute, frames)
            return

        # DENIS: I can factor this out with the ClassificationIndex class.
        static_answer = self._static_answer_map[attribute.feature_node_hash]
        if static_answer.is_answered() and overwrite is False:
            raise RuntimeError(
                "The answer to this attribute was already set. Set `overwrite` to `True` if you want to"
                "overwrite an existing answer to and attribute."
            )

        _set_answer_for_object(static_answer, answer)

    def _is_attribute_valid_child_of_object_instance(self, attribute: Attribute) -> bool:
        # DENIS: this will fail for dynamic attributes.
        is_static_child = attribute.feature_node_hash in self._static_answer_map
        is_dynamic_child = self._dynamic_answer_manager.is_valid_dynamic_attribute(attribute)
        return is_dynamic_child or is_static_child

    # def get_all_static_answers(
    #     self,
    # ) -> List[Answer]:
    #     ret = copy(self._static_answers)
    #     # Deliberately always returning a shallow copy to make sure no one removes the static answers.
    #     return ret

    # def get_static_answer(self, attribute: Attribute) -> Answer:
    #     # DENIS: can I be smarter about the return type according to the incoming type?
    #     for static_answer in self._static_answers:
    #         if attribute.feature_node_hash == static_answer.ontology_attribute.feature_node_hash:
    #             return static_answer
    #     raise ValueError("The attribute was not found in this ObjectInstance's ontology.")

    # def _get_dynamic_answers(self) -> Set[Answer]:
    #     ret: Set[Answer] = set()
    #     for attribute in self._ontology_object.attributes:
    #         if attribute.dynamic:
    #             answer = _get_default_answer_from_attribute(attribute)
    #             ret.add(answer)
    #     return ret

    # def get_dynamic_answer(self, frame: int, attribute: Attribute):
    #     # DENIS: probably I don't need two classes
    #     answer = self._get_dynamic_answer(frame, attribute)
    #     if isinstance(answer, TextAnswer):
    #         return DynamicTextAnswer(self, frame, answer.ontology_attribute)
    #     elif isinstance(answer, ChecklistAnswer):
    #         return DynamicChecklistAnswer(self, frame, answer.ontology_attribute)
    #     elif isinstance(answer, RadioAnswer):
    #         return DynamicRadioAnswer(self, frame, answer.ontology_attribute)
    #     else:
    #         raise NotImplemented("Need to implement the other answer types")

    @property
    def object_hash(self) -> str:
        return self._object_hash

    @object_hash.setter
    def object_hash(self, v: Any) -> NoReturn:
        raise RuntimeError("Cannot set the object hash on an instantiated label object.")

    @property
    def ontology_item(self) -> Any:
        return deepcopy(self._ontology_object)

    @ontology_item.setter
    def ontology_item(self, v: Any) -> NoReturn:
        raise RuntimeError("Cannot set the ontology item of an instantiated ObjectInstance.")

    def set_coordinates(
        # DENIS: should this be called `set_instance_data` or something similar?
        self,
        coordinates: Coordinates,
        frames: Iterable[int],
        # ^ DENIS: this is slightly awkward, do we really need to have multiple?
        *,
        object_frame_instance_info: ObjectFrameInstanceInfo = ObjectFrameInstanceInfo(),
        # DENIS: could have a set/overwrite/force flag
    ):
        """
        DENIS: The client needs to be careful here! If a reference of multiple coordinates is being passed around, they
        might accidentally overwrite specific values.

        DENIS: validate that the coordinates are not out of bounds.
        """
        expected_coordinate_type = ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS[self._ontology_object.shape]
        if type(coordinates) != expected_coordinate_type:
            raise ValueError(
                f"Expected a coordinate of type `{expected_coordinate_type}`, but got type `{type(coordinates)}`."
            )

        for frame in frames:
            self._frames_to_instance_data[frame] = ObjectFrameInstanceData(
                coordinates=coordinates, object_frame_instance_info=object_frame_instance_info
            )
            # self._add_initial_dynamic_answers(frame)

        if self._parent:
            self._parent._add_to_frame_to_hashes_map(self)

    def get_for_frame(self, frame: int) -> ObjectFrameInstanceData:
        saved_data = self._frames_to_instance_data[frame]
        return ObjectFrameInstanceData(
            coordinates=deepcopy(saved_data.coordinates),
            object_frame_instance_info=saved_data.object_frame_instance_info,
        )

    # def _add_initial_dynamic_answers(self, frame: int) -> None:
    #     if frame in self._frames_to_answers:
    #         return
    #
    #     for answer in self._dynamic_uninitialised_answer_options:
    #         self._frames_to_answers[frame].add(answer)
    #         self._answers_to_frames[answer].add(frame)

    def copy(self) -> ObjectInstance:
        """
        Creates an exact copy of this ObjectInstance but with a new object hash and without being associated to any
        LabelRow. This is useful if you want to add the semantically same ObjectInstance to multiple `LabelRow`s."""
        ret = ObjectInstance(self._ontology_object)
        ret._frames_to_instance_data = copy(self._frames_to_instance_data)
        # DENIS: test if a shallow copy is enough
        # DENIS: copy the answers stuff as well.
        return ret

    def frames(self) -> List[int]:
        # DENIS: this is public - think about if I want to have a condensed version with a run length encoding.
        return list(self._frames_to_instance_data.keys())

    def get_instance_data(self, frames: Iterable[int]) -> List[ObjectFrameInstanceData]:
        ret = []
        for frame in frames:
            if frame not in self._frames_to_instance_data:
                raise ValueError(f"This object does not exist on frame `{frame}`.")
            ret.append(self._frames_to_instance_data[frame])
        return ret

    def remove_from_frames(self, frames: Iterable[int]):
        """Ensure that it will be removed from all frames."""
        # DENIS: probably frames everywhere should be Union[Iterable[int], int]
        for frame in frames:
            self._frames_to_instance_data.pop(frame)
            # self._remove_dynamic_answers_from_frame(frame)

        if self._parent:
            self._parent._remove_from_frame_to_hashes_map(frames, self.object_hash)

        # DENIS: can we remove to make this invalid?
        # DENIS: ensure that dynamic answers are also handled properly.

    # def _remove_dynamic_answers_from_frame(self, frame: int) -> None:
    #     answers = self._frames_to_answers[frame]
    #     for answer in answers:
    #         self._remove_dynamic_answer_at_frame(answer, frame)
    #
    #     self._frames_to_answers.pop(frame)
    #
    # def _remove_dynamic_answer_at_frame(self, answer: Answer, frame: int) -> None:
    #     default_answer = _get_default_answer_from_attribute(answer.ontology_attribute)
    #
    #     if hash(answer) == hash(default_answer):
    #         return
    #
    #     self._answers_to_frames[answer].remove(frame)
    #     if len(self._answers_to_frames) == 0:
    #         self._answers_to_frames.pop(answer)
    #
    #     self._frames_to_answers[frame].remove(answer)
    #     self._frames_to_answers[frame].add(default_answer)
    #
    # def _reset_dynamic_answer_at_frame(self, new_answer: Answer, old_answer: Answer, frame: int) -> None:
    #     self._answers_to_frames[old_answer].remove(frame)
    #     self._frames_to_answers[frame].remove(old_answer)
    #
    #     self._answers_to_frames[new_answer].add(frame)
    #     self._frames_to_answers[frame].add(new_answer)

    def is_valid(self) -> bool:
        """Check if is valid, could also return some human/computer  messages."""
        if len(self._frames_to_instance_data) == 0:
            return False
        return True

    def _is_selectable_child_attribute(self, attribute: Attribute) -> bool:
        # I have the ontology classification, so I can build the tree from that. Basically do a DFS.
        ontology_object = self._ontology_object
        for search_attribute in ontology_object.attributes:
            if _search_child_attributes(attribute, search_attribute, self._static_answer_map):
                return True
        return False


@dataclass(frozen=True)
class ClassificationInstanceData:
    created_at: datetime = datetime.now()
    created_by: str = None
    confidence: int = DEFAULT_CONFIDENCE
    manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION
    # DENIS: last_edited_at, last_edited_by
    reviews: List[dict] = field(default_factory=list)  # DENIS this is some sort of "read only data"

    @staticmethod
    def from_dict(d: dict) -> ClassificationInstanceData:
        return ClassificationInstanceData(
            created_at=parse(d["createdAt"]),
            created_by=d["createdBy"],
            confidence=d["confidence"],
            manual_annotation=d["manualAnnotation"],
            reviews=d["reviews"],
        )


class ClassificationInstance:
    def __init__(self, ontology_classification: Classification, *, classification_hash: Optional[str] = None):
        # DENIS: should I also be able to accept the first level attribute? Ideally not, as
        # I'd need to awkwardly verify whether this is the first level attribute or not.
        self._ontology_classification = ontology_classification
        self._parent: Optional[LabelRow] = None
        self._classification_hash = classification_hash or short_uuid_str()
        self._classification_instance_data = ClassificationInstanceData()
        # DENIS: These are actually somehow per frame! What would that even mean? check this!

        self._static_answer_map: Dict[str, Answer] = _get_static_answer_map(self._ontology_classification.attributes)
        # feature_node_hash of attribute to the answer.

        self._frames: Set[int] = set()
        # DENIS: Ideally there would be a max range check.
        self._max_frame: int = float("inf")

    @property
    def classification_hash(self) -> str:
        return self._classification_hash

    @classification_hash.setter
    def classification_hash(self, v: Any) -> NoReturn:
        raise RuntimeError("Cannot set the object hash on an instantiated label object.")

    def set_classification_instance_data(self, classification_instance_data) -> None:
        self._classification_instance_data = classification_instance_data

    def get_classification_instance_data(self) -> ClassificationInstanceData:
        # DENIS: the naming is definitely confusing.
        # DENIS: this also needs to have a proper setter
        return self._classification_instance_data

    @property
    def ontology_item(self) -> Classification:
        return deepcopy(self._ontology_classification)

    @ontology_item.setter
    def ontology_item(self, v: Any) -> NoReturn:
        raise RuntimeError("Cannot set the ontology item of an instantiated ObjectInstance.")

    def set_frames(self, frames: Iterable[int]) -> None:
        """Overwrites the current frames."""
        new_frames = set()
        self._check_classification_already_present(frames)
        for frame in frames:
            self._check_within_range(frame)
            new_frames.add(frame)
        self._frames = new_frames

    def add_to_frames(
        self,
        frames: Iterable[int],
    ) -> None:
        self._check_classification_already_present(frames)
        for frame in frames:
            self._check_within_range(frame)
            self._frames.add(frame)
            if self._parent is not None:
                self._parent._add_to_frame_to_hashes_map(self)

    def remove_from_frames(self, frames: Iterable[int]) -> None:
        for frame in frames:
            self._frames.remove(frame)

        if self._parent is not None:
            self._parent._remove_frames_from_classification(self.ontology_item, frames)
            self._parent._remove_from_frame_to_hashes_map(frames, self.classification_hash)

    def frames(self) -> List[int]:
        return list(self._frames)

    # def get_static_answer(self) -> Answer:
    #     return self._static_answer

    def is_valid(self) -> bool:
        return len(self._frames) > 0

    @overload
    def set_answer(self, answer: str, attribute: TextAttribute) -> None:
        ...

    @overload
    def set_answer(self, answer: Option, attribute: RadioAttribute, overwrite: bool = False) -> None:
        ...

    @overload
    def set_answer(self, answer: Iterable[Option], attribute: ChecklistAttribute, overwrite: bool = False) -> None:
        ...

    @overload
    def set_answer(
        self, answer: Union[str, Option, Iterable[Option]], attribute: None = None, overwrite: bool = False
    ) -> None:
        ...

    def set_answer(
        self,
        answer: Union[str, Option, Iterable[Option]],
        attribute: Optional[Attribute] = None,
        overwrite: bool = False,
    ) -> None:
        """
        We could make these functions part of a different class which this inherits from.

        Args:
            answer: The answer to set.
            attribute: The ontology attribute to set the answer for. If not provided, the first level attribute is used.
            overwrite: If `True`, the answer will be overwritten if it already exists. If `False`, this will throw
                a RuntimeError if the answer already exists.
        """
        if attribute is None:
            attribute = self._ontology_classification.attributes[0]
        elif not self._is_attribute_valid_child_of_classification(attribute):
            raise ValueError("The attribute is not a valid child of the classification.")
        elif not self._is_selectable_child_attribute(attribute):
            raise RuntimeError(
                "Setting a nested attribute is only possible if all parent attributes have been" "selected."
            )

        static_answer = self._static_answer_map[attribute.feature_node_hash]
        if static_answer.is_answered() and overwrite is False:
            raise RuntimeError(
                "The answer to this attribute was already set. Set `overwrite` to `True` if you want to"
                "overwrite an existing answer to and attribute."
            )

        _set_answer_for_object(static_answer, answer)

    @overload
    def get_answer(self, attribute: TextAttribute) -> str:
        ...

    @overload
    def get_answer(self, attribute: RadioAttribute) -> Option:
        ...

    @overload
    def get_answer(self, attribute: ChecklistAttribute) -> List[Option]:
        ...

    @overload
    def get_answer(self, attribute: None = None) -> Union[str, Option, List[Option]]:
        ...

    def get_answer(self, attribute: Optional[Attribute] = None) -> Union[str, Option, Iterable[Option], None]:
        """
        Args:
            attribute: The ontology attribute to get the answer for. If not provided, the first level attribute is used.
        """
        if attribute is None:
            attribute = self._ontology_classification.attributes[0]
        elif not self._is_attribute_valid_child_of_classification(attribute):
            raise ValueError("The attribute is not a valid child of the classification.")
        elif not self._is_selectable_child_attribute(attribute):
            return None

        static_answer = self._static_answer_map[attribute.feature_node_hash]

        return _get_answer_from_object(static_answer)

    def _is_attribute_valid_child_of_classification(self, attribute: Attribute) -> bool:
        return attribute.feature_node_hash in self._static_answer_map

    def _is_selectable_child_attribute(self, attribute: Attribute) -> bool:
        # I have the ontology classification, so I can build the tree from that. Basically do a DFS.
        ontology_classification = self._ontology_classification
        top_attribute = ontology_classification.attributes[0]
        return _search_child_attributes(attribute, top_attribute, self._static_answer_map)

    def _check_within_range(self, frame: int) -> None:
        if frame < 0 or frame > self._max_frame:
            raise ValueError(
                f"The supplied frame of `{frame}` is not within the acceptable bounds of `0` to `{self._max_frame}`."
            )

    def _check_classification_already_present(self, frames: Iterable[int]) -> None:
        if self._parent is None:
            return
        already_present_frame = self._parent._is_classification_already_present(self.ontology_item, frames)
        if already_present_frame is not None:
            raise ValueError(
                f"The LabelRow, that this classification is part of, already has a classification of the same type "
                f"on frame `{already_present_frame}`. The same type of classification can only be present once per "
                f"frame per LabelRow."
            )


@dataclass(frozen=True)
class FrameLevelImageGroupData:
    # DENIS: check which ones here are optional. Can even branch off of different DataType of the LabelRow
    # This is for now for image groups
    image_hash: str
    image_title: str
    data_link: str
    file_type: str
    frame_number: int
    width: int
    height: int


@dataclass(frozen=True)
class LabelRowReadOnlyData:
    label_hash: str
    dataset_hash: str
    dataset_title: str
    data_title: str
    data_type: DataType
    label_status: str  # actually some sort of enum
    number_of_frames: int
    frame_level_data: Dict[int, FrameLevelImageGroupData]  # DENIS: this could be an array too.
    image_hash_to_frame: Dict[str, int] = field(default_factory=dict)
    frame_to_image_hash: Dict[int, str] = field(default_factory=dict)


class LabelRow:
    """
    will also need to be able to keep around possible coordinate sizes and also query those if necessary.

    This is essentially one blob of data_units. For an image_group we need to get all the hashed in.
    """

    def __init__(self, label_row_dict: dict, ontology_structure: Union[dict, OntologyStructure]) -> None:
        if isinstance(ontology_structure, dict):
            self._ontology_structure = OntologyStructure.from_dict(ontology_structure)
        else:
            self._ontology_structure = ontology_structure

        self._label_row_read_only_data: LabelRowReadOnlyData = self._parse_label_row_dict(label_row_dict)
        # DENIS: ^ this should probably be protected so no one resets it.

        # DENIS: next up need to also parse objects and classifications from current label rows.

        self._frame_to_hashes: defaultdict[int, Set[str]] = defaultdict(set)
        # ^ frames to object and classification hashes

        self._classifications_to_frames: defaultdict[Classification, Set[int]] = defaultdict(set)

        self._objects_map: Dict[str, ObjectInstance] = dict()
        self._classifications_map: Dict[str, ClassificationInstance] = dict()
        # ^ conveniently a dict is ordered in Python. Use this to our advantage to keep the labels in order
        # at least at the final objects_index/classifications_index level.
        # DENIS: actually if I have a hash function of ObjectInstance, this doesn't have to be a map, however the ordering
        # property would be lost.
        self._parse_objects_map(label_row_dict)
        self._parse_classifications_map(label_row_dict)

    def get_image_hash(self, frame_number: int) -> str:
        # DENIS: to do
        return "xyz"

    def get_frame_number(self, image_hash: str) -> int:
        # DENIS: to do
        return 5

    @property
    def label_row_read_only_data(self) -> LabelRowReadOnlyData:
        return self._label_row_read_only_data

    @label_row_read_only_data.setter
    def label_row_read_only_data(self, v: Any) -> NoReturn:
        raise RuntimeError("Cannot overwrite the read only data.")

    def upload(self):
        """Do the client request"""
        # Can probably just use the set label row here.
        pass

    def to_encord_dict(self) -> dict:
        """
        Client should never need to use this, but they can.

        I think on download it is important to cache whatever we have, because of all the additional data.
        Or the read only data actually already has all of the information anyways, and we parse it back
        and forth every single time.
        """
        ret = {}
        read_only_data = self.label_row_read_only_data

        ret["label_hash"] = read_only_data.label_hash
        ret["dataset_hash"] = read_only_data.dataset_hash
        ret["dataset_title"] = read_only_data.dataset_title
        ret["data_title"] = read_only_data.data_title
        ret["data_type"] = read_only_data.data_type.value
        ret["object_answers"] = self._to_object_answers()
        ret["classification_answers"] = self._to_classification_answers()
        ret["object_actions"] = dict()  # TODO:
        ret["label_status"] = read_only_data.label_status
        ret["data_units"] = self._to_encord_data_units()

        return ret

    def _to_object_answers(self) -> dict:
        ret = {}
        for obj in self._objects_map.values():
            all_static_answers = self._get_all_static_answers(obj)
            ret[obj.object_hash] = {
                "classifications": all_static_answers,
                "objectHash": obj.object_hash,
            }
        return ret

    def _to_classification_answers(self) -> dict:
        ret = {}
        for classification in self._classifications_map.values():
            static_answer = classification.get_static_answer()
            d_opt = static_answer._to_encord_dict()
            classifications = [] if d_opt is None else [d_opt]
            ret[classification.classification_hash] = {
                "classifications": classifications,
                "classificationHash": classification.classification_hash,
            }
        return ret

    @staticmethod
    def _get_all_static_answers(item: Union[ObjectInstance, ClassificationInstance]) -> List[dict]:
        ret = []
        for answer in item.get_all_static_answers():
            d_opt = answer._to_encord_dict()
            if d_opt is not None:
                ret.append(d_opt)
        return ret

    def _to_encord_data_units(self) -> dict:
        # DENIS: assume an image group for now
        ret = {}
        frame_level_data = self.label_row_read_only_data.frame_level_data
        for value in frame_level_data.values():
            ret[value.image_hash] = self._to_encord_data_unit(value)

        return ret

    def _to_encord_data_unit(self, frame_level_data: FrameLevelImageGroupData) -> dict:
        ret = {}

        ret["data_hash"] = frame_level_data.image_hash
        ret["data_title"] = frame_level_data.image_title
        ret["data_link"] = frame_level_data.data_link
        ret["data_type"] = frame_level_data.file_type
        ret["data_sequence"] = str(frame_level_data.frame_number)
        ret["width"] = frame_level_data.width
        ret["height"] = frame_level_data.height
        ret["labels"] = self._to_encord_label(frame_level_data.frame_number)

        return ret

    def _to_encord_label(self, frame: int) -> dict:
        ret = {}

        # TODO:
        ret["objects"] = self._to_encord_objects_list(frame)
        ret["classifications"] = self._to_encord_classifications_list(frame)

        return ret

    def _to_encord_objects_list(self, frame: int) -> list:
        # Get objects for frame
        ret: List[dict] = []

        objects = self.get_objects_by_frame([frame])
        for object_ in objects:
            encord_object = self._to_encord_object(object_, frame)
            ret.append(encord_object)
        return ret

    def _to_encord_object(
        self,
        object_: ObjectInstance,
        frame: int,
    ) -> dict:
        ret = {}

        object_frame_instance_data = object_.get_for_frame(frame)
        object_frame_instance_info = object_frame_instance_data.object_frame_instance_info
        coordinates = object_frame_instance_data.coordinates
        ontology_hash = object_.ontology_item.feature_node_hash
        ontology_object = get_item_by_hash(ontology_hash, self._ontology_structure)

        ret["name"] = ontology_object.name
        ret["color"] = ontology_object.color
        ret["shape"] = ontology_object.shape.value
        ret["value"] = _lower_snake_case(ontology_object.name)
        ret["createdAt"] = object_frame_instance_info.created_at.strftime(DATETIME_LONG_STRING_FORMAT)
        ret["createdBy"] = object_frame_instance_info.created_by or "denis@cord.tech"  # DENIS: fix
        ret["confidence"] = object_frame_instance_info.confidence
        ret["objectHash"] = object_.object_hash
        ret["featureHash"] = ontology_object.feature_node_hash
        ret["manualAnnotation"] = object_frame_instance_info.manual_annotation

        if object_frame_instance_info.last_edited_at is not None:
            ret["lastEditedAt"] = object_frame_instance_info.last_edited_at.strftime(DATETIME_LONG_STRING_FORMAT)
        if object_frame_instance_info.last_edited_by is not None:
            ret["lastEditedBy"] = object_frame_instance_info.last_edited_by

        self._add_coordinates_to_encord_object(coordinates, ret)

        return ret

    def _add_coordinates_to_encord_object(self, coordinates: Coordinates, encord_object: dict) -> None:
        if isinstance(coordinates, BoundingBoxCoordinates):
            encord_object["boundingBox"] = coordinates.to_dict()
        elif isinstance(coordinates, PolygonCoordinates):
            encord_object["polygon"] = coordinates.to_dict()
        else:
            NotImplementedError(f"adding coordinatees for this type not yet implemented {type(coordinates)}")

    def _to_encord_classifications_list(self, frame: int) -> list:
        ret: List[dict] = []

        classifications = self.get_classifications_by_frame([frame])
        for classification in classifications:
            encord_classification = self._to_encord_classification(classification, frame)
            ret.append(encord_classification)

        return ret

    def _to_encord_classification(self, classification: ClassificationInstance, frame: int) -> dict:
        ret = {}

        classification_instance_data = classification.get_classification_instance_data()
        classification_feature_hash = classification.ontology_item.feature_node_hash
        ontology_classification = get_item_by_hash(classification_feature_hash, self._ontology_structure)
        attribute_hash = classification.ontology_item.attributes[0].feature_node_hash
        ontology_attribute = get_item_by_hash(attribute_hash, self._ontology_structure)

        ret["name"] = ontology_attribute.name
        ret["value"] = _lower_snake_case(ontology_attribute.name)
        ret["createdAt"] = classification_instance_data.created_at.strftime(DATETIME_LONG_STRING_FORMAT)
        ret["createdBy"] = classification_instance_data.created_by
        ret["confidence"] = classification_instance_data.confidence
        ret["featureHash"] = ontology_classification.feature_node_hash
        ret["classificationHash"] = classification.classification_hash
        ret["manualAnnotation"] = classification_instance_data.manual_annotation

        # if classification_instance_data.last_edited_at is not None:
        #     ret["lastEditedAt"] = classification_instance_data.last_edited_at.strftime(DATETIME_LONG_STRING_FORMAT)
        # if classification_instance_data.last_edited_by is not None:
        #     ret["lastEditedBy"] = classification_instance_data.last_edited_by

        return ret

    def refresh(self, *, get_signed_urls: bool = False, force: bool = False) -> bool:
        """
        Grab the labels from the server. Return False if the labels have been changed in the meantime.

        Args:
            force:
                If `False`, it will not do the refresh if something has changed on the server.
                If `True`, it will always overwrite the local changes with what has happened on the server.
        """
        # Actually can probably use the get_label_row() here.

    def get_objects(self, ontology_object: Optional[Object] = None) -> List[ObjectInstance]:
        """Returns all the objects with this hash."""
        ret: List[ObjectInstance] = list()
        for object_ in self._objects_map.values():
            if ontology_object is None or object_.ontology_item.feature_node_hash == ontology_object.feature_node_hash:
                ret.append(object_)
                # DENIS: the accessors are protected. Check that no one can do anything stupid.
        return ret

    def add_object(self, object_instance: ObjectInstance, force=True):
        """
        Do we want a bulk function? probably not needed as it is local? (only for the force option)

        Args:
            force: overwrites current objects, otherwise this will replace the current object.
        """
        if not object_instance.is_valid():
            raise ValueError("The supplied ObjectInstance is not in a valid format.")

        if object_instance._parent is not None:
            raise RuntimeError(
                "The supplied ObjectInstance is already part of a LabelRow. You can only add a ObjectInstance to one "
                "LabelRow. You can do a ObjectInstance.copy() to create an identical ObjectInstance which is not part of "
                "any LabelRow."
            )

        object_hash = object_instance.object_hash
        if object_hash in self._objects_map and not force:
            raise ValueError("The supplied ObjectInstance was already previously added. (the object_hash is the same).")
        elif object_hash in self._objects_map and force:
            self._objects_map.pop(object_hash)

        self._objects_map[object_hash] = object_instance
        object_instance._parent = self

        self._add_to_frame_to_hashes_map(object_instance)

    def add_classification(self, classification_instance: ClassificationInstance, force: bool = False):
        if not classification_instance.is_valid():
            raise ValueError("The supplied ClassificationInstance is not in a valid format.")

        # DENIS: probably better to have a member function saying whether a parent is currently set.
        if classification_instance._parent is not None:
            raise RuntimeError(
                "The supplied ClassificationInstance is already part of a LabelRow. You can only add a ClassificationInstance"
                " to one LabelRow. You can do a ClassificationInstance.copy() to create an identical ObjectInstance which is "
                "not part of any LabelRow."
            )

        classification_hash = classification_instance.classification_hash
        already_present_frame = self._is_classification_already_present(
            classification_instance.ontology_item, classification_instance.frames()
        )
        if classification_hash in self._classifications_map and not force:
            raise ValueError(
                "The supplied ClassificationInstance was already previously added. (the classification_hash is the same)."
            )

        if already_present_frame is not None and not force:
            raise ValueError(
                f"A ClassificationInstance of the same type was already added and has overlapping frames. One "
                f"overlapping frame that was found is `{already_present_frame}`. Make sure that you only add "
                f"classifications which are on frames where the same type of classification does not yet exist."
            )

        if classification_hash in self._classifications_map and force:
            self._classifications_map.pop(classification_hash)

        self._classifications_map[classification_hash] = classification_instance
        classification_instance._parent = self

        self._classifications_to_frames[classification_instance.ontology_item].update(
            set(classification_instance.frames())
        )
        self._add_to_frame_to_hashes_map(classification_instance)

    def _is_classification_already_present(
        self, classification: Classification, frames: Iterable[int]
    ) -> Optional[int]:
        present_frames = self._classifications_to_frames.get(classification, set())
        for frame in frames:
            if frame in present_frames:
                return frame
        return None

    def _remove_frames_from_classification(self, classification: Classification, frames: Iterable[int]) -> None:
        present_frames = self._classifications_to_frames.get(classification, set())
        for frame in frames:
            present_frames.remove(frame)

    def remove_classification(self, classification_instance: ClassificationInstance):
        classification_hash = classification_instance.classification_hash
        self._classifications_map.pop(classification_hash)
        all_frames = self._classifications_to_frames[classification_instance.ontology_item]
        actual_frames = classification_instance.frames()
        for actual_frame in actual_frames:
            all_frames.remove(actual_frame)

    def _add_to_frame_to_hashes_map(self, label_item: Union[ObjectInstance, ClassificationInstance]):
        """This can be called by the ObjectInstance."""
        for frame in label_item.frames():
            if isinstance(label_item, ObjectInstance):
                self._frame_to_hashes[frame].add(label_item.object_hash)
            elif isinstance(label_item, ClassificationInstance):
                self._frame_to_hashes[frame].add(label_item.classification_hash)
            else:
                return NotImplementedError(f"Got an unexpected label item class `{type(label_item)}`")

    def get_classifications(
        self, ontology_classification: Optional[Classification] = None
    ) -> List[ClassificationInstance]:
        """Returns all the objects with this hash."""
        ret = []
        for classification_instance in self._classifications_map.values():
            if (
                ontology_classification is None
                or ontology_classification.feature_node_hash == classification_instance.ontology_item.feature_node_hash
            ):
                ret.append(classification_instance)
        return ret

    def get_objects_by_frame(self, frames: Iterable[int]) -> Set[ObjectInstance]:
        """DENIS: maybe merge this with the getter above."""
        ret: Set[ObjectInstance] = set()
        for frame in frames:
            hashes = self._frame_to_hashes[frame]
            for hash_ in hashes:
                if hash_ in self._objects_map:
                    ret.add(self._objects_map[hash_])

        return ret

    def get_classifications_by_frame(self, frames: Iterable[int]) -> Set[ClassificationInstance]:
        ret: Set[ClassificationInstance] = set()
        for frame in frames:
            hashes = self._frame_to_hashes[frame]
            for hash_ in hashes:
                if hash_ in self._classifications_map:
                    ret.add(self._classifications_map[hash_])
        return ret

    def remove_object(self, object_instance: ObjectInstance):
        """Remove the object."""
        self._objects_map.pop(object_instance.object_hash)
        self._remove_from_frame_to_hashes_map(object_instance.frames(), object_instance.object_hash)
        object_instance._parent = None

    def _remove_from_frame_to_hashes_map(self, frames: Iterable[int], item_hash: str):
        for frame in frames:
            self._frame_to_hashes[frame].remove(item_hash)

    def _parse_label_row_dict(self, label_row_dict: dict) -> LabelRowReadOnlyData:
        frame_level_data = self._parse_image_group_frame_level_data(label_row_dict["data_units"])
        image_hash_to_frame = {item.image_hash: item.frame_number for item in frame_level_data.values()}
        frame_to_image_hash = {item.frame_number: item.image_hash for item in frame_level_data.values()}
        # DENIS: for images/image_groups, we need a per image data row. For videos/dicoms this is not needed.
        return LabelRowReadOnlyData(
            label_hash=label_row_dict["label_hash"],
            dataset_hash=label_row_dict["dataset_hash"],
            dataset_title=label_row_dict["dataset_title"],
            data_title=label_row_dict["data_title"],
            data_type=DataType(label_row_dict["data_type"]),
            label_status=label_row_dict["label_status"],  # This is some kind of enum.
            number_of_frames=float("inf"),  # TODO: make this an int by getting this from the BE.
            frame_level_data=frame_level_data,
            image_hash_to_frame=image_hash_to_frame,
            frame_to_image_hash=frame_to_image_hash,
        )

    def _parse_objects_map(self, label_row_dict: dict):
        # DENIS: catch and throw at the top level if we couldn't parse, meaning that the dict is invalid.
        # Iterate over the data_units. Find objects. Start adding them into

        # Think about breaking or not breaking the order of the objects
        # DENIS: the only way to really know the order is through the objects_index. In this case, we'd need
        # additional information from the BE.

        for data_unit in label_row_dict["data_units"].values():
            frame = int(data_unit["data_sequence"])  # DENIS: change for non-image groups.
            for frame_object_label in data_unit["labels"]["objects"]:
                object_hash = frame_object_label["objectHash"]
                if object_hash not in self._objects_map:
                    object_instance = self._create_new_object_instance(frame_object_label, frame)
                    self.add_object(object_instance)
                else:
                    self._add_coordinates_to_object_instance(frame_object_label, frame)

        self._add_objects_answers(label_row_dict)
        self._add_action_answers(label_row_dict)

    def _add_objects_answers(self, label_row_dict: dict):
        # DENIS: deal with dynamic answers at some point.
        for answer in label_row_dict["object_answers"].values():
            object_hash = answer["objectHash"]
            object_instance = self._objects_map[object_hash]

            for classification in answer["classifications"]:
                pass
                # DENIS: TODO: parse the classification answers into the object_instance
                # do the same for classification instances.

    def _add_action_answers(self, label_row_dict: dict):
        # DENIS: TODO
        pass

    def _create_new_object_instance(self, frame_object_label: dict, frame: int) -> ObjectInstance:
        ontology = self._ontology_structure
        feature_hash = frame_object_label["featureHash"]
        object_hash = frame_object_label["objectHash"]

        label_class = get_item_by_hash(feature_hash, ontology)
        object_instance = ObjectInstance(label_class, object_hash=object_hash)

        coordinates = self._get_coordinates(frame_object_label)
        object_frame_instance_info = ObjectFrameInstanceInfo.from_dict(frame_object_label)

        object_instance.set_coordinates(
            coordinates=coordinates, frames={frame}, object_frame_instance_info=object_frame_instance_info
        )
        return object_instance

    def _add_coordinates_to_object_instance(
        self,
        frame_object_label: dict,
        frame: int,
    ) -> None:
        object_hash = frame_object_label["objectHash"]
        object_instance = self._objects_map[object_hash]

        coordinates = self._get_coordinates(frame_object_label)
        object_frame_instance_info = ObjectFrameInstanceInfo.from_dict(frame_object_label)

        object_instance.set_coordinates(
            coordinates=coordinates, frames={frame}, object_frame_instance_info=object_frame_instance_info
        )

    def _get_coordinates(self, frame_object_label: dict) -> Coordinates:
        if "boundingBox" in frame_object_label:
            return BoundingBoxCoordinates.from_dict(frame_object_label)
        elif "polygon" in frame_object_label:
            return PolygonCoordinates.from_dict(frame_object_label)
        else:
            raise NotImplementedError("Getting other coordinates is not yet implemented.")

    def _parse_classifications_map(self, label_row_dict: dict) -> None:
        for data_unit in label_row_dict["data_units"].values():
            frame = int(data_unit["data_sequence"])
            for frame_classification_label in data_unit["labels"]["classifications"]:
                classification_hash = frame_classification_label["classificationHash"]
                if classification_hash not in self._classifications_map:
                    classification_instance = self._create_new_classification_instance(
                        frame_classification_label, frame, label_row_dict["classification_answers"]
                    )
                    self.add_classification(classification_instance)
                else:
                    self._add_frames_to_classification_instance(frame_classification_label, frame)

    def _parse_image_group_frame_level_data(self, label_row_data_units: dict) -> Dict[int, FrameLevelImageGroupData]:
        frame_level_data: Dict[int, FrameLevelImageGroupData] = dict()
        for _, payload in label_row_data_units.items():
            frame_number = payload["data_sequence"]
            frame_level_image_group_data = FrameLevelImageGroupData(
                image_hash=payload["data_hash"],
                image_title=payload["data_title"],
                data_link=payload["data_link"],  # DENIS: what happens if no URLs requested?
                file_type=payload["data_type"],
                frame_number=int(frame_number),
                width=payload["width"],
                height=payload["height"],
            )
            frame_level_data[frame_number] = frame_level_image_group_data
        return frame_level_data

    def _create_new_classification_instance(
        self, frame_classification_label: dict, frame: int, classification_answers: dict
    ) -> ClassificationInstance:
        ontology = self._ontology_structure
        feature_hash = frame_classification_label["featureHash"]
        classification_hash = frame_classification_label["classificationHash"]

        label_class = get_item_by_hash(feature_hash, ontology)
        classification_instance = ClassificationInstance(label_class, classification_hash=classification_hash)

        classification_instance.set_frames([frame])
        classification_frame_instance_info = ClassificationInstanceData.from_dict(frame_classification_label)
        classification_instance.set_classification_instance_data(classification_frame_instance_info)
        # DENIS: TODO: add the answers to the classification instance.
        answers_dict = classification_answers[classification_hash]["classifications"]
        self._add_static_answers_from_dict(classification_instance, answers_dict)

        return classification_instance

    def _add_static_answers_from_dict(
        self, classification_instance: ClassificationInstance, answers_dict: List[dict]
    ) -> None:
        if len(answers_dict) == 0:
            return

        answer_dict = answers_dict[0]

        answer = classification_instance.get_static_answer()
        # DENIS: check if the same ontology type etc.

        answer.from_dict(answer_dict)

    def _add_frames_to_classification_instance(self, frame_classification_label: dict, frame: int) -> None:
        object_hash = frame_classification_label["classificationHash"]
        classification_instance = self._classifications_map[object_hash]

        classification_instance.add_to_frames([frame])


# @dataclass
# class LabelMaster:
#     """
#     DENIS: this thing probably should take the corresponding ontology, ideally automatically
#     DENIS: there is actually not much difference between this and the `LabelRow` class. Probably we
#         want to merge them together.
#     """
#
#     #
#     # label_hash: str
#     # dataset_hash: str
#     # dataset_title: str
#     # data_title: str
#     # data_type: DataType
#     # # DENIS: the above fields could be translated less literally.
#     #
#     # single_label: LabelRow  # Only one label across this multi-label thing.
#
#     def get_or_create_label_by_frame(self, frame: Union[int, str]) -> LabelRow:
#         """Get it depending on frame number or hash."""
#         pass
#
#     def delete_label_by_frame(self, frame: Union[int, str]) -> bool:
#         """Depending on if there was one, return True or not"""
#         pass
#
#     def get_used_frames(self) -> List[Union[int, str]]:
#         pass
#
#     def reset_labels(self):
#         self.single_labels = list()
#
#     def upload(self):
#         """Do the client request"""
#         # Can probably just use the set label row here.
#         pass
#
#     def refresh(self, *, get_signed_urls: bool = False, force: bool = False) -> bool:
#         """
#         Grab the labels from the server. Return False if the labels have been changed in the meantime.
#
#         Args:
#             force:
#                 If `False`, it will not do the refresh if something has changed on the server.
#                 If `True`, it will always overwrite the local changes with what has happened on the server.
#         """
#         # Actually can probably use the get_label_row() here.
#
#     """
#     Now the data units will either be keyed by the video_hash. Unless it is an image group, then it is keyed
#     by the individual image_hashes.
#
#     for image groups and images we'd have only one label
#     for videos and dicoms we have multiple frames.
#
#     It seems like I'd like to create the common "labels" thing first, and then see how I want to glue
#     it together.
#     probably something like "add_label" which goes for a specific frame (data_sequence in img group) or for
#     a specific hash.
#     """


# DENIS: should this LabelStructure be able to be self-updatable? Without the involvement of the project?
def _get_option_by_hash(feature_node_hash: str, options: List[Option]):
    for option_ in options:
        if option_.feature_node_hash == feature_node_hash:
            return option_

        if option_.get_option_type() == OptionType.NESTABLE:
            found_item = _get_attribute_by_hash(feature_node_hash, option_.nested_options)
            if found_item is not None:
                return found_item

    return None


def _get_attribute_by_hash(feature_node_hash: str, attributes: List[Attribute]):
    for attribute in attributes:
        if attribute.feature_node_hash == feature_node_hash:
            return attribute

        if attribute.has_options_field():
            found_item = _get_option_by_hash(feature_node_hash, attribute.options)
            if found_item is not None:
                return found_item
    return None


def get_item_by_hash(feature_node_hash: str, ontology: OntologyStructure):
    for object_ in ontology.objects:
        if object_.feature_node_hash == feature_node_hash:
            return object_
        found_item = _get_attribute_by_hash(feature_node_hash, object_.attributes)
        if found_item is not None:
            return found_item

    for classification in ontology.classifications:
        if classification.feature_node_hash == feature_node_hash:
            return classification
        found_item = _get_attribute_by_hash(feature_node_hash, classification.attributes)
        if found_item is not None:
            return found_item

    raise RuntimeError("Item not found.")


def _lower_snake_case(s: str):
    return "_".join(s.lower().split())


def _get_static_answer_map(attributes: List[Attribute]) -> Dict[str, Answer]:
    answers = _get_default_answers_from_attributes(attributes)
    answer_map = {answer.ontology_attribute.feature_node_hash: answer for answer in answers}
    return answer_map


def _search_child_attributes(
    passed_attribute: Attribute, search_attribute: Attribute, static_answer_map: Dict[str, Answer]
) -> bool:
    if passed_attribute == search_attribute:
        return True

    if not isinstance(search_attribute, RadioAttribute):
        # DENIS: or raise something?
        return False

    answer = static_answer_map[search_attribute.feature_node_hash]
    value = answer.get_value()
    if value is None:
        return False

    for option in search_attribute.options:
        if value == option:
            for nested_option in option.nested_options:
                # If I have multi nesting here, what then?
                if _search_child_attributes(passed_attribute, nested_option, static_answer_map):
                    return True

    return False


def _set_answer_for_object(answer_object: Answer, answer_value: Union[str, Option, Iterable[Option]]) -> None:
    attribute = answer_object.ontology_attribute
    if isinstance(attribute, TextAttribute):
        answer_object.set(answer_value)
    elif isinstance(attribute, RadioAttribute):
        answer_object.set(answer_value)
    elif isinstance(attribute, ChecklistAttribute):
        answer_object.set_options(answer_value)
    else:
        raise ValueError(f"Unknown attribute type: {type(attribute)}")


def _get_answer_from_object(answer_object: Answer) -> Union[str, Option, Iterable[Option], None]:
    attribute = answer_object.ontology_attribute
    if isinstance(attribute, TextAttribute):
        return answer_object.get_value()
    elif isinstance(attribute, RadioAttribute):
        return answer_object.get_value()
    elif isinstance(attribute, ChecklistAttribute):
        return answer_object.get_options()
    else:
        raise ValueError(f"Unknown attribute type: {type(attribute)}")
