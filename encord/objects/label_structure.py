from __future__ import annotations

from collections import defaultdict
from copy import copy, deepcopy
from dataclasses import Field, dataclass, field
from datetime import datetime
from enum import Flag, auto
from typing import Any, Dict, Iterable, List, NoReturn, Optional, Set, Type, Union

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

"""
DENIS:
I'd like to optimise the reads and writes.

For reads I needs some associations

For writes I need the builder pattern same as the OntologyStructure.

"""
# DENIS: think about better error codes for people to catch.


class _Answer:
    """Common fields amongst all answers"""

    _ontology_attribute: Attribute

    def __init__(self, ontology_attribute: Attribute):
        self._answered = False
        self._ontology_attribute = ontology_attribute
        self._answer_uuid = short_uuid_str()

    def is_answered(self) -> bool:
        return self._answered

    def unset(self) -> None:
        """Remove the value from the answer"""
        self._answered = False
        # DENIS: might be better to default everything again for more consistent states!

    @property
    def ontology_attribute(self):
        return deepcopy(self._ontology_attribute)

    @ontology_attribute.setter
    def ontology_attribute(self, v: Any) -> NoReturn:
        raise RuntimeError("Cannot reset the ontology attribute of an instantiated answer.")


class TextAnswer(_Answer):
    def __init__(self, ontology_attribute: TextAttribute):
        super().__init__(ontology_attribute)
        self._value = None

    def set(self, value: str) -> TextAnswer:
        """Returns the object itself"""
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

    def __hash__(self):
        return hash((self._value, type(self).__name__))


@dataclass
class RadioAnswer(_Answer):
    def __init__(self, ontology_attribute: RadioAttribute):
        super().__init__(ontology_attribute)
        self._value: Optional[NestableOption] = None

    def set(self, value: NestableOption):
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

    def __init__(self, parent: LabelObject, frame: int, attribute: Attribute):
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
    def __init__(self, parent: LabelObject, frame: int, attribute: Attribute):
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
    def __init__(self, parent: LabelObject, frame: int, attribute: Attribute):
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
    def __init__(self, parent: LabelObject, frame: int, attribute: Attribute):
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


# PolygonCoordinates = List[PointCoordinate]


@dataclass(frozen=True)
class PolygonCoordinates:
    values: List[PointCoordinate]


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
    created_at: datetime = datetime.now()
    created_by: Optional[str] = None
    """None defaults to the user of the SDK"""
    last_edited_at: Optional[datetime] = datetime.now()
    last_edited_by: Optional[str] = None
    """None defaults to the user of the SDK"""
    confidence: float = 1
    manual_annotation: bool = True
    read_only_info: ObjectFrameReadOnlyInstanceInfo = ObjectFrameReadOnlyInstanceInfo()


@dataclass(frozen=True)
class ObjectFrameInstanceData:
    coordinates: Coordinates
    object_frame_instance_info: ObjectFrameInstanceInfo


