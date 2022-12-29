from __future__ import annotations

from collections import defaultdict
from copy import copy, deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, NoReturn, Optional, Set, Union, overload

from dateutil.parser import parse

from encord.constants.enums import DataType
from encord.objects.classification import Classification
from encord.objects.common import (
    Attribute,
    ChecklistAttribute,
    Option,
    RadioAttribute,
    TextAttribute,
)
from encord.objects.constants import (
    DATETIME_LONG_STRING_FORMAT,
    DEFAULT_CONFIDENCE,
    DEFAULT_MANUAL_ANNOTATION,
)
from encord.objects.coordinates import (
    ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS,
    BoundingBoxCoordinates,
    Coordinates,
    PolygonCoordinates,
)
from encord.objects.internal_helpers import (
    Answer,
    _get_static_answer_map,
    _search_child_attributes,
    get_answer_from_object,
    get_default_answer_from_attribute,
    set_answer_for_object,
)
from encord.objects.ontology_object import Object
from encord.objects.ontology_structure import OntologyStructure
from encord.objects.utils import (
    Frames,
    _lower_snake_case,
    frames_class_to_frames_list,
    short_uuid_str,
)

"""
DENIS:
I'd like to optimise the reads and writes.

For reads I needs some associations

For writes I need the builder pattern same as the OntologyStructure.

"""
# DENIS: think about better error codes for people to catch.


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

        set_answer_for_object(static_answer, answer)

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

        return get_answer_from_object(static_answer)

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

    def __repr__(self):
        return f"ClassificationInstance({self.classification_hash})"


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

    DENIS: For tracing, it could be an idea to record the function calls that are being done (can be condensed
    as well) and send them as part of the payload to the server. I could even have this as a more generic solution
    for the SDK.
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
        ontology_object = self._ontology_structure.get_item_by_hash(ontology_hash)

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
        ontology_classification = self._ontology_structure.get_item_by_hash(classification_feature_hash)
        attribute_hash = classification.ontology_item.attributes[0].feature_node_hash
        ontology_attribute = self._ontology_structure.get_item_by_hash(attribute_hash)

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

        label_class = ontology.get_item_by_hash(feature_hash)
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
        frame: int,  # DENIS: should default to None for the single image case.
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

        label_class = ontology.get_item_by_hash(feature_hash)
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
    range: Set[int]
    # DENIS: Do I really want to return a set here?


class ObjectInstance:
    """This is per video/image_group/dicom/...

    should you be able to set the color per object?


    DENIS: move this to `ontology_object` and have a my_ontology_object.create_instance() -> ObjectInstance
    """

    def __init__(self, ontology_object: Object, *, object_hash: Optional[str] = None):
        self._ontology_object = ontology_object
        self._frames_to_instance_data: Dict[int, ObjectFrameInstanceData] = dict()
        # DENIS: do I need to make tests for memory requirements? As in, how much more memory does
        # this thing take over the label structure itself (for large ones it would be interesting)
        self._object_hash = object_hash or short_uuid_str()
        self._parent: Optional[LabelRow] = None
        """This member should only be manipulated by a LabelRow"""

        self._static_answer_map: Dict[str, Answer] = _get_static_answer_map(self._ontology_object.attributes)
        # feature_node_hash of attribute to the answer.

        self._dynamic_answer_manager = DynamicAnswerManager(self)

    @overload
    def get_answer(
        self,
        attribute: TextAttribute,
        filter_answer: Union[str, Option, Iterable[Option], None] = None,
        filter_frame: Optional[int] = None,
    ) -> Optional[str]:
        ...

    @overload
    def get_answer(
        self,
        attribute: RadioAttribute,
        filter_answer: Union[str, Option, Iterable[Option], None] = None,
        filter_frame: Optional[int] = None,
    ) -> Optional[Option]:
        ...

    @overload
    def get_answer(
        self,
        attribute: ChecklistAttribute,
        filter_answer: Union[str, Option, Iterable[Option], None] = None,
        filter_frame: Optional[int] = None,
    ) -> Optional[List[Option]]:
        """Returns None only if the attribute is nested and the parent is unselected. Otherwise, if not
        yet answered it will return an empty list."""
        ...

    def get_answer(
        self,
        attribute: Attribute,
        filter_answer: Union[str, Option, Iterable[Option], None] = None,
        filter_frame: Optional[int] = None,
    ) -> Union[str, Option, Iterable[Option], None]:
        """
        Args:
            attribute: The ontology attribute to get the answer for.
            filter_answer: A filter for a specific answer value. Only applies to dynamic attributes.
            filter_frame: A filter for a specific frame. Only applies to dynamic attributes.
            DENIS: overthink the return type. Dynamic answers would have a different return type.
        """
        if attribute is None:
            attribute = self._ontology_object.attributes[0]
        elif not self._is_attribute_valid_child_of_object_instance(attribute):
            raise ValueError("The attribute is not a valid child of the classification.")
        elif not self._is_selectable_child_attribute(attribute):
            return None

        if attribute.dynamic:
            return self._dynamic_answer_manager.get_answer(attribute, filter_answer, filter_frame)

        static_answer = self._static_answer_map[attribute.feature_node_hash]

        return get_answer_from_object(static_answer)

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
            frames: Only relevant for dynamic attributes. The frames to set the answer for. If `None`, the
                answer is set for all frames that this object currently has set coordinates for (also overwriting
                current answers). This will not automatically propagate the answer to new frames that are added in the
                future.
                If this is anything but `None` for non-dynamic attributes, this will
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

        set_answer_for_object(static_answer, answer)

    def delete_answer(
        self,
        attribute: Attribute,
        filter_answer: Union[str, Option, Iterable[Option]] = None,
        frames: Optional[int] = None,
    ) -> None:
        """
        Args:
            attribute: The attribute to delete the answer for.
            filter_answer: A filter for a specific answer value. Only applies to dynamic attributes.
            frames: A filter for a specific frame. Only applies to dynamic attributes.
        """
        raise NotImplementedError("Needs to be implemented.")
        if attribute.dynamic:
            self._dynamic_answer_manager.delete_answer(attribute, frames)
            return

        static_answer = self._static_answer_map[attribute.feature_node_hash]
        # _set_answer_for_object(static_answer, None)

    def _is_attribute_valid_child_of_object_instance(self, attribute: Attribute) -> bool:
        # DENIS: this will fail for dynamic attributes.
        is_static_child = attribute.feature_node_hash in self._static_answer_map
        is_dynamic_child = self._dynamic_answer_manager.is_valid_dynamic_attribute(attribute)
        return is_dynamic_child or is_static_child

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

    def is_valid(self) -> bool:
        """Check if is valid, could also return some human/computer  messages."""
        if len(self._frames_to_instance_data) == 0:
            return False

        if not self.are_dynamic_answers_valid():
            return False

        return True

    def are_dynamic_answers_valid(self) -> bool:
        """
        Whether there are any dynamic answers on frames that have no coordinates.
        """
        dynamic_frames = set(self._dynamic_answer_manager.frames())
        local_frames = set(self.frames())

        return len(dynamic_frames - local_frames) == 0

    def _is_selectable_child_attribute(self, attribute: Attribute) -> bool:
        # I have the ontology classification, so I can build the tree from that. Basically do a DFS.
        ontology_object = self._ontology_object
        for search_attribute in ontology_object.attributes:
            if _search_child_attributes(attribute, search_attribute, self._static_answer_map):
                return True
        return False

    def __repr__(self):
        return f"ObjectInstance({self._object_hash})"


