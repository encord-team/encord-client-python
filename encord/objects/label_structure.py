from dataclasses import Field, dataclass, field
from datetime import datetime
from enum import Flag, auto
from typing import Any, Dict, Iterable, List, Optional, Set, Type, Union

from encord.constants.enums import DataType
from encord.objects.common import (
    Attribute,
    ChecklistAttribute,
    RadioAttribute,
    Shape,
    TextAttribute,
)
from encord.objects.ontology_object import Object
from encord.objects.ontology_structure import OntologyStructure

"""
DENIS:
I'd like to optimise the reads and writes.

For reads I needs some associations

For writes I need the builder pattern same as the OntologyStructure.


"""


@dataclass
class _Answer:
    """Common fields amongst all anwers"""

    feature_hash: str
    answered: bool
    _ontology_attribute: Attribute
    # NOTE: no hash is needed here, it will be taken from the LabelObject once it needs to.

    def __init__(self, ontology_attribute: Attribute):
        self.answered = False
        self._ontology_attribute = ontology_attribute


@dataclass
class TextAnswer(_Answer):
    value: str
    # feature_hash: str
    # ^ Do I need to add the feature_hash of the specific text feature? I believe so.

    def __init__(self, ontology_attribute: TextAttribute):
        super().__init__(ontology_attribute)

    def set(self, value: str):
        self.value = value


@dataclass
class RadioAnswer(_Answer):
    value: str
    # ^ this could be the feature hash

    def __init__(self, ontology_attribute: RadioAttribute):
        super().__init__(ontology_attribute)

    def set(self, value: str):
        # NOTE: if the value is not in ontology, throw
        self.value = value


@dataclass
class CheckBoxAnswer(_Answer):
    values: List[str]
    # ^ A list of feature hashes
    # on write, this will be initially None. On read, this will always be inferred as all unchecked.

    def __init__(self, ontology_attribute: ChecklistAttribute):
        super().__init__(ontology_attribute)

    def set(self, values: List[str]):
        # NOTE: if the values are not in ontology, throw
        self.values = values


Answer = Union[TextAnswer, RadioAnswer, CheckBoxAnswer]
"""These ones are answers for dynamic and static things."""


def get_all_answers(ontology: OntologyStructure):
    """Maybe get all answers needed according to the specific part of the ontology structure???"""
    pass


@dataclass
class BoundingBoxCoordinates:
    """All the values are percentages relative to the total image size."""

    height: float
    width: float
    top_left_x: float
    top_left_y: float


@dataclass
class RotatableBoundingBoxCoordinates:
    """All the values are percentages relative to the total image size."""

    height: float
    width: float
    top_left_x: float
    top_left_y: float
    theta: float  # angle of rotation originating at center of box


@dataclass
class PointCoordinate:
    """All coordinates are a percentage relative to the total image size."""

    x: float
    y: float


PolygonCoordinates = List[PointCoordinate]
PolylineCoordinates = List[PointCoordinate]


class Visibility(Flag):
    """
    An item is invisible if it is outside the frame. It is occluded
    if it is covered by something in the frame, but it would otherwise
    be in the frame. Else it is visible.
    """

    VISIBLE = auto()
    INVISIBLE = auto()
    OCCLUDED = auto()


@dataclass
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


SkeletonCoordinates = List[SkeletonCoordinate]


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

# @dataclass
class LabelObject:
    """This is per video/image_group/dicom/...

    should you be able to set the color per object?
    """

    # DENIS: this needs to take an OntologyLabelObject to navigate around.
    def __init__(self, ontology_item: Object):
        self._ontology_item = ontology_item
        self._frames_to_coordinates: Dict[int, Coordinates] = dict()
        # DENIS: this also needs a reference to the parent object, to understand what kind of coordinates are allowed?

    def add_coordinates(
        self,
        coordinates: Coordinates,
        frames: Iterable[int],
    ):
        """
        DENIS: The client needs to be careful here! If a reference of multiple coordinates is being passed around, they
        might accidentally overwrite specific values.
        """
        expected_coordinate_type = ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS[self._ontology_item.shape]
        if type(coordinates) != expected_coordinate_type:
            raise ValueError(
                f"Expected a coordinate of type `{expected_coordinate_type}`, but got type `{type(coordinates)}`."
            )

        for frame in frames:
            self._frames_to_coordinates[frame] = coordinates

    def set_answer(self, answer: Answer) -> None:
        """
        This thing will throw if the answer is not possibly according to the ontology.
        If the answer is already there, it will actually

        """
        pass

    def is_valid(self) -> bool:
        """Check if is valid, could also return some human/computer  messages."""
        if len(self._frames_to_coordinates) == 0:
            return False
        return True

    def set_coordinates(self, coordinates: Any, frames: Any):
        """Instead of adding, this will overwrite current coordinates. Or do we need this?"""
        pass

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


@dataclass
class LabelRowReadOnlyData:
    label_hash: str
    dataset_hash: str
    dataset_title: str
    data_title: str
    data_type: DataType
    number_of_frames: int
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
        # DENIS: try to parse and create the read only data
        self._label_row_read_only_data = LabelRowReadOnlyData(
            label_hash="wow",
            dataset_hash="wow",
            dataset_title="wow",
            data_title="wow",
            data_type=DataType.VIDEO,
            number_of_frames=float("inf"),  # TODO: make this an int by getting this from the BE.
            # image_hash_to_frame= "wow",
            # frame_to_image_hash= "wow",
        )
        # DENIS: technically the objects/classifications don't need to be in order, but I believe that we're sometimes
        #  relying on them being in order. Can also use a dict which is ordered with an empty key.
        self.objects: List[LabelObject] = list()
        self.classifications: List[LabelClassification] = list()
        self._frame_to_items: Dict[int, Set[Union[LabelObject, LabelClassification]]] = dict()

    def get_image_hash(self, frame_number: int) -> str:
        return "xyz"

    def get_objects(self, ontology_object: Object):
        """Returns all the objects with this hash."""
        pass

    def add_object(self, label_object: LabelObject):
        """
        Validate that it was initialised well enough by having at least
        one coordinate. Can also validate that this object hash is not present yet. And that the coordinates are not
        out of bounds. But ideally this would already be guaranteed with the `.add_coordinate()` call.

        Do we want a bulk function? probably not needed as it is local?
        """
        pass

    def get_items(self, frame_number: int) -> Set[Union[LabelObject, LabelClassification]]:
        pass

    def remove_object(self, label_object: LabelObject):
        """Remove the object."""

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

    def refresh(self, force: bool = False) -> bool:
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