class LabelObject:
    """This is per video/image_group/dicom/...

    should you be able to set the color per object?
    """

    # DENIS: this needs to take an OntologyLabelObject to navigate around.
    def __init__(
        self,
        ontology_object: Object,
    ):
        self._ontology_object = ontology_object
        self._frames_to_instance_data: Dict[int, ObjectFrameInstanceData] = dict()
        # DENIS: do I need to make tests for memory requirements? As in, how much more memory does
        # this thing take over the label structure itself (for large ones it would be interesting)
        self._object_hash = short_uuid_str()
        self._parent: Optional[LabelRow] = None
        """This member should only be manipulated by a LabelRow"""

        self._static_answers: List[Answer] = self._get_static_answers()

        self._frames_to_answers: Dict[int, Set[Answer]] = defaultdict(set)
        self._answers_to_frames: Dict[Answer, Set[int]] = defaultdict(set)
        # ^ for dynamic answer management => DENIS: may be better to have a manager class with the
        # responsibility to manage this

        self._dynamic_uninitialised_answer_options: Set[Answer] = self._get_dynamic_answers()
        # ^ read only for dynamic answers management.

    def _get_dynamic_answer(self, frame: int, attribute: Attribute) -> Answer:
        """This should only be called from the DynamicAnswer"""
        answers = self._frames_to_answers[frame]
        for answer in answers:
            if answer.ontology_attribute.feature_node_hash == attribute.feature_node_hash:
                return answer

        raise RuntimeError("The attribute is not a valid attribute for this LabelObject.")

    def _get_frames_for_dynamic_answer(self, answer: Answer) -> Set[int]:
        return self._answers_to_frames[answer]

    def _set_dynamic_answer_to_frames(self, frames: Iterable[int], answer: Answer) -> None:
        self._answers_to_frames[answer].update(set(frames))
        for frame in frames:
            self._frames_to_answers[frame].add(answer)

    def get_all_static_answers(
        self,
    ) -> List[Answer]:
        ret = copy(self._static_answers)
        # Deliberately always returning a shallow copy to make sure no one removes the static answers.
        return ret

    def get_static_answer(self, attribute: Attribute) -> Answer:
        # DENIS: can I be smarter about the return type according to the incoming type?
        for static_answer in self._static_answers:
            if attribute.feature_node_hash == static_answer.ontology_attribute.feature_node_hash:
                return static_answer
        raise ValueError("The attribute was not found in this LabelObject's ontology.")

    def _get_static_answers(self) -> List[Answer]:
        attributes = self._ontology_object.attributes
        return _get_default_answers_from_attributes(attributes)

    def _get_dynamic_answers(self) -> Set[Answer]:
        ret: Set[Answer] = set()
        for attribute in self._ontology_object.attributes:
            if attribute.dynamic:
                answer = _get_default_answer_from_attribute(attribute)
                ret.add(answer)
        return ret

    def get_dynamic_answer(self, frame: int, attribute: Attribute):
        # DENIS: probably I don't need two classes
        answer = self._get_dynamic_answer(frame, attribute)
        if isinstance(answer, TextAnswer):
            return DynamicTextAnswer(self, frame, answer.ontology_attribute)
        elif isinstance(answer, ChecklistAnswer):
            return DynamicChecklistAnswer(self, frame, answer.ontology_attribute)
        elif isinstance(answer, RadioAnswer):
            return DynamicRadioAnswer(self, frame, answer.ontology_attribute)
        else:
            raise NotImplemented("Need to implement the other answer types")

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
        raise RuntimeError("Cannot set the ontology item of an instantiated LabelObject.")

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
            self._add_initial_dynamic_answers(frame)

        if self._parent:
            self._parent._add_to_frame_to_hashes_map(self)

    def _add_initial_dynamic_answers(self, frame: int) -> None:
        if frame in self._frames_to_answers:
            return

        for answer in self._dynamic_uninitialised_answer_options:
            self._frames_to_answers[frame].add(answer)
            self._answers_to_frames[answer].add(frame)

    def copy(self) -> LabelObject:
        """
        Creates an exact copy of this LabelObject but with a new object hash and without being associated to any
        LabelRow. This is useful if you want to add the semantically same LabelObject to multiple `LabelRow`s."""
        ret = LabelObject(self._ontology_object)
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
            self._remove_dynamic_answers_from_frame(frame)

        if self._parent:
            self._parent._remove_from_frame_to_hashes_map(frames, self.object_hash)

        # DENIS: can we remove to make this invalid?
        # DENIS: ensure that dynamic answers are also handled properly.

    def _remove_dynamic_answers_from_frame(self, frame: int) -> None:
        answers = self._frames_to_answers[frame]
        for answer in answers:
            self._remove_dynamic_answer_at_frame(answer, frame)

        self._frames_to_answers.pop(frame)

    def _remove_dynamic_answer_at_frame(self, answer: Answer, frame: int) -> None:
        default_answer = _get_default_answer_from_attribute(answer.ontology_attribute)

        if hash(answer) == hash(default_answer):
            return

        self._answers_to_frames[answer].remove(frame)
        if len(self._answers_to_frames) == 0:
            self._answers_to_frames.pop(answer)

        self._frames_to_answers[frame].remove(answer)
        self._frames_to_answers[frame].add(default_answer)

    def _reset_dynamic_answer_at_frame(self, new_answer: Answer, old_answer: Answer, frame: int) -> None:
        self._answers_to_frames[old_answer].remove(frame)
        self._frames_to_answers[frame].remove(old_answer)

        self._answers_to_frames[new_answer].add(frame)
        self._frames_to_answers[frame].add(new_answer)

    def is_valid(self) -> bool:
        """Check if is valid, could also return some human/computer  messages."""
        if len(self._frames_to_instance_data) == 0:
            return False
        return True


