from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union, cast

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
    get_geometric_coordinates_from_frame_object,
)
from encord.objects.frames import Frames, Ranges, frames_class_to_frames_list, ranges_list_to_ranges
from encord.objects.internal_helpers import _infer_attribute_from_answer
from encord.objects.label_utils import create_frame_classification_dict, create_frame_object_dict
from encord.objects.ontology_object_instance import AnswersForFrames, DynamicAnswerManager, check_coordinate_type
from encord.objects.spaces.annotation.base_annotation import AnnotationData, AnnotationMetadata
from encord.objects.spaces.annotation.geometric_annotation import (
    FrameClassificationAnnotation,
    GeometricAnnotationData,
    GeometricFrameObjectAnnotation,
)
from encord.objects.spaces.base_space import FramePlacement, Space
from encord.objects.spaces.types import ChildInfo, SpaceInfo, VideoSpaceInfo
from encord.objects.types import (
    AttributeDict,
    ClassificationAnswer,
    DynamicAttributeObject,
    FrameClassification,
    FrameObject,
    LabelBlob,
    ObjectAnswer,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from encord.objects import Classification, ClassificationInstance, Option
    from encord.objects.ontology_labels_impl import LabelRowV2
    from encord.objects.ontology_object import Object, ObjectInstance


class VideoSpace(Space):
    """Video space implementation for frame-based video annotations."""

    def __init__(
        self, space_id: str, parent: LabelRowV2, child_info: ChildInfo, number_of_frames: int, width: int, height: int
    ):
        super().__init__(space_id, SpaceType.VIDEO, parent)

        self._frames_to_object_hash_to_annotation_data: defaultdict[int, dict[str, GeometricAnnotationData]] = (
            defaultdict(dict)
        )
        self._frames_to_classification_hash_to_annotation_data: defaultdict[int, dict[str, AnnotationData]] = (
            defaultdict(dict)
        )
        self._classifications_to_ranges: defaultdict[Classification, RangeManager] = defaultdict(RangeManager)

        self._objects_map: dict[str, ObjectInstance] = dict()
        self._classification_map: dict[str, ClassificationInstance] = dict()
        self._object_hash_to_dynamic_answer_manager: dict[str, DynamicAnswerManager] = dict()

        self._layout_key = child_info["layout_key"]
        self._is_readonly = child_info["is_readonly"]
        self._file_name = child_info["file_name"]

        self._number_of_frames: int = number_of_frames
        self._width = width
        self._height = height

    def _is_classification_present_on_frames(
        self, classification: Classification, frames: Frames
    ) -> Tuple[bool, Ranges]:
        if classification.is_global and classification in self._classifications_to_ranges:
            return True, []
        else:
            range_manager = self._classifications_to_ranges.get(classification, RangeManager())
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
                if classification_hash in self._classification_map:
                    existing_classification = self._classification_map[classification_hash]
                    if existing_classification._ontology_classification == classification._ontology_classification:
                        hashes_to_remove.append(classification_hash)

            # Remove the conflicting classification_hash entries
            for hash_to_remove in hashes_to_remove:
                self._frames_to_classification_hash_to_annotation_data[frame].pop(hash_to_remove, None)

    def _place_object(
        self,
        object_instance: ObjectInstance,
        frames: Frames,
        coordinates: GeometricCoordinates,
        *,
        overwrite: bool = False,
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
        is_deleted: Optional[bool] = None,
    ) -> None:
        frame_list = frames_class_to_frames_list(frames)
        self._objects_map[object_instance.object_hash] = object_instance

        if object_instance.object_hash not in self._object_hash_to_dynamic_answer_manager:
            self._object_hash_to_dynamic_answer_manager[object_instance.object_hash] = DynamicAnswerManager(
                object_instance
            )

        object_instance._add_to_space(self)

        check_coordinate_type(coordinates, object_instance._ontology_object, self.parent)

        for frame in frame_list:
            objects_on_frame = self._frames_to_object_hash_to_annotation_data.get(frame)
            if objects_on_frame is None:
                continue

            existing_frame_data = objects_on_frame.get(object_instance.object_hash)

            if overwrite is False and existing_frame_data is not None:
                raise LabelRowError(
                    "Cannot overwrite existing data for a frame. Set 'overwrite' to 'True' to overwrite."
                )

        for frame in frame_list:
            existing_frame_annotation_data = self._get_frame_object_annotation_data(
                object_hash=object_instance.object_hash, frame=frame
            )
            if existing_frame_annotation_data is None:
                existing_frame_annotation_data = GeometricAnnotationData(
                    annotation_metadata=AnnotationMetadata(),
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
                is_deleted=is_deleted,
            )
            existing_frame_annotation_data.coordinates = coordinates

    @property
    def layout_key(self) -> str:
        return self._layout_key

    @property
    def is_readonly(self) -> bool:
        return self._is_readonly

    def place_object(
        self,
        object_instance: ObjectInstance,
        placement: FramePlacement,
        *,
        overwrite: bool = False,
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
        is_deleted: Optional[bool] = None,
    ) -> None:
        self._method_not_supported_for_object_instance_with_frames(object_instance=object_instance)
        self._method_not_supported_for_object_instance_with_dynamic_attributes(object_instance=object_instance)
        frames = placement.frames
        coordinates = placement.coordinates

        self._place_object(
            object_instance=object_instance,
            frames=frames,
            coordinates=coordinates,
            overwrite=overwrite,
            created_at=created_at,
            created_by=created_by,
            last_edited_at=last_edited_at,
            last_edited_by=last_edited_by,
            confidence=confidence,
            manual_annotation=manual_annotation,
            is_deleted=is_deleted,
        )

    def unplace_object(
        self,
        object_instance: ObjectInstance,
        frames: Frames,
    ):
        self._method_not_supported_for_object_instance_with_frames(object_instance=object_instance)

        frame_list = frames_class_to_frames_list(frames)

        # Remove all dynamic answers from these frames
        self._remove_all_answers_from_frames(object_instance, frame_list)

        # TODO: What if all frames are unplaced?
        # Need to remove from objects_map
        # Also need to remove from object_hash_to_dynamic_answer map
        for frame in frame_list:
            self._frames_to_object_hash_to_annotation_data[frame].pop(object_instance.object_hash)

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

        # Only set answer on frames where object exists
        # TODO: Should we throw an error here instead?
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
        dynamic_answer_manager = self._object_hash_to_dynamic_answer_manager.get(object_instance.object_hash)
        if dynamic_answer_manager is None:
            raise LabelRowError("This object does not exist on this space.")

        if not attribute.dynamic:
            raise LabelRowError("This method should only be used for dynamic attributes.")

        return dynamic_answer_manager.get_answer(attribute, filter_answer, filter_frames=frames)

    def place_classification(
        self,
        classification: ClassificationInstance,
        placement: Frames,
        *,
        overwrite: bool = False,
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
        is_deleted: Optional[bool] = None,
    ) -> None:
        self._method_not_supported_for_classification_instance_with_frames(classification_instance=classification)

        frame_list = frames_class_to_frames_list(placement)
        self._classification_map[classification.classification_hash] = classification
        classification._add_to_space(self)

        is_present, conflicting_ranges = self._is_classification_present_on_frames(
            classification._ontology_classification, frame_list
        )

        if is_present and not overwrite:
            location_msg = "globally" if classification.is_global() else f"on the ranges {conflicting_ranges}. "
            raise LabelRowError(
                f"The classification '{classification.classification_hash}' already exists "
                f"{location_msg}"
                f"Set 'overwrite' parameter to True to overwrite."
            )

        # If overwriting, remove conflicting classification entries from other classification instances
        if is_present and overwrite:
            self._remove_conflicting_classifications_from_frames(
                classification=classification,
                conflicting_ranges=conflicting_ranges,
            )

        for frame in frame_list:
            existing_frame_classification_annotation_data = self._get_frame_classification_annotation_data(
                classification_hash=classification.classification_hash, frame=frame
            )

            if existing_frame_classification_annotation_data is None:
                existing_frame_classification_annotation_data = AnnotationData(
                    annotation_metadata=AnnotationMetadata(),
                )

                self._frames_to_classification_hash_to_annotation_data[frame][classification.classification_hash] = (
                    existing_frame_classification_annotation_data
                )

            existing_frame_classification_annotation_data.annotation_metadata.update_from_optional_fields(
                created_at=created_at,
                created_by=created_by,
                last_edited_at=last_edited_at,
                last_edited_by=last_edited_by,
                confidence=confidence,
                manual_annotation=manual_annotation,
                is_deleted=is_deleted,
            )

        range_manager = RangeManager(frame_class=frame_list)
        ranges_to_add = range_manager.get_ranges()

        existing_range_manager = self._classifications_to_ranges.get(classification._ontology_classification)
        if existing_range_manager is None:
            self._classifications_to_ranges[classification._ontology_classification] = range_manager
        else:
            existing_range_manager.add_ranges(ranges_to_add)

    def unplace_classification(
        self,
        classification: ClassificationInstance,
        frames: Frames,
    ):
        self._method_not_supported_for_classification_instance_with_frames(classification_instance=classification)
        frame_list = frames_class_to_frames_list(frames)
        # TODO: What if all frames are unplaaced?
        for frame in frame_list:
            self._frames_to_classification_hash_to_annotation_data[frame].pop(classification.classification_hash)

        range_manager = RangeManager(frame_class=frames)
        ranges_to_remove = range_manager.get_ranges()

        classification_range_manager = self._classifications_to_ranges.get(classification._ontology_classification)
        if classification_range_manager is not None:
            classification_range_manager.remove_ranges(ranges_to_remove)

    def _get_object_annotation_on_frame(self, object_hash: str, frame: int = 0) -> GeometricFrameObjectAnnotation:
        return GeometricFrameObjectAnnotation(space=self, object_instance=self._objects_map[object_hash], frame=frame)

    def get_object_annotations(
        self, filter_objects: Optional[list[str]] = None
    ) -> list[GeometricFrameObjectAnnotation]:
        res: list[GeometricFrameObjectAnnotation] = []

        for frame, obj in dict(sorted(self._frames_to_object_hash_to_annotation_data.items())).items():
            for obj_hash, annotation in obj.items():
                if filter_objects is None or obj_hash in filter_objects:
                    res.append(self._get_object_annotation_on_frame(object_hash=obj_hash, frame=frame))

        return res

    def get_classification_annotations(
        self, filter_classifications: Optional[list[str]] = None
    ) -> list[FrameClassificationAnnotation]:
        res: list[FrameClassificationAnnotation] = []

        for frame, classification in dict(
            sorted(self._frames_to_classification_hash_to_annotation_data.items())
        ).items():
            for classification_hash, annotation in classification.items():
                if filter_classifications is None or classification_hash in filter_classifications:
                    res.append(
                        FrameClassificationAnnotation(
                            space=self,
                            classification_instance=self._classification_map[classification_hash],
                            frame=frame,
                        )
                    )

        return res

    def get_objects(self) -> list[ObjectInstance]:
        return list(self._objects_map.values())

    def get_classifications(self) -> list[ClassificationInstance]:
        return list(self._classification_map.values())

    def remove_object(self, object_hash: str) -> Optional[ObjectInstance]:
        object_instance = self._objects_map.pop(object_hash, None)

        if object_instance is not None:
            object_instance._remove_from_space(self.space_id)
            self._object_hash_to_dynamic_answer_manager.pop(object_instance.object_hash)

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

    def remove_classification(self, classification_hash: str) -> Optional[ClassificationInstance]:
        classification_instance = self._classification_map.pop(classification_hash, None)

        if classification_instance is not None:
            classification_instance._remove_from_space(self.space_id)
            for frame, classification in self._frames_to_classification_hash_to_annotation_data.items():
                if classification_hash in classification:
                    classification.pop(classification_hash)

        return classification_instance

    """INTERNAL METHODS FOR DESERDE"""

    def _create_new_object_from_frame_object_dict(self, frame_object_label: FrameObject) -> ObjectInstance:
        from encord.objects.ontology_object import Object, ObjectInstance

        ontology = self.parent._ontology.structure
        feature_hash = frame_object_label["featureHash"]
        object_hash = frame_object_label["objectHash"]
        label_class = ontology.get_child_by_hash(feature_hash, type_=Object)
        return ObjectInstance(ontology_object=label_class, object_hash=object_hash)

    def _create_new_classification_from_frame_label_dict(
        self, frame_classification_label: FrameClassification, classification_answers: dict
    ) -> ClassificationInstance:
        from encord.objects import Classification, ClassificationInstance

        ontology = self.parent._ontology.structure
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
        self.parent._add_static_answers_from_dict(new_classification_instance, answers_dict)

        return new_classification_instance

    def _get_frame_object_annotation_data(self, object_hash: str, frame: int) -> Optional[GeometricAnnotationData]:
        object_to_frame_annotation_data = self._frames_to_object_hash_to_annotation_data.get(frame)
        if object_to_frame_annotation_data is None:
            return None
        else:
            return object_to_frame_annotation_data.get(object_hash)

    def _get_frame_classification_annotation_data(
        self, classification_hash: str, frame: int
    ) -> Optional[AnnotationData]:
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
            d_opt = answer.to_encord_dict(ranges, spaceId=self.space_id)
            if d_opt is not None:
                ret.append(cast(DynamicAttributeObject, d_opt))
        return ret

    def _to_encord_object(
        self,
        object_instance: ObjectInstance,
        frame_object_annotation_data: GeometricAnnotationData,
    ) -> FrameObject:
        from encord.objects.ontology_object import Object

        ontology_hash = object_instance._ontology_object.feature_node_hash
        ontology_object = self.parent._ontology.structure.get_child_by_hash(ontology_hash, type_=Object)

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
        frame_classification_annotation_data: AnnotationData,
    ) -> FrameClassification:
        from encord.objects import Classification
        from encord.objects.attributes import Attribute

        ontology_hash = classification_instance._ontology_classification.feature_node_hash
        ontology_classification = self.parent._ontology.structure.get_child_by_hash(ontology_hash, type_=Classification)

        attribute_hash = classification_instance.ontology_item.attributes[0].feature_node_hash
        attribute = self.parent._ontology.structure.get_child_by_hash(attribute_hash, type_=Attribute)

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
            space_classification = self._classification_map[classification_hash]
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

    def _to_object_answers(self) -> dict[str, ObjectAnswer]:
        ret: dict[str, ObjectAnswer] = {}
        for object_instance in self._objects_map.values():
            all_static_answers = self.parent._get_all_static_answers(object_instance)
            object_index_element: ObjectAnswer = {
                "classifications": list(reversed(all_static_answers)),
                "objectHash": object_instance.object_hash,
            }
            ret[object_instance.object_hash] = object_index_element

        return ret

    def _to_classification_answers(self) -> dict[str, ClassificationAnswer]:
        ret: dict[str, ClassificationAnswer] = {}
        for classification_instance in self._classification_map.values():
            all_static_answers = classification_instance.get_all_static_answers()
            classifications = [
                cast(AttributeDict, answer.to_encord_dict()) for answer in all_static_answers if answer.is_answered()
            ]
            classification_index_element: ClassificationAnswer = {
                "classifications": classifications,
                "classificationHash": classification_instance.classification_hash,
                "featureHash": classification_instance.feature_hash,
            }

            ret[classification_instance.classification_hash] = classification_index_element

        return ret

    def _parse_space_dict(
        self,
        space_info: SpaceInfo,
        object_answers: dict[str, ObjectAnswer],
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

            for space in self.parent._space_map.values():
                object_instance = space._objects_map.get(object_hash)
                if object_instance is not None:
                    break

            if object_instance is None:
                object_instance = self._create_new_object_from_frame_object_dict(frame_object_label=obj)

            coordinates = get_geometric_coordinates_from_frame_object(frame_object_label=obj)
            object_frame_instance_info = AnnotationMetadata.from_dict(obj)
            self.place_object(
                object_instance=object_instance,
                placement=FramePlacement(
                    coordinates=coordinates,
                    frames=frame,
                ),
                created_at=object_frame_instance_info.created_at,
                created_by=object_frame_instance_info.created_by,
                last_edited_at=object_frame_instance_info.last_edited_at,
                last_edited_by=object_frame_instance_info.last_edited_by,
                manual_annotation=object_frame_instance_info.manual_annotation,
                confidence=object_frame_instance_info.confidence,
                # is_deleted=object_frame_instance_info.is_deleted,
            )

        # Process classifications
        for classification in frame_label["classifications"]:
            classification_hash = classification["classificationHash"]

            classification_instance = None
            for space in self.parent._space_map.values():
                classification_instance = space._classifications_map.get(classification_hash)
                if classification_instance is not None:
                    break

            if classification_instance is None:
                classification_instance = self._create_new_classification_from_frame_label_dict(
                    frame_classification_label=classification,
                    classification_answers=classification_answers,
                )

            classification_frame_instance_info = AnnotationMetadata.from_dict(classification)
            self.place_classification(
                classification=classification_instance,
                placement=frame,
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
            info={
                "is_readonly": self._is_readonly,
                "layout_key": self._layout_key,
                "file_name": self._file_name,
            },
        )