class DynamicAnswerManager:
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

    def delete_answer(self, attribute: Attribute, frames: Frames) -> None:
        frame_list = frames_class_to_frames_list(frames)

        for frame in frame_list:
            to_remove_answer = None
            for answer_object in self._frames_to_answers[frame]:
                # ideally this would not be a log(n) operation, however these will not be extremely large.
                if answer_object.ontology_attribute == attribute:
                    to_remove_answer = answer_object
                    break

            if to_remove_answer is not None:
                self._frames_to_answers[frame].remove(to_remove_answer)
                self._answers_to_frames[to_remove_answer].remove(frame)
                if self._answers_to_frames[to_remove_answer] == set():
                    del self._answers_to_frames[to_remove_answer]

    def set_answer(
        self, answer: Union[str, Option, Iterable[Option]], attribute: Attribute, frames: Optional[Frames] = None
    ) -> None:
        if frames is None:
            for available_frame in self._object_instance.frames():
                self._set_answer(answer, attribute, available_frame)
            return
        self._set_answer(answer, attribute, frames)

    def _set_answer(self, answer: Union[str, Option, Iterable[Option]], attribute: Attribute, frames: Frames) -> None:
        """Set the answer for a single frame"""

        self.delete_answer(attribute, frames)

        default_answer = get_default_answer_from_attribute(attribute)
        set_answer_for_object(default_answer, answer)

        frame_list = frames_class_to_frames_list(frames)
        for frame in frame_list:
            self._frames_to_answers[frame].add(default_answer)
            self._answers_to_frames[default_answer].add(frame)

    def get_answer(
        self,
        attribute: Attribute,
        filter_answer: Union[str, Option, Iterable[Option], None] = None,
        filter_frames: Optional[Frames] = None,
    ) -> List[AnswerForFrames]:
        """For a given attribute, return all the answers and frames given the filters."""
        ret = []
        filter_frames_set = None if filter_frames is None else set(frames_class_to_frames_list(filter_frames))
        for answer in self._answers_to_frames:
            if answer.ontology_attribute != attribute:
                continue
            if not (filter_answer is None or filter_answer == get_answer_from_object(answer)):
                continue
            actual_frames = self._answers_to_frames[answer]
            if not (filter_frames_set is None or len(actual_frames & filter_frames_set) > 0):
                continue
            ret.append(AnswerForFrames(answer=get_answer_from_object(answer), range=self._answers_to_frames[answer]))
        return ret

    def frames(self) -> Iterable[int]:
        """Returns all frames that have answers set."""
        return self._frames_to_answers.keys()

    def _get_dynamic_answers(self) -> Set[Answer]:
        ret: Set[Answer] = set()
        for attribute in self._object_instance.ontology_item.attributes:
            if attribute.dynamic:
                answer = get_default_answer_from_attribute(attribute)
                ret.add(answer)
        return ret
