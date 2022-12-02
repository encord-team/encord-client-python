from __future__ import annotations

from collections import defaultdict
from copy import copy, deepcopy
from dataclasses import Field, dataclass, field
from datetime import datetime
from enum import Flag, auto
from typing import Any, Dict, Iterable, List, NoReturn, Optional, Set, Type, Union

from encord.constants.enums import DataType
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


class _Answer:
    """Common fields amongst all answers"""

    _ontology_attribute: Attribute

    def __init__(self, ontology_attribute: Attribute):
        self._answered = False
        self._ontology_attribute = ontology_attribute

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
            raise RuntimeError(
                f"The supplied NestableOption `{value}` is not a child of the RadioAttribute that "
                f"is associated with this class: `{self._ontology_attribute}`"
            )
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


Answer = Union[TextAnswer, RadioAnswer, ChecklistAnswer]
"""These ones are answers for dynamic and static things."""


def get_all_answers(ontology: OntologyStructure):
    """Maybe get all answers needed according to the specific part of the ontology structure???"""
    pass


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
class ObjectFrameInstanceInfo:
    created_at: datetime = datetime.now()
    created_by: Optional[str] = None
    """None defaults to the user of the SDK"""
    last_edited_at: Optional[datetime] = datetime.now()
    last_edited_by: Optional[str] = None
    """None defaults to the user of the SDK"""
    confidence: float = 1
    manual_annotation: bool = True


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
        ontology_item: Object,
    ):
        self._ontology_item = ontology_item
        self._frames_to_instance_data: Dict[int, ObjectFrameInstanceData] = dict()
        # DENIS: this also needs a reference to the parent object, to understand what kind of coordinates are allowed?
        self._object_hash = short_uuid_str()
        self._parent: Optional[LabelRow] = None
        """This member should only be manipulated by a LabelRow"""

        self._static_answers: List[Answer] = self._get_static_answers()

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
        attributes = self._ontology_item.attributes
        return self._get_default_answers_from_attributes(attributes)

    def _get_default_answers_from_attributes(self, attributes: List[Attribute]) -> List[Answer]:
        ret: List[Answer] = list()
        for attribute in attributes:
            answer = self._get_default_answer_from_attribute(attribute)
            ret.append(answer)

            if attribute.has_options_field():
                for option in attribute.options:
                    if option.get_option_type() == OptionType.NESTABLE:
                        other_attributes = self._get_default_answers_from_attributes(option.nested_options)
                        ret.extend(other_attributes)

        return ret

    def _get_default_answer_from_attribute(self, attribute: Attribute) -> Answer:
        property_type = attribute.get_property_type()
        if property_type == PropertyType.TEXT:
            return TextAnswer(attribute)
        elif property_type == PropertyType.RADIO:
            return RadioAnswer(attribute)
        elif property_type == PropertyType.CHECKLIST:
            return ChecklistAnswer(attribute)
        else:
            raise RuntimeError(f"Got an attribute with an unexpected property type: {attribute}")

    @property
    def object_hash(self) -> str:
        return self._object_hash

    @object_hash.setter
    def object_hash(self, v: Any) -> NoReturn:
        raise RuntimeError("Cannot set the object hash on an instantiated label object.")

    @property
    def ontology_item(self) -> Any:
        return deepcopy(self._ontology_item)

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
        expected_coordinate_type = ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS[self._ontology_item.shape]
        if type(coordinates) != expected_coordinate_type:
            raise ValueError(
                f"Expected a coordinate of type `{expected_coordinate_type}`, but got type `{type(coordinates)}`."
            )

        for frame in frames:
            self._frames_to_instance_data[frame] = ObjectFrameInstanceData(
                coordinates=coordinates, object_frame_instance_info=object_frame_instance_info
            )

        if self._parent:
            self._parent._add_to_frame_to_hashes_map(self)

    def copy(self) -> LabelObject:
        """
        Creates an exact copy of this LabelObject but with a new object hash and without being associated to any
        LabelRow. This is useful if you want to add the semantically same LabelObject to multiple `LabelRow`s."""
        ret = LabelObject(self._ontology_item)
        ret._frames_to_instance_data = copy(self._frames_to_instance_data)
        # DENIS: test if a shallow copy is enough
        return ret

    def frames(self) -> List[int]:
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

        if self._parent:
            self._parent._remove_from_frame_to_hashes_map(frames, self.object_hash)

        # DENIS: ensure that dynamic answers are also handled properly.

    def set_answer(self, answer: Answer) -> None:
        """
        This thing will throw if the answer is not possibly according to the ontology.
        If the answer is already there, it will actually
        """
        pass

    def is_valid(self) -> bool:
        """Check if is valid, could also return some human/computer  messages."""
        if len(self._frames_to_instance_data) == 0:
            return False
        return True

    def add_dynamic_answers(
        self,
        frames: Any,
        answers: Any,
    ):
        """
        For a given range, add the dynamic answers

        Again, do intelligent range merging with the current ranges of the same answers
        """
        pass

    def set_static_answers(
        self,
        answers: List[Any],
    ):
        """Add or set the static answers"""
        pass

    def initialise_static_answers(self) -> List[Answer]:
        """Return the answers that still need to happen"""
        # DENIS: probably this should just be a member, initialisation can happen at construction.
        pass

    def get_dynamic_unanswered_objects(self):
        """Return the answers that still need to happen"""
        pass

    # def get_dynamic_answers_for_frame(self, frame_range, feature_hash: str) -> List[AnswerByFrames]:
    #     """Here we could set the answer for a sub range."""
    #     pass


