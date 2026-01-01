from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
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

from encord.common.range_manager import RangeManager
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
from encord.objects.spaces.base_space import Space
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
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from encord.objects import Classification, ClassificationInstance, Option
    from encord.objects.ontology_labels_impl import LabelRowV2
    from encord.objects.ontology_object import Object, ObjectInstance

FrameOverlapStrategy = Union[Literal["error"], Literal["replace"]]


class VideoSpace(Space[_GeometricFrameObjectAnnotation, _FrameClassificationAnnotation]):
    """Video space implementation for frame-based video annotations."""

    def __init__(
        self,
        space_id: str,
        label_row: LabelRowV2,
        number_of_frames: int,
        width: int,
        height: int,
    ):
        super().__init__(space_id, label_row)

        # Keeps track of object/classification annotation data on each frame
        self._frames_to_object_hash_to_annotation_data: defaultdict[int, dict[str, _GeometricAnnotationData]] = (
            defaultdict(dict)
        )
        self._frames_to_classification_hash_to_annotation_data: defaultdict[int, dict[str, _AnnotationData]] = (
            defaultdict(dict)
        )

        # Keeps track of which frames each object/classification still exists on.
        # Used primarily to completely remove object if someone has removed it from all frames via `remove_object_instance_from_frames` or
        # `remove_classification_instance_from_frames`.
        self._object_hash_to_range_manager: defaultdict[str, RangeManager] = defaultdict(RangeManager)
        self._classification_hash_to_range_manager: defaultdict[str, RangeManager] = defaultdict(RangeManager)

        # Used to track whether an instance of a classification_ontology exists on frames
        self._classifications_ontology_to_ranges: defaultdict[Classification, RangeManager] = defaultdict(RangeManager)

        self._object_hash_to_dynamic_answer_manager: dict[str, DynamicAnswerManager] = dict()

        # Need to check if this is 1-indexed
        self._number_of_frames: int = number_of_frames
        self._width = width
        self._height = height

    def _is_classification_present_on_frames(
        self, classification: Classification, frames: Frames
    ) -> Tuple[bool, Ranges]:
        if classification.is_global and classification in self._classifications_ontology_to_ranges:
            return True, []
        else:
            range_manager = self._classifications_ontology_to_ranges.get(classification, RangeManager())
            intersection = range_manager.intersection(frames)
            return len(intersection) > 0, intersection

    def _remove_conflicting_classifications_from_frames(
        self, classification: ClassificationInstance, conflicting_ranges: Ranges
    ) -> None:
        """
        Method for removing conflicting classifications from frames.
        Used when user is adding classification instances to frames where other instances of the same classification are already present.
        We therefore need to remove those other classification instances from the frames.
        """

        conflicting_frames = frames_class_to_frames_list(conflicting_ranges) if conflicting_ranges else []
        for frame in conflicting_frames:
            if frame not in self._frames_to_classification_hash_to_annotation_data:
                continue

            # Find all classification_hashes on this frame that belong to the same ontology Classification
            hashes_to_remove = []
            for classification_hash in self._frames_to_classification_hash_to_annotation_data[frame].keys():
                if classification_hash in self._classifications_map:
                    existing_classification = self._classifications_map[classification_hash]
                    if existing_classification._ontology_classification == classification._ontology_classification:
                        hashes_to_remove.append(classification_hash)

            # Remove the conflicting classification_hash entries
            for hash_to_remove in hashes_to_remove:
                self._frames_to_classification_hash_to_annotation_data[frame].pop(hash_to_remove, None)

    def _are_frames_valid(self, frames: List[int]) -> None:
        max_frame = max(frames)
        min_frame = min(frames)

        max_allowed_frame_index = self._number_of_frames - 1  # Number of frames is 1-indexed.

        if min_frame < 0:
            raise LabelRowError(f"Frame {min_frame} is invalid. Negative frames are not supported.")
        if max_frame > max_allowed_frame_index:
            raise LabelRowError(
                f"Frame {max_frame} is invalid. The max frame on this video is {max_allowed_frame_index}."
            )

    def _put_object_instance(
        self,
        object_instance: ObjectInstance,
        frames: Frames,
        coordinates: GeometricCoordinates,
        *,
        on_overlap: FrameOverlapStrategy,
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
    ) -> None:
        frame_list = frames_class_to_frames_list(frames)
        self._are_frames_valid(frame_list)
        self._objects_map[object_instance.object_hash] = object_instance

        if object_instance.object_hash not in self._object_hash_to_dynamic_answer_manager:
            self._object_hash_to_dynamic_answer_manager[object_instance.object_hash] = DynamicAnswerManager(
                object_instance
            )

        object_instance._add_to_space(self)

        check_coordinate_type(coordinates, object_instance._ontology_object, self._label_row)

        # Checks overlap
        for frame in frame_list:
            objects_on_frame = self._frames_to_object_hash_to_annotation_data.get(frame)
            if objects_on_frame is None:
                continue

            existing_frame_data = objects_on_frame.get(object_instance.object_hash)
            if on_overlap == "error" and existing_frame_data is not None:
                raise LabelRowError(
                    f"Annotation already exists on frame {frame}. Set 'on_overlap' to 'replace' to overwrite existing annotations."
                )

        range_manager = RangeManager(frames)
        self._object_hash_to_range_manager[object_instance.object_hash].add_ranges(range_manager.get_ranges())

        for frame in frame_list:
            existing_frame_annotation_data = self._get_frame_object_annotation_data(
                object_hash=object_instance.object_hash, frame=frame
            )
            if existing_frame_annotation_data is None:
                existing_frame_annotation_data = _GeometricAnnotationData(
                    annotation_metadata=_AnnotationMetadata(),
                    coordinates=coordinates,
                )

                self._frames_to_object_hash_to_annotation_data[frame][object_instance.object_hash] = (
                    existing_frame_annotation_data
                )

            existing_frame_annotation_data.annotation_metadata.update_from_optional_fields(
                created_at=created_at,
                created_by=created_by,
                last_edited_at=last_edited_at,
                last_edited_by=last_edited_by,
                confidence=confidence,
                manual_annotation=manual_annotation,
            )
            existing_frame_annotation_data.coordinates = coordinates

    def put_object_instance(
        self,
        object_instance: ObjectInstance,
        frames: Frames,
        coordinates: GeometricCoordinates,
        *,
        on_overlap: FrameOverlapStrategy = "error",
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
    ) -> None:
        """Add an object instance to specific frames in the video space.

        Args:
            object_instance: The object instance to add to the video space.
            frames: Frame numbers or ranges where the object should appear. Can be:
                - A single frame number (int)
                - A list of frame numbers (List[int])
                - A Range object, specifying the start and end of the range (Range)
                - A list of Range objects for multiple ranges (List[Range])
            coordinates: Geometric coordinates for the object (e.g., bounding box, polygon, polyline).
            on_overlap: Strategy for handling existing annotations on the same frames.
                - "error" (default): Raises an error if annotation already exists.
                - "replace": Overwrites existing annotations on overlapping frames.
            created_at: Optional timestamp when the annotation was created.
            created_by: Optional identifier of who created the annotation.
            last_edited_at: Optional timestamp when the annotation was last edited.
            last_edited_by: Optional identifier of who last edited the annotation.
            confidence: Optional confidence score for the annotation (0.0 to 1.0).
            manual_annotation: Optional flag indicating if this was manually annotated.

        Raises:
            LabelRowError: If frames are invalid or if annotation already exists when on_overlap="error".
        """
        self._label_row._check_labelling_is_initalised()
        self._method_not_supported_for_object_instance_with_frames(object_instance=object_instance)
        self._method_not_supported_for_object_instance_with_dynamic_attributes(object_instance=object_instance)

        self._put_object_instance(
            object_instance=object_instance,
            frames=frames,
            coordinates=coordinates,
            on_overlap=on_overlap,
            created_at=created_at,
            created_by=created_by,
            last_edited_at=last_edited_at,
            last_edited_by=last_edited_by,
            confidence=confidence,
            manual_annotation=manual_annotation,
        )

    def remove_object_instance_from_frames(
        self,
        object_instance: ObjectInstance,
        frames: Frames,
    ) -> List[int]:
        """Remove an object instance from specific frames in the video space.

        If the object is removed from all frames, it will be completely removed from the space.
        All dynamic answers associated with the object on these frames will also be removed.

        Args:
            object_instance: The object instance to remove from frames.
            frames: Frame numbers or ranges to remove the object from. Can be:
                - A single frame number (int)
                - A list of frame numbers (List[int])
                - A Range object, specifying the start and end of the range (Range)
                - A list of Range objects for multiple ranges (List[Range])

        Returns:
            List[int]: List of frame numbers where the object was actually removed.
                Empty if the object didn't exist on any of the specified frames.
        """
        self._label_row._check_labelling_is_initalised()
        self._method_not_supported_for_object_instance_with_frames(object_instance=object_instance)

        frame_list = frames_class_to_frames_list(frames)

        # Remove all dynamic answers from these frames
        self._remove_all_answers_from_frames(object_instance, frame_list)

        # Tracks frames that are actually removed. User might have passed in frames that object doesn't even exist on.
        frames_removed: list[int] = []

        for frame in frame_list:
            object_removed_from_frame = self._frames_to_object_hash_to_annotation_data[frame].pop(
                object_instance.object_hash, None
            )
            if object_removed_from_frame is not None:
                frames_removed.append(frame)

        range_manager_for_object_hash = self._object_hash_to_range_manager[object_instance.object_hash]
        temp_range_manager = RangeManager(frames)
        range_manager_for_object_hash.remove_ranges(temp_range_manager.get_ranges())
        if len(range_manager_for_object_hash.get_ranges()) == 0:
            self._objects_map.pop(object_instance.object_hash)
            self._object_hash_to_dynamic_answer_manager.pop(object_instance.object_hash)

        return frames_removed

    def _remove_all_answers_from_frames(self, object_instance: ObjectInstance, frames: List[int]) -> None:
        """Remove all dynamic answers from the specified frames for an object instance.

        Args:
            object_instance: The object instance to remove answers from.
            frames: List of frame numbers to remove answers from.
        """
        dynamic_answer_manager = self._object_hash_to_dynamic_answer_manager.get(object_instance.object_hash)
        if dynamic_answer_manager is None:
            # No dynamic answers to remove
            return

        # Get all dynamic attributes for this object
        dynamic_attributes = [attr for attr in object_instance._ontology_object.attributes if attr.dynamic]

        # Remove answers for each dynamic attribute on the specified frames
        for attribute in dynamic_attributes:
            dynamic_answer_manager.delete_answer(attribute, frames=frames)

    # This implementation is copied mostly from ObjectInstance.set_answer_from_list
    def _set_answer_from_list(self, object_hash: str, answers_list: List[Dict[str, Any]]):
        grouped_answers = defaultdict(list)
        object_instance = self._objects_map[object_hash]
        dynamic_answer_manager = self._object_hash_to_dynamic_answer_manager[object_instance.object_hash]

        for answer_dict in answers_list:
            attribute = _get_attribute_by_hash(answer_dict["featureHash"], object_instance._ontology_object.attributes)
            if attribute is None:
                raise LabelRowError(
                    "One of the attributes does not exist in the ontology. Cannot create a valid LabelRow."
                )
            if not object_instance._is_attribute_valid_child_of_object_instance(attribute):
                raise LabelRowError(
                    "One of the attributes set for a classification is not a valid child of the classification. "
                    "Cannot create a valid LabelRow."
                )

            grouped_answers[attribute.feature_node_hash].append(answer_dict)

        for feature_hash, answers_list in grouped_answers.items():
            attribute = _get_attribute_by_hash(feature_hash, object_instance._ontology_object.attributes)
            assert attribute  # we already checked that attribute is not null above. So just silencing this for now
            self._set_answer_from_grouped_list(dynamic_answer_manager, attribute, answers_list)

    def _set_answer_from_grouped_list(
        self, dynamic_answer_manager: DynamicAnswerManager, attribute: Attribute, answers_list: List[Dict[str, Any]]
    ) -> None:
        if isinstance(attribute, ChecklistAttribute):
            if not attribute.dynamic:
                raise LabelRowError("This method should not be called for non-dynamic attributes.")
            else:
                all_feature_hashes: Set[str] = set()
                ranges = []
                for answer_dict in answers_list:
                    feature_hashes: Set[str] = {answer["featureHash"] for answer in answer_dict["answers"]}
                    all_feature_hashes.update(feature_hashes)
                    for frame_range in ranges_list_to_ranges(answer_dict["range"]):
                        ranges.append((frame_range, feature_hashes))

                options_cache = {
                    feature_hash: attribute.get_child_by_hash(feature_hash, type_=Option)
                    for feature_hash in all_feature_hashes
                }

                for frame_range, feature_hashes in ObjectInstance._merge_answers_to_non_overlapping_ranges(ranges):
                    options = [options_cache[feature_hash] for feature_hash in feature_hashes]
                    dynamic_answer_manager.set_answer(options, attribute, [frame_range])
        else:
            for answer in answers_list:
                self._set_answer_from_dict(dynamic_answer_manager, answer, attribute)

    def _set_answer_from_dict(
        self, dynamic_answer_manager: DynamicAnswerManager, answer_dict: Dict[str, Any], attribute: Attribute
    ) -> None:
        if not attribute.dynamic:
            raise LabelRowError("This method should not be called for non-dynamic attributes.")

        ranges = ranges_list_to_ranges(answer_dict["range"])

        if isinstance(attribute, TextAttribute):
            dynamic_answer_manager.set_answer(answer_dict["answers"], attribute, ranges)
        elif isinstance(attribute, RadioAttribute):
            if len(answer_dict["answers"]) == 1:
                feature_hash = answer_dict["answers"][0]["featureHash"]
                option = attribute.get_child_by_hash(feature_hash, type_=Option)
                dynamic_answer_manager.set_answer(option, attribute, ranges)
        elif isinstance(attribute, ChecklistAttribute):
            options = []
            for answer in answer_dict["answers"]:
                feature_hash = answer["featureHash"]
                option = attribute.get_child_by_hash(feature_hash, type_=Option)
                options.append(option)
            dynamic_answer_manager.set_answer(options, attribute, ranges)
        elif isinstance(attribute, NumericAttribute):
            value: float = answer_dict["answers"]

            if not isinstance(value, float) and not isinstance(value, int):
                raise LabelRowError(f"The answer for a numeric attribute must be a float or an int. Found {value}.")

            dynamic_answer_manager.set_answer(value, attribute, ranges)
        else:
            raise NotImplementedError(f"The attribute type {type(attribute)} is not supported.")

    def set_answer_on_frames(
        self,
        object_instance: ObjectInstance,
        frames: Frames,
        answer: Union[str, NumericAnswerValue, Option, Sequence[Option]],
        attribute: Optional[Attribute] = None,
    ) -> None:
        """Set dynamic attribute answers for an object instance on specific frames.

        This method is only for dynamic attributes. For static attributes, use `ObjectInstance.set_answer`.

        Args:
            object_instance: The object instance to set answers for.
            frames: Frame numbers or ranges where the answer should be applied.
            answer: The answer value. Can be:
                - str: For text attributes
                - float/int: For numeric attributes
                - Option: For radio attributes
                - Sequence[Option]: For checklist attributes
            attribute: The attribute to set the answer for. If None, will be inferred from the answer type.

        Raises:
            LabelRowError: If the attribute is not dynamic, not a valid child of the object,
                or if the object doesn't exist on the space yet.
        """
        self._label_row._check_labelling_is_initalised()
        if attribute is None:
            attribute = _infer_attribute_from_answer(object_instance._ontology_object.attributes, answer)
        if not object_instance._is_attribute_valid_child_of_object_instance(attribute):
            raise LabelRowError("The attribute is not a valid child of the object.")
        elif not attribute.dynamic and not object_instance._is_selectable_child_attribute(attribute):
            raise LabelRowError(
                "Setting a nested attribute is only possible if all parent attributes have been selected."
            )
        elif attribute.dynamic is False:
            raise LabelRowError(
                "This method should only be used for dynamic attributes. For static attributes, use `ObjectInstance.set_answer`."
            )

        frames_list = frames_class_to_frames_list(frames)

        valid_frames = []
        for frame in frames_list:
            annotation_data = self._get_frame_object_annotation_data(
                object_hash=object_instance.object_hash, frame=frame
            )
            if annotation_data is not None:
                valid_frames.append(frame)

        dynamic_answer_manager = self._object_hash_to_dynamic_answer_manager.get(object_instance.object_hash)
        if dynamic_answer_manager is None:
            raise LabelRowError(
                "Object does not yet exist on this space. Place the object on this space with `Space.place_object`."
            )

        dynamic_answer_manager.set_answer(answer, attribute, frames=valid_frames)

    def remove_answer_from_frame(
        self,
        object_instance: ObjectInstance,
        attribute: Attribute,
        frame: int,
        filter_answer: Optional[Union[str, Option, Iterable[Option]]] = None,
    ) -> None:
        """Remove a dynamic attribute answer from an object instance on a specific frame.

        Args:
            object_instance: The object instance to remove the answer from.
            attribute: The dynamic attribute whose answer should be removed.
            frame: The frame number to remove the answer from.
            filter_answer: Optional filter to remove only specific answer values.
                For checklist attributes, can specify which options to remove.

        Raises:
            LabelRowError: If the attribute is not dynamic or if the object doesn't exist on the space.
        """
        self._label_row._check_labelling_is_initalised()
        if not attribute.dynamic:
            raise LabelRowError("This method should not be called for non-dynamic attributes.")

        dynamic_answer_manager = self._object_hash_to_dynamic_answer_manager.get(object_instance.object_hash)
        if dynamic_answer_manager is None:
            raise LabelRowError(
                "Object does not yet exist on this space. Place the object on this space with `Space.place_object`."
            )

        dynamic_answer_manager.delete_answer(attribute, frames=frame, filter_answer=filter_answer)

    def get_answer_on_frames(
        self,
        object_instance: ObjectInstance,
        frames: Frames,
        attribute: Attribute,
        filter_answer: Union[str, NumericAnswerValue, Option, Iterable[Option], None] = None,
    ) -> AnswersForFrames:
        """Get dynamic attribute answers for an object instance on specific frames.

        This method is only for dynamic attributes. For static attributes, use `ObjectInstance.get_answer`.

        Args:
            object_instance: The object instance to get answers from.
            frames: Frame numbers or ranges to retrieve answers for.
            attribute: The dynamic attribute to get answers for.
            filter_answer: Optional filter to retrieve only specific answer values.

        Returns:
            AnswersForFrames: Dictionary mapping frames to their corresponding answers.

        Raises:
            LabelRowError: If the attribute is not dynamic or if the object doesn't exist on the space.
        """
        self._label_row._check_labelling_is_initalised()
        dynamic_answer_manager = self._object_hash_to_dynamic_answer_manager.get(object_instance.object_hash)
        if dynamic_answer_manager is None:
            raise LabelRowError("This object does not exist on this space.")

        if not attribute.dynamic:
            raise LabelRowError("This method should only be used for dynamic attributes.")

        return dynamic_answer_manager.get_answer(attribute, filter_answer, filter_frames=frames)

    def put_classification_instance(
        self,
        classification_instance: ClassificationInstance,
        frames: Frames,
        *,
        on_overlap: FrameOverlapStrategy = "error",
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
    ) -> None:
        """Add a classification instance to specific frames in the video space.

        Args:
            classification_instance: The classification instance to add to the video space.
            frames: Frame numbers or ranges where the classification should appear. Can be:
                - A single frame number (int)
                - A list of frame numbers (List[int])
                - A Range object, specifying the start and end of the range (Range)
                - A list of Range objects for multiple ranges (List[Range])
            on_overlap: Strategy for handling existing classifications on the same frames.
                - "error" (default): Raises an error if classification already exists.
                - "replace": Overwrites existing classifications on overlapping frames.
            created_at: Optional timestamp when the annotation was created.
            created_by: Optional identifier of who created the annotation.
            last_edited_at: Optional timestamp when the annotation was last edited.
            last_edited_by: Optional identifier of who last edited the annotation.
            confidence: Optional confidence score for the annotation (0.0 to 1.0).
            manual_annotation: Optional flag indicating if this was manually annotated.

        Raises:
            LabelRowError: If frames are invalid or if classification already exists when on_overlap="error".
        """
        self._label_row._check_labelling_is_initalised()
        self._method_not_supported_for_classification_instance_with_frames(
            classification_instance=classification_instance
        )

        frame_list = frames_class_to_frames_list(frames)
        self._are_frames_valid(frame_list)

        self._classifications_map[classification_instance.classification_hash] = classification_instance
        classification_instance._add_to_space(self)

        is_present, conflicting_ranges = self._is_classification_present_on_frames(
            classification_instance._ontology_classification, frame_list
        )

        if is_present:
            if on_overlap == "error":
                location_msg = (
                    "globally" if classification_instance.is_global() else f"on the ranges {conflicting_ranges}. "
                )
                raise LabelRowError(
                    f"The classification '{classification_instance.classification_hash}' already exists "
                    f"{location_msg}"
                    f"Set 'on_overlap' parameter to 'replace' to overwrite."
                )
            elif on_overlap == "replace":
                # If overwriting, remove conflicting classification entries from other classification instances
                self._remove_conflicting_classifications_from_frames(
                    classification=classification_instance,
                    conflicting_ranges=conflicting_ranges,
                )

        for frame in frame_list:
            existing_frame_classification_annotation_data = self._get_frame_classification_annotation_data(
                classification_hash=classification_instance.classification_hash, frame=frame
            )

            if existing_frame_classification_annotation_data is None:
                existing_frame_classification_annotation_data = _AnnotationData(
                    annotation_metadata=_AnnotationMetadata(),
                )

                self._frames_to_classification_hash_to_annotation_data[frame][
                    classification_instance.classification_hash
                ] = existing_frame_classification_annotation_data

            existing_frame_classification_annotation_data.annotation_metadata.update_from_optional_fields(
                created_at=created_at,
                created_by=created_by,
                last_edited_at=last_edited_at,
                last_edited_by=last_edited_by,
                confidence=confidence,
                manual_annotation=manual_annotation,
            )

        range_manager = RangeManager(frame_class=frame_list)
        ranges_to_add = range_manager.get_ranges()

        existing_range_manager = self._classifications_ontology_to_ranges.get(
            classification_instance._ontology_classification
        )
        if existing_range_manager is None:
            self._classifications_ontology_to_ranges[classification_instance._ontology_classification] = range_manager
        else:
            existing_range_manager.add_ranges(ranges_to_add)

        self._classification_hash_to_range_manager[classification_instance._classification_hash].add_ranges(
            ranges_to_add
        )

    def remove_classification_instance_from_frames(
        self,
        classification_instance: ClassificationInstance,
        frames: Frames,
    ) -> List[int]:
        """Remove a classification instance from specific frames in the video space.

        If the classification is removed from all frames, it will be completely removed from the space.

        Args:
            classification_instance: The classification instance to remove from frames.
            frames: Frame numbers or ranges to remove the classification from. Can be:
                - A single frame number (int)
                - A list of frame numbers (List[int])
                - A Range object, specifying the start and end of the range (Range)
                - A list of Range objects for multiple ranges (List[Range])

        Returns:
            List[int]: List of frame numbers where the classification was actually removed.
                Empty if the classification didn't exist on any of the specified frames.
        """
        self._label_row._check_labelling_is_initalised()
        self._method_not_supported_for_classification_instance_with_frames(
            classification_instance=classification_instance
        )

        frame_list = frames_class_to_frames_list(frames)

        # Keeps track of frames that are actually removed. User might pass in frames that the classification does not exist on.
        frames_removed: list[int] = []
        for frame in frame_list:
            classification_removed = self._frames_to_classification_hash_to_annotation_data[frame].pop(
                classification_instance.classification_hash, None
            )
            if classification_removed is not None:
                frames_removed.append(frame)

        range_manager = RangeManager(frame_class=frames_removed)
        ranges_to_remove = range_manager.get_ranges()

        classification_ontology_range_manager = self._classifications_ontology_to_ranges.get(
            classification_instance._ontology_classification
        )

        if classification_ontology_range_manager is not None:
            classification_ontology_range_manager.remove_ranges(ranges_to_remove)

        range_manager_for_classification_instance = self._classification_hash_to_range_manager[
            classification_instance.classification_hash
        ]
        range_manager_for_classification_instance.remove_ranges(ranges_to_remove)
        if len(range_manager_for_classification_instance.get_ranges()) == 0:
            self._classifications_map.pop(classification_instance.classification_hash)

        return frames_removed

    def _get_object_annotation_on_frame(self, object_hash: str, frame: int = 0) -> _GeometricFrameObjectAnnotation:
        return _GeometricFrameObjectAnnotation(space=self, object_instance=self._objects_map[object_hash], frame=frame)

    def _create_object_annotation(self, obj_hash: str) -> _GeometricFrameObjectAnnotation:
        """Not supported for VideoSpace - use _get_object_annotation_on_frame() instead.

        VideoSpace has frame-specific annotations, so it overrides get_object_instance_annotations()
        with its own implementation that iterates through all frames.
        """
        raise NotImplementedError(
            "VideoSpace does not support _create_object_annotation() without a frame. "
            "Use _get_object_annotation_on_frame() instead or call get_object_instance_annotations() "
            "to get all annotations across all frames."
        )

    def _create_classification_annotation(self, classification_hash: str) -> _FrameClassificationAnnotation:
        """Not supported for VideoSpace - VideoSpace handles classifications per-frame.

        VideoSpace has frame-specific annotations, so it overrides get_classification_instance_annotations()
        with its own implementation that iterates through all frames.
        """
        raise NotImplementedError(
            "VideoSpace does not support _create_classification_annotation() without a frame. "
            "Use get_classification_instance_annotations() to get all annotations across all frames."
        )

    def get_object_instance_annotations(
        self, filter_object_instances: Optional[list[str]] = None
    ) -> Iterator[_GeometricFrameObjectAnnotation]:
        """Get all object instance annotations in the video space.

        Args:
            filter_object_instances: Optional list of object hashes to filter by.
                If provided, only annotations for these objects will be returned.

        Returns:
            Iterator[_GeometricFrameObjectAnnotation]: Iterator over all object annotations across all frames,
                sorted by frame number. Annotations are created lazily as the iterator is consumed.
        """
        self._label_row._check_labelling_is_initalised()
        filter_set = set(filter_object_instances) if filter_object_instances is not None else None

        for frame, obj in dict(sorted(self._frames_to_object_hash_to_annotation_data.items())).items():
            for obj_hash in obj.keys():
                if filter_set is None or obj_hash in filter_set:
                    yield self._get_object_annotation_on_frame(object_hash=obj_hash, frame=frame)

    def get_object_instance_annotations_by_frame(self) -> Dict[int, List[_GeometricFrameObjectAnnotation]]:
        """Get all object instance annotations organized by frame number.

        Returns:
            Dict[int, List[_GeometricFrameObjectAnnotation]]: Dictionary mapping frame numbers to lists of
                object annotations on that frame.
        """
        self._label_row._check_labelling_is_initalised()
        ret: Dict[int, List[_GeometricFrameObjectAnnotation]] = {}

        for frame, object_to_annotation_data_map in sorted(self._frames_to_object_hash_to_annotation_data.items()):
            ret[frame] = [
                self._get_object_annotation_on_frame(frame=frame, object_hash=object_hash)
                for object_hash in object_to_annotation_data_map.keys()
            ]

        return ret

    def get_classification_instance_annotations(
        self, filter_classification_instances: Optional[list[str]] = None
    ) -> Iterator[_FrameClassificationAnnotation]:
        """Get all classification instance annotations in the video space.

        Args:
            filter_classification_instances: Optional list of classification hashes to filter by.
                If provided, only annotations for these classifications will be returned.

        Returns:
            Iterator[_FrameClassificationAnnotation]: Iterator over all classification annotations across all frames,
                sorted by frame number. Annotations are created lazily as the iterator is consumed.
        """
        self._label_row._check_labelling_is_initalised()

        for frame, classification in dict(
            sorted(self._frames_to_classification_hash_to_annotation_data.items())
        ).items():
            for classification_hash, annotation in classification.items():
                if filter_classification_instances is None or classification_hash in filter_classification_instances:
                    yield _FrameClassificationAnnotation(
                        space=self,
                        classification_instance=self._classifications_map[classification_hash],
                        frame=frame,
                    )

    def remove_object_instance(self, object_hash: str) -> Optional[ObjectInstance]:
        """Completely remove an object instance from all frames in the video space.

        This removes the object from all frames it appears on and cleans up all associated data.

        Args:
            object_hash: The hash identifier of the object instance to remove.

        Returns:
            Optional[ObjectInstance]: The removed object instance, or None if the object wasn't found.
        """
        self._label_row._check_labelling_is_initalised()
        object_instance = self._objects_map.pop(object_hash, None)

        if object_instance is None:
            return None

        object_instance._remove_from_space(self.space_id)
        self._object_hash_to_dynamic_answer_manager.pop(object_instance.object_hash)
        self._object_hash_to_range_manager.pop(object_hash)

        frames_to_remove: list[int] = []
        for frame, object_to_annotation_data_map in self._frames_to_object_hash_to_annotation_data.items():
            if object_hash in object_to_annotation_data_map:
                object_to_annotation_data_map.pop(object_hash)

            if not bool(object_to_annotation_data_map):
                frames_to_remove.append(frame)

        # If no objects on frame, remove it from the map
        for frame in frames_to_remove:
            self._frames_to_object_hash_to_annotation_data.pop(frame)

        return object_instance

    def remove_classification_instance(self, classification_hash: str) -> Optional[ClassificationInstance]:
        """Completely remove a classification instance from all frames in the video space.

        This removes the classification from all frames it appears on and cleans up all associated data.

        Args:
            classification_hash: The hash identifier of the classification instance to remove.

        Returns:
            Optional[ClassificationInstance]: The removed classification instance, or None if the classification wasn't found.
        """
        self._label_row._check_labelling_is_initalised()
        classification_instance = self._classifications_map.pop(classification_hash, None)

        if classification_instance is not None:
            classification_instance._remove_from_space(self.space_id)
            for frame, classification in self._frames_to_classification_hash_to_annotation_data.items():
                if classification_hash in classification:
                    classification.pop(classification_hash)

            self._classification_hash_to_range_manager.pop(classification_instance.classification_hash)

        return classification_instance

    """INTERNAL METHODS FOR DESERDE"""

    def _create_new_object_from_frame_object_dict(self, frame_object_label: FrameObject) -> ObjectInstance:
        from encord.objects.ontology_object import Object, ObjectInstance

        ontology = self._label_row._ontology.structure
        feature_hash = frame_object_label["featureHash"]
        object_hash = frame_object_label["objectHash"]
        label_class = ontology.get_child_by_hash(feature_hash, type_=Object)
        return ObjectInstance(ontology_object=label_class, object_hash=object_hash)

    def _create_new_classification_from_frame_label_dict(
        self, frame_classification_label: FrameClassification, classification_answers: dict
    ) -> ClassificationInstance:
        from encord.objects import Classification, ClassificationInstance

        ontology = self._label_row._ontology.structure
        feature_hash = frame_classification_label["featureHash"]
        classification_hash = frame_classification_label["classificationHash"]
        label_class = ontology.get_child_by_hash(feature_hash, type_=Classification)

        classification_answer = classification_answers.get(classification_hash)
        if classification_answer is None:
            raise LabelRowError("No classification answer found for classification hash {}".format(classification_hash))

        new_classification_instance = ClassificationInstance(
            ontology_classification=label_class, classification_hash=classification_hash
        )
        answers_dict = classification_answer["classifications"]
        self._label_row._add_static_answers_from_dict(new_classification_instance, answers_dict)

        return new_classification_instance

    def _get_frame_object_annotation_data(self, object_hash: str, frame: int) -> Optional[_GeometricAnnotationData]:
        object_to_frame_annotation_data = self._frames_to_object_hash_to_annotation_data.get(frame)
        if object_to_frame_annotation_data is None:
            return None
        else:
            return object_to_frame_annotation_data.get(object_hash)

    def _get_frame_classification_annotation_data(
        self, classification_hash: str, frame: int
    ) -> Optional[_AnnotationData]:
        classification_to_frame_annotation_data = self._frames_to_classification_hash_to_annotation_data.get(frame)
        if classification_to_frame_annotation_data is None:
            return None
        else:
            return classification_to_frame_annotation_data.get(classification_hash)

    def _dynamic_answers_to_encord_dict(self, object_instance: ObjectInstance) -> List[DynamicAttributeObject]:
        ret = []
        dynamic_answer_manager = self._object_hash_to_dynamic_answer_manager[object_instance.object_hash]

        if dynamic_answer_manager is None:
            raise LabelRowError("No dynamic answers found for this object instance on this space.")

        for answer, ranges in dynamic_answer_manager.get_all_answers():
            d_opt = answer.to_encord_dict(ranges, space_id=self.space_id)
            if d_opt is not None:
                ret.append(cast(DynamicAttributeObject, d_opt))
        return ret

    def _to_encord_object(
        self,
        object_instance: ObjectInstance,
        frame_object_annotation_data: _GeometricAnnotationData,
    ) -> FrameObject:
        from encord.objects.ontology_object import Object

        ontology_hash = object_instance._ontology_object.feature_node_hash
        ontology_object = self._label_row._ontology.structure.get_child_by_hash(ontology_hash, type_=Object)

        base_frame_object = create_frame_object_dict(
            ontology_object=ontology_object,
            object_hash=object_instance.object_hash,
            object_instance_annotation=frame_object_annotation_data.annotation_metadata,
        )

        frame_object = add_coordinates_to_frame_object_dict(
            coordinates=frame_object_annotation_data.coordinates,
            base_frame_object=base_frame_object,
            width=self._width,
            height=self._height,
        )

        return frame_object

    def _to_encord_classification(
        self,
        classification_instance: ClassificationInstance,
        frame_classification_annotation_data: _AnnotationData,
    ) -> FrameClassification:
        from encord.objects import Classification
        from encord.objects.attributes import Attribute

        ontology_hash = classification_instance._ontology_classification.feature_node_hash
        ontology_classification = self._label_row._ontology.structure.get_child_by_hash(
            ontology_hash, type_=Classification
        )

        attribute_hash = classification_instance.ontology_item.attributes[0].feature_node_hash
        attribute = self._label_row._ontology.structure.get_child_by_hash(attribute_hash, type_=Attribute)

        frame_object_dict = create_frame_classification_dict(
            ontology_classification=ontology_classification,
            classification_instance_annotation=frame_classification_annotation_data.annotation_metadata,
            classification_hash=classification_instance.classification_hash,
            attribute=attribute,
        )

        return frame_object_dict

    def _build_frame_label_dict(self, frame: int) -> LabelBlob:
        object_list: List[FrameObject] = []
        classification_list: List[FrameClassification] = []

        objects_to_annotation_data = self._frames_to_object_hash_to_annotation_data.get(frame, {})
        classifications_to_annotation_data = self._frames_to_classification_hash_to_annotation_data.get(frame, {})

        for object_hash, frame_object_annotation_data in objects_to_annotation_data.items():
            space_object = self._objects_map[object_hash]
            object_list.append(
                self._to_encord_object(
                    object_instance=space_object, frame_object_annotation_data=frame_object_annotation_data
                )
            )

        for classification_hash, frame_classification_annotation_data in classifications_to_annotation_data.items():
            space_classification = self._classifications_map[classification_hash]
            classification_list.append(
                self._to_encord_classification(
                    classification_instance=space_classification,
                    frame_classification_annotation_data=frame_classification_annotation_data,
                )
            )

        return LabelBlob(
            objects=object_list,
            classifications=classification_list,
        )

    def _to_object_answers(self, existing_object_answers: dict[str, ObjectAnswer]) -> Dict[str, ObjectAnswer]:
        ret: dict[str, ObjectAnswerForGeometric] = {}
        for object_instance in self._objects_map.values():
            all_static_answers = self._label_row._get_all_static_answers(object_instance)
            object_index_element: ObjectAnswerForGeometric = {
                "classifications": list(reversed(all_static_answers)),
                "objectHash": object_instance.object_hash,
            }
            ret[object_instance.object_hash] = object_index_element

        return cast(Dict[str, ObjectAnswer], ret)

    def _to_classification_answers(
        self, existing_classification_answers: dict[str, ClassificationAnswer]
    ) -> dict[str, ClassificationAnswer]:
        ret: dict[str, ClassificationAnswer] = {}
        for classification_instance in self._classifications_map.values():
            classification_range_manager = self._classification_hash_to_range_manager.get(
                classification_instance.classification_hash, None
            )
            if classification_range_manager is None:
                continue

            all_static_answers = classification_instance.get_all_static_answers()
            classifications = [
                cast(AttributeDict, answer.to_encord_dict()) for answer in all_static_answers if answer.is_answered()
            ]
            classification_index_element: ClassificationAnswer = {
                "classifications": classifications,
                "classificationHash": classification_instance.classification_hash,
                "featureHash": classification_instance.feature_hash,
                "spaces": {
                    self.space_id: {
                        "range": ranges_to_list(
                            classification_range_manager.get_ranges(),
                        ),
                        "type": "frame",
                    }
                },
            }

            ret[classification_instance.classification_hash] = classification_index_element

        return ret

    def _parse_space_dict(
        self,
        space_info: SpaceInfo,
        object_answers: dict[str, ObjectAnswerForGeometric],
        classification_answers: dict[str, ClassificationAnswer],
    ) -> None:
        for frame_str, frame_label in space_info["labels"].items():
            self._parse_frame_label_dict(
                frame=int(frame_str), frame_label=frame_label, classification_answers=classification_answers
            )

        for answer in object_answers.values():
            object_hash = answer["objectHash"]
            if object_instance := self._objects_map.get(object_hash):
                answer_list = answer["classifications"]
                object_instance.set_answer_from_list(answer_list)

    def _parse_frame_label_dict(self, frame: int, frame_label: LabelBlob, classification_answers: dict):
        for obj in frame_label["objects"]:
            object_hash = obj["objectHash"]
            # TODO: Might have to keep track of all objects on spaces in parent
            object_instance = None

            for space in self._label_row._space_map.values():
                object_instance = space._objects_map.get(object_hash)
                if object_instance is not None:
                    break

            if object_instance is None:
                object_instance = self._create_new_object_from_frame_object_dict(frame_object_label=obj)

            coordinates = get_geometric_coordinates_from_frame_object_dict(frame_object_dict=obj)
            object_frame_instance_info = _AnnotationMetadata.from_dict(obj)
            self.put_object_instance(
                object_instance=object_instance,
                coordinates=coordinates,
                frames=frame,
                created_at=object_frame_instance_info.created_at,
                created_by=object_frame_instance_info.created_by,
                last_edited_at=object_frame_instance_info.last_edited_at,
                last_edited_by=object_frame_instance_info.last_edited_by,
                manual_annotation=object_frame_instance_info.manual_annotation,
                confidence=object_frame_instance_info.confidence,
            )

        # Process classifications
        for classification in frame_label["classifications"]:
            classification_hash = classification["classificationHash"]

            classification_instance = None
            for space in self._label_row._space_map.values():
                classification_instance = space._classifications_map.get(classification_hash)
                if classification_instance is not None:
                    break

            if classification_instance is None:
                classification_instance = self._create_new_classification_from_frame_label_dict(
                    frame_classification_label=classification,
                    classification_answers=classification_answers,
                )

            classification_frame_instance_info = _AnnotationMetadata.from_dict(classification)
            self.put_classification_instance(
                classification_instance=classification_instance,
                frames=frame,
                created_at=classification_frame_instance_info.created_at,
                created_by=classification_frame_instance_info.created_by,
                last_edited_at=classification_frame_instance_info.last_edited_at,
                last_edited_by=classification_frame_instance_info.last_edited_by,
                manual_annotation=classification_frame_instance_info.manual_annotation,
                confidence=classification_frame_instance_info.confidence,
            )

    def _to_space_dict(self) -> VideoSpaceInfo:
        """Export video space to dictionary format."""
        labels: dict[str, LabelBlob] = {}
        frames_with_objects = list(self._frames_to_object_hash_to_annotation_data.keys())
        frames_with_classifications = list(self._frames_to_classification_hash_to_annotation_data.keys())
        frames_with_both_objects_and_classifications = sorted(set(frames_with_objects + frames_with_classifications))

        for frame in frames_with_both_objects_and_classifications:
            frame_label = self._build_frame_label_dict(frame=frame)
            labels[str(frame)] = frame_label

        return VideoSpaceInfo(
            space_type=SpaceType.VIDEO,
            labels=labels,
            number_of_frames=self._number_of_frames,
            width=self._width,
            height=self._height,
        )