class LabelClassification:
    def __init__(self, ontology_classification: Classification):
        # DENIS: should I also be able to accept the first level attribute? Ideally not, as
        # I'd need to awkwardly verify whether this is the first level attribute or not.
        self._ontology_classification = ontology_classification
        self._parent: Optional[LabelRow] = None
        self._classification_hash = short_uuid_str()

        self._static_answer: Answer = self._get_static_answer()
        self._frames: Set[int] = set()
        # DENIS: Ideally there would be a max range check.
        self._max_frame: int = float("inf")

    @property
    def classification_hash(self) -> str:
        return self._classification_hash

    @classification_hash.setter
    def classification_hash(self, v: Any) -> NoReturn:
        raise RuntimeError("Cannot set the object hash on an instantiated label object.")

    @property
    def ontology_item(self) -> Classification:
        return deepcopy(self._ontology_classification)

    @ontology_item.setter
    def ontology_item(self, v: Any) -> NoReturn:
        raise RuntimeError("Cannot set the ontology item of an instantiated LabelObject.")

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

    def remove_from_frames(self, frames: Iterable[int]) -> None:
        for frame in frames:
            self._frames.remove(frame)

        if self._parent is not None:
            self._parent._remove_frames_from_classification(self.ontology_item, frames)

    def frames(self) -> List[int]:
        return list(self._frames)

    def get_static_answer(self) -> Answer:
        return self._static_answer

    def is_valid(self) -> bool:
        return len(self._frames) > 0

    def _get_static_answer(self) -> Answer:
        attributes = self._ontology_classification.attributes
        answers = _get_default_answers_from_attributes(attributes)
        if len(answers) != 1:
            raise RuntimeError("The LabelClassification is in an invalid state.")
        return answers[0]

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

    def __init__(self, label_row_dict: dict, ontology_structure: dict):
        self._ontology_structure = OntologyStructure.from_dict(ontology_structure)
        self._label_row_read_only_data: LabelRowReadOnlyData = self._parse_label_row_dict(label_row_dict)
        # DENIS: ^ this should probably be protected so no one resets it.

        # DENIS: next up need to also parse objects and classifications from current label rows.

        self._frame_to_hashes: defaultdict[int, Set[str]] = defaultdict(set)
        # ^ frames to object and classification hashes

        self._classifications_to_frames: defaultdict[Classification, Set[int]] = defaultdict(set)

        self._objects_map: Dict[str, LabelObject] = dict()
        self._classifications_map: Dict[str, LabelClassification] = dict()
        # ^ conveniently a dict is ordered in Python. Use this to our advantage to keep the labels in order
        # at least at the final objects_index/classifications_index level.

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
        ret["object_answers"] = dict()  # TODO:
        ret["classification_answers"] = dict()  # TODO:
        ret["object_actions"] = dict()  # TODO:
        ret["label_status"] = read_only_data.label_status
        ret["data_units"] = self._to_encord_data_units()

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

    def _to_encord_label(self, frame_number: int):
        ret = {}

        # TODO:
        ret["objects"] = []
        ret["classifications"] = []

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

    def get_objects(self, ontology_object: Optional[Object] = None) -> List[LabelObject]:
        """Returns all the objects with this hash."""
        ret: List[LabelObject] = list()
        for object_ in self._objects_map.values():
            if ontology_object is None or object_.ontology_item.feature_node_hash == ontology_object.feature_node_hash:
                ret.append(object_)
                # DENIS: the accessors are protected. Check that no one can do anything stupid.
        return ret

    def add_object(self, label_object: LabelObject, force=True):
        """
        Do we want a bulk function? probably not needed as it is local? (only for the force option)

        Args:
            force: overwrites current objects, otherwise this will replace the current object.
        """
        if not label_object.is_valid():
            raise ValueError("The supplied LabelObject is not in a valid format.")

        if label_object._parent is not None:
            raise RuntimeError(
                "The supplied LabelObject is already part of a LabelRow. You can only add a LabelObject to one "
                "LabelRow. You can do a LabelObject.copy() to create an identical LabelObject which is not part of "
                "any LabelRow."
            )

        object_hash = label_object.object_hash
        if object_hash in self._objects_map and not force:
            raise ValueError("The supplied LabelObject was already previously added. (the object_hash is the same).")
        elif object_hash in self._objects_map and force:
            self._objects_map.pop(object_hash)

        self._objects_map[object_hash] = label_object
        label_object._parent = self

        self._add_to_frame_to_hashes_map(label_object)

    def add_classification(self, label_classification: LabelClassification, force: bool = False):
        if not label_classification.is_valid():
            raise ValueError("The supplied LabelClassification is not in a valid format.")

        # DENIS: probably better to have a member function saying whether a parent is currently set.
        if label_classification._parent is not None:
            raise RuntimeError(
                "The supplied LabelClassification is already part of a LabelRow. You can only add a LabelClassification"
                " to one LabelRow. You can do a LabelClassification.copy() to create an identical LabelObject which is "
                "not part of any LabelRow."
            )

        classification_hash = label_classification.classification_hash
        already_present_frame = self._is_classification_already_present(
            label_classification.ontology_item, label_classification.frames()
        )
        if classification_hash in self._classifications_map and not force:
            raise ValueError(
                "The supplied LabelClassification was already previously added. (the classification_hash is the same)."
            )

        if already_present_frame is not None and not force:
            raise ValueError(
                f"A LabelClassification of the same type was already added and has overlapping frames. One "
                f"overlapping frame that was found is `{already_present_frame}`. Make sure that you only add "
                f"classifications which are on frames where the same type of classification does not yet exist."
            )

        if classification_hash in self._classifications_map and force:
            self._classifications_map.pop(classification_hash)

        self._classifications_map[classification_hash] = label_classification
        label_classification._parent = self

        self._classifications_to_frames[label_classification.ontology_item].update(set(label_classification.frames()))
        self._add_to_frame_to_hashes_map(label_classification)

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

    def remove_classification(self, label_classification: LabelClassification):
        classification_hash = label_classification.classification_hash
        self._classifications_map.pop(classification_hash)
        all_frames = self._classifications_to_frames[label_classification.ontology_item]
        actual_frames = label_classification.frames()
        for actual_frame in actual_frames:
            all_frames.remove(actual_frame)

    def _add_to_frame_to_hashes_map(self, label_item: Union[LabelObject, LabelClassification]):
        """This can be called by the LabelObject."""
        for frame in label_item.frames():
            if isinstance(label_item, LabelObject):
                self._frame_to_hashes[frame].add(label_item.object_hash)
            elif isinstance(label_item, LabelClassification):
                self._frame_to_hashes[frame].add(label_item.classification_hash)
            else:
                return NotImplementedError(f"Got an unexpected label item class `{type(label_item)}`")

    def get_classifications(
        self, ontology_classification: Optional[Classification] = None
    ) -> List[LabelClassification]:
        """Returns all the objects with this hash."""
        ret = []
        for label_classification in self._classifications_map.values():
            if (
                ontology_classification is None
                or ontology_classification.feature_node_hash == label_classification.ontology_item.feature_node_hash
            ):
                ret.append(label_classification)
        return ret

    def get_objects_by_frame(self, frames: Iterable[int]) -> Set[LabelObject]:
        """DENIS: maybe merge this with the getter above."""
        ret: Set[LabelObject] = set()
        for frame in frames:
            hashes = self._frame_to_hashes[frame]
            for hash_ in hashes:
                if hash_ in self._objects_map:
                    ret.add(self._objects_map[hash_])

        return ret

    def remove_object(self, label_object: LabelObject):
        """Remove the object."""
        self._objects_map.pop(label_object.object_hash)
        self._remove_from_frame_to_hashes_map(label_object.frames(), label_object.object_hash)
        label_object._parent = None

    def _remove_from_frame_to_hashes_map(self, frames: Iterable[int], object_hash: str):
        for frame in frames:
            self._frame_to_hashes[frame].remove(object_hash)

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