@dataclass
class LabelClassification:
    pass

    def set_range(
        self,
        frames: Any,
    ):
        # essentially change the range.
        pass

    def get_static_unanswered_objects(self):
        """Return the answers that still need to happen"""
        pass

    def set_answers(self):
        """"""
        pass


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
    number_of_frames: int
    frame_level_data: Dict[int, FrameLevelImageGroupData]
    image_hash_to_frame: Dict[str, int] = field(default_factory=dict)
    frame_to_image_hash: Dict[int, str] = field(default_factory=dict)


class LabelRow:
    """
    DENIS: the big question here is how we want to see this.
    I'd argue that we actually want to flatten out the frames and the individual images, and create
    LabelObjects/LabelClassifications from that. So the range can be chosen across an arbitrary
    range of images/frames and then the coordinates can be set for multiple different frames.
    Keep in mind that we might have multiple instances of same object_hash in a given frame soon, but another
    hash will then separate those.

    will also need to be able to keep around possible coordinate sizes and also query those if necessary.

    This is essentially one blob of data_units. For an image_group we need to get all the hashed in.
    """

    def __init__(self, label_row_dict: dict):
        self._ontology_structure = OntologyStructure()
        self.label_row_read_only_data = self._parse_label_row_dict(label_row_dict)
        # DENIS: ^ this should probably be protected so no one resets it.

        # DENIS: next up need to also parse objects and classifications from current label rows.

        self._frame_to_hashes: defaultdict[int, Set[str]] = defaultdict(set)
        # ^ frames to object and classification hashes

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

    def _add_to_frame_to_hashes_map(self, label_object: LabelObject):
        """This can be called by the LabelObject."""
        for frame in label_object.frames():
            self._frame_to_hashes[frame].add(label_object.object_hash)

    def get_classifications(self, ontology_classification: Optional[Object] = None) -> List[LabelObject]:
        """Returns all the objects with this hash."""
        # DENIS: Which hash are we referring to here? the attribute one or the non-attribute one?
        return []

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

    def _parse_label_row_dict(self, label_row_dict: dict):
        frame_level_data = self._parse_image_group_frame_level_data(label_row_dict["data_units"])
        image_hash_to_frame = {item.image_hash: item.frame_number for item in frame_level_data.values()}
        frame_to_image_hash = {item.frame_number: item.image_hash for item in frame_level_data.values()}
        return LabelRowReadOnlyData(
            label_hash=label_row_dict["label_hash"],
            dataset_hash=label_row_dict["dataset_hash"],
            dataset_title=label_row_dict["dataset_title"],
            data_title=label_row_dict["data_title"],
            data_type=label_row_dict["data_type"],  # DENIS: translate this into the enum
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

    # def add_new_object(
    #     self,
    #     feature_hash: str,
    # ) -> LabelObject:
    #     """All it does, is getting the new object but also passing in the correct ontology."""

    # def add_object_maybe_not(
    #     self,
    #     feature_hash: str,
    #     coordinates: Any,
    #     # ^ DENIS: maybe we want to specify this only on the object itself?
    #     #     However, do we really want to create a label with a practically invalid
    #     #     object? So maybe what we want is to add an object as a whole here?
    #     #     then we could validate in this function whether this object actually makes
    #     #     sense or not
    #     frames: Union[Set[int], Set[str]],
    #     # ^ should range be a more intelligent range? Maybe a custom class?
    #     answers: Optional[Any] = None,
    #     *,
    #     created_at: datetime = datetime.now(),
    #     created_by: Optional[str] = None,
    #     last_edited_at: datetime = datetime.now(),
    #     last_edited_by: Optional[str] = None,
    #     confidence: float = 1.0,
    #     manual_annotation: bool = True,
    #     color: Optional[str] = None,
    # ):
    #     """
    #     * dynamic answers.
    #
    #     * TODO: do I want to have an `add_bounding_box`, `add_polygon`, ... function instead?
    #         It can simply complain right away if the wrong coordinate is added.
    #     * say reviews are read only
    #
    #     Args:
    #         frames: The frames in which this object with the exact same coordinates and answers will be placed.
    #     """
    #     pass

    # def add_classification(
    #     self,
    #     feature_hash: str,
    #     frames: Union[Set[int], Set[str]],
    #     answer: Any,
    #     *,
    #     created_at: datetime = datetime.now(),
    #     created_by: Optional[str] = None,
    #     last_edited_at: datetime = datetime.now(),
    #     last_edited_by: Optional[str] = None,
    #     confidence: float = 1.0,
    #     manual_annotation: bool = True,
    # ):
    #     """
    #     * Ensure that the client can supply the classification answers.
    #     * How does the client add a classification range?
    #     * Note: no support for dynamic attributes is needed.
    #     * Say somewhere that `reviews` is a read only property that will not be added to the server.
    #     TODO: the default should be clear from the signature.
    #     """
    #     pass
    #     x = frames
    #     """Frames need to be added intelligently - as in adjacent frames are added intelligently."""
    #     y = answer
    #     """
    #     The answer could be a text, or a specific choice of radio or classification. Likely we'd want
    #     to have a separate class for this.
    #     """


@dataclass
class LabelMaster:
    """
    DENIS: this thing probably should take the corresponding ontology, ideally automatically
    DENIS: there is actually not much difference between this and the `LabelRow` class. Probably we
        want to merge them together.
    """

    #
    # label_hash: str
    # dataset_hash: str
    # dataset_title: str
    # data_title: str
    # data_type: DataType
    # # DENIS: the above fields could be translated less literally.
    #
    # single_label: LabelRow  # Only one label across this multi-label thing.

    def get_or_create_label_by_frame(self, frame: Union[int, str]) -> LabelRow:
        """Get it depending on frame number or hash."""
        pass

    def delete_label_by_frame(self, frame: Union[int, str]) -> bool:
        """Depending on if there was one, return True or not"""
        pass

    def get_used_frames(self) -> List[Union[int, str]]:
        pass

    def reset_labels(self):
        self.single_labels = list()

    def upload(self):
        """Do the client request"""
        # Can probably just use the set label row here.
        pass

    def refresh(self, *, get_signed_urls: bool = False, force: bool = False) -> bool:
        """
        Grab the labels from the server. Return False if the labels have been changed in the meantime.

        Args:
            force:
                If `False`, it will not do the refresh if something has changed on the server.
                If `True`, it will always overwrite the local changes with what has happened on the server.
        """
        # Actually can probably use the get_label_row() here.

    """
    Now the data units will either be keyed by the video_hash. Unless it is an image group, then it is keyed
    by the individual image_hashes.
    
    for image groups and images we'd have only one label
    for videos and dicoms we have multiple frames. 
    
    It seems like I'd like to create the common "labels" thing first, and then see how I want to glue
    it together.
    probably something like "add_label" which goes for a specific frame (data_sequence in img group) or for
    a specific hash. 
    """


# DENIS: should this LabelStructure be able to be self-updatable? Without the involvement of the project?
def _get_option_by_hash(feature_node_hash: str, options: List[Option]):
    for option_ in options:
        if option_.feature_node_hash == feature_node_hash:
            return option_

        if option_.get_option_type == OptionType.NESTABLE:
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
