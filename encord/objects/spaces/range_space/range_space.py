from __future__ import annotations

import logging
from abc import abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Literal, Optional, Union, cast

from encord.common.range_manager import RangeManager
from encord.common.time_parser import format_datetime_to_long_string, format_datetime_to_long_string_optional
from encord.exceptions import LabelRowError
from encord.objects import ClassificationInstance, Shape
from encord.objects.frames import Range, Ranges
from encord.objects.ontology_object_instance import ObjectInstance
from encord.objects.spaces.annotation.base_annotation import _AnnotationData, _AnnotationMetadata
from encord.objects.spaces.annotation.range_annotation import (
    _RangeClassificationAnnotation,
    _RangeObjectAnnotation,
)
from encord.objects.spaces.base_space import Space
from encord.objects.types import (
    AttributeDict,
    ClassificationAnswer,
    FrameClassification,
    LabelBlob,
    ObjectAnswer,
    ObjectAnswerForGeometric,
    ObjectAnswerForNonGeometric,
    SpaceRange,
)
from encord.objects.utils import _lower_snake_case

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from encord.objects import Object
    from encord.objects.ontology_labels_impl import LabelRowV2

RangeOverlapStrategy = Union[Literal["error"], Literal["merge"], Literal["replace"]]


class RangeSpace(Space):
    """Abstract base class for spaces that manage one dimensional range-based annotations. (Audio, Text and HTML).
    This class extracts common logic for managing object and classification instances
    across ranges.
    """

    def __init__(self, space_id: str, label_row: LabelRowV2):
        super().__init__(space_id, label_row)
        self._objects_map: dict[str, ObjectInstance] = dict()
        self._classifications_map: dict[str, ClassificationInstance] = dict()
        self._classification_hash_to_annotation_data: dict[str, _AnnotationData] = dict()
        self._object_hash_to_range_manager: dict[str, RangeManager] = dict()

        # Since we can only have one classification of a particular class, this keeps track to make sure we don't add duplicates
        self._classification_ontologies: set[str] = set()

    @abstractmethod
    def _are_ranges_valid(self, ranges: Ranges) -> None:
        pass

    @staticmethod
    def _get_start_and_end_of_ranges(ranges: Ranges) -> tuple[int, int]:
        if len(ranges) == 0:
            raise LabelRowError("The array of ranges is empty. Please specify at least one range.")

        range_manager = RangeManager(ranges)

        sorted_ranges = range_manager.get_ranges()
        start_of_range = sorted_ranges[0].start
        end_of_range = sorted_ranges[-1].end

        return start_of_range, end_of_range

    def get_object_instance_annotations(
        self, filter_object_instances: Optional[list[str]] = None
    ) -> List[_RangeObjectAnnotation]:
        """Get all object instance annotations in the video space.

        Args:
            filter_object_instances: Optional list of object hashes to filter by.
                If provided, only annotations for these objects will be returned.

        Returns:
            List[_GeometricFrameObjectAnnotation]: List of all object annotations across all frames,
                sorted by frame number.
        """
        res: List[_RangeObjectAnnotation] = []

        # Convert to set for O(1) lookup performance
        filter_set = set(filter_object_instances) if filter_object_instances is not None else None

        for obj_hash in self._objects_map.keys():
            # If no filter is provided or if the object_hash is in the filter set
            if filter_set is None or obj_hash in filter_set:
                res.append(self._create_object_annotation(obj_hash))

        return res

    def put_object_instance(
        self,
        object_instance: ObjectInstance,
        ranges: Ranges | Range,
        *,
        on_overlap: RangeOverlapStrategy = "error",
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
    ) -> None:
        """Add an object instance to specific ranges in the space (audio, text, or HTML).

        Args:
            object_instance: The object instance to add to the space.
            ranges: Time ranges where the object should appear. Can be:
                - A single Range object (Range)
                - A list of Range objects for multiple ranges (List[Range])
            on_overlap: Strategy for handling existing annotations on overlapping ranges.
                - "error" (default): Raises an error if annotation already exists on overlapping ranges.
                - "merge": Adds the object to new ranges while keeping existing annotations.
                - "replace": Removes object from existing ranges before adding to new ranges.
            created_at: Optional timestamp when the annotation was created.
            created_by: Optional identifier of who created the annotation.
            last_edited_at: Optional timestamp when the annotation was last edited.
            last_edited_by: Optional identifier of who last edited the annotation.
            confidence: Optional confidence score for the annotation (0.0 to 1.0).
            manual_annotation: Optional flag indicating if this was manually annotated.

        Raises:
            LabelRowError: If ranges are invalid or if annotation already exists when on_overlap="error".
        """
        self._method_not_supported_for_object_instance_with_frames(object_instance=object_instance)
        self._method_not_supported_for_object_instance_with_dynamic_attributes(object_instance=object_instance)

        self._objects_map[object_instance.object_hash] = object_instance
        object_instance._add_to_space(self)

        if isinstance(ranges, Range):
            ranges = [ranges]

        self._are_ranges_valid(ranges)

        existing_annotation_range_manager = self._object_hash_to_range_manager.get(object_instance.object_hash)
        has_overlap = False

        if existing_annotation_range_manager is not None:
            overlapping_ranges = existing_annotation_range_manager.intersection(ranges)
            has_overlap = len(overlapping_ranges) > 0
            if has_overlap and on_overlap == "error":
                raise LabelRowError(
                    f"Annotations already exist on the ranges {overlapping_ranges}. "
                    "Set the 'on_overlap' parameter to 'merge' to add the object instance to the new ranges while keeping existing annotations. "
                    "Set the 'on_overlap' parameter to 'replace' to remove object instance from existing ranges before adding it to the new ranges."
                )
        elif existing_annotation_range_manager is None:
            existing_annotation_range_manager = RangeManager()
            self._object_hash_to_range_manager[object_instance.object_hash] = existing_annotation_range_manager

        object_instance._instance_metadata.update_from_optional_fields(
            created_at=created_at,
            created_by=created_by,
            last_edited_at=last_edited_at,
            last_edited_by=last_edited_by,
            confidence=confidence,
            manual_annotation=manual_annotation,
        )

        if has_overlap:
            if on_overlap == "merge":
                existing_annotation_range_manager.add_ranges(ranges)
            elif on_overlap == "replace":
                existing_annotation_range_manager.clear_ranges()
                existing_annotation_range_manager.add_ranges(ranges)
        else:
            existing_annotation_range_manager.add_ranges(ranges)

    def remove_object_instance_from_range(self, object_instance: ObjectInstance, ranges: Ranges | Range) -> Ranges:
        """Remove an object instance from specific ranges in the space.

        If the object is removed from all ranges, it will be completely removed from the space.

        Args:
            object_instance: The object instance to remove from ranges.
            ranges: Ranges to remove the object from. Can be:
                - A single Range object (Range)
                - A list of Range objects for multiple ranges (List[Range])

        Returns:
            Ranges: List of ranges where the object was actually removed.
                Empty if the object didn't exist on any of the specified ranges.
        """
        if object_instance.object_hash not in self._object_hash_to_range_manager:
            return []

        if isinstance(ranges, Range):
            ranges = [ranges]

        range_manager_for_object = self._object_hash_to_range_manager[object_instance.object_hash]

        # Users might pass in ranges where the object does not actually exist on
        actual_ranges_to_remove = range_manager_for_object.intersection(ranges)
        range_manager_for_object.remove_ranges(actual_ranges_to_remove)

        if len(range_manager_for_object.get_ranges()) == 0:
            self._objects_map.pop(object_instance.object_hash)
            self._object_hash_to_range_manager.pop(object_instance.object_hash)

        return actual_ranges_to_remove

    def put_classification_instance(
        self,
        classification_instance: ClassificationInstance,
        *,
        on_overlap: Union[Literal["error"], Literal["replace"]] = "error",
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
    ) -> None:
        """Add a classification instance to the space (audio, text, or HTML).

        Args:
            classification_instance: The classification instance to add to the space.
            on_overlap: Strategy for handling existing classifications.
                - "error" (default): Raises an error if classification of the same ontology item already exists.
                - "replace": Overwrites existing classifications.
            created_at: Optional timestamp when the annotation was created.
            created_by: Optional identifier of who created the annotation.
            last_edited_at: Optional timestamp when the annotation was last edited.
            last_edited_by: Optional identifier of who last edited the annotation.
            confidence: Optional confidence score for the annotation (0.0 to 1.0).
            manual_annotation: Optional flag indicating if this was manually annotated.

        Raises:
            LabelRowError: If classification already exists when on_overlap="error".
        """
        self._method_not_supported_for_classification_instance_with_frames(
            classification_instance=classification_instance
        )
        is_classification_of_same_ontology_present = (
            classification_instance._ontology_classification.feature_node_hash in self._classification_ontologies
        )

        if is_classification_of_same_ontology_present and on_overlap == "error":
            ontology_classification = classification_instance._ontology_classification
            raise LabelRowError(
                f"Annotation for the classification '{ontology_classification.title}' already exists. "
                "Set the 'on_overlap' parameter to 'replace' to overwrite this annotation."
            )
        elif is_classification_of_same_ontology_present and on_overlap == "replace":
            classification_to_remove = None
            for existing_classification_instance in self._classifications_map.values():
                if (
                    existing_classification_instance._ontology_classification.feature_node_hash
                    == classification_instance._ontology_classification.feature_node_hash
                ):
                    classification_to_remove = existing_classification_instance

            if classification_to_remove is not None:
                self._classifications_map.pop(classification_to_remove.classification_hash)
                self._classification_hash_to_annotation_data.pop(classification_to_remove.classification_hash)

        self._classifications_map[classification_instance.classification_hash] = classification_instance
        classification_instance._add_to_space(self)

        existing_annotation_data = self._classification_hash_to_annotation_data.get(
            classification_instance.classification_hash
        )

        if existing_annotation_data is None:
            existing_annotation_data = _AnnotationData(
                annotation_metadata=_AnnotationMetadata(),
            )

            self._classification_hash_to_annotation_data[classification_instance.classification_hash] = (
                existing_annotation_data
            )

        existing_annotation_data.annotation_metadata.update_from_optional_fields(
            created_at=created_at,
            created_by=created_by,
            last_edited_at=last_edited_at,
            last_edited_by=last_edited_by,
            confidence=confidence,
            manual_annotation=manual_annotation,
        )

        self._classification_ontologies.add(classification_instance._ontology_classification.feature_node_hash)

    def _create_object_annotation(self, obj_hash: str) -> _RangeObjectAnnotation:
        return _RangeObjectAnnotation(space=self, object_instance=self._objects_map[obj_hash])

    def _create_classification_annotation(self, classification_hash: str) -> _RangeClassificationAnnotation:
        return _RangeClassificationAnnotation(
            space=self, classification_instance=self._classifications_map[classification_hash]
        )

    def remove_object_instance(self, object_hash: str) -> Optional[ObjectInstance]:
        """Remove an object instance from all ranges in the space.

        This completely removes the object and all associated data from the space.

        Args:
            object_hash: The hash identifier of the object instance to remove.

        Returns:
            Optional[ObjectInstance]: The removed object instance, or None if the object wasn't found.
        """
        object_instance = self._objects_map.pop(object_hash, None)
        # self._object_hash_to_annotation_data.pop(object_hash)
        self._object_hash_to_range_manager.pop(object_hash)
        if object_instance is not None:
            object_instance._remove_from_space(self.space_id)

        return object_instance

    def remove_classification_instance(self, classification_hash: str) -> Optional[ClassificationInstance]:
        """Remove a classification instance from the space.

        This completely removes the classification and all associated data from the space.

        Args:
            classification_hash: The hash identifier of the classification instance to remove.

        Returns:
            Optional[ClassificationInstance]: The removed classification instance, or None if the classification wasn't found.
        """
        classification_instance = self._classifications_map.pop(classification_hash, None)

        if classification_instance is not None:
            classification_instance._remove_from_space(self.space_id)
            self._classification_hash_to_annotation_data.pop(classification_hash)
            self._classification_ontologies.remove(classification_instance._ontology_classification.feature_node_hash)

        return classification_instance

    def _create_new_classification_from_classification_answer(
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

    def _create_new_object(self, feature_hash: str, object_hash: str) -> ObjectInstance:
        from encord.objects.ontology_object import Object, ObjectInstance

        ontology = self._label_row._ontology.structure
        label_class = ontology.get_child_by_hash(feature_hash, type_=Object)
        return ObjectInstance(ontology_object=label_class, object_hash=object_hash)

    def _build_labels_dict(self) -> dict[str, LabelBlob]:
        """For range-based annotations, labels are stored in objects/classifications index"""
        return {}

    def _to_object_answers(self, existing_object_answers: Dict[str, ObjectAnswer]) -> dict[str, ObjectAnswer]:
        ret: Dict[str, ObjectAnswerForNonGeometric] = {}

        for obj in self.get_object_instances():
            range_manager = self._object_hash_to_range_manager[obj.object_hash]
            annotation_metadata = obj._instance_metadata
            ranges = [[range.start, range.end] for range in range_manager.get_ranges()]
            does_obj_exist = obj.object_hash in existing_object_answers

            if does_obj_exist:
                existing_object_answer = cast(ObjectAnswerForNonGeometric, existing_object_answers[obj.object_hash])
                space_range_to_add: SpaceRange = {"range": ranges, "type": "frame"}
                existing_object_answer["spaces"][self.space_id] = space_range_to_add
            else:
                shape = cast(Union[Literal[Shape.TEXT], Literal[Shape.AUDIO]], obj.ontology_item.shape.value)
                all_static_answers = self._label_row._get_all_static_answers(obj)

                object_answer: ObjectAnswerForNonGeometric = {
                    "classifications": list(reversed(all_static_answers)),
                    "objectHash": obj.object_hash,
                    "createdBy": annotation_metadata.created_by,
                    "createdAt": format_datetime_to_long_string(annotation_metadata.created_at),
                    "lastEditedAt": format_datetime_to_long_string(annotation_metadata.last_edited_at),
                    "lastEditedBy": annotation_metadata.last_edited_by,
                    "manualAnnotation": annotation_metadata.manual_annotation,
                    "featureHash": obj.feature_hash,
                    "name": obj.ontology_item.name,
                    "color": obj.ontology_item.color,
                    "shape": shape,
                    "value": _lower_snake_case(obj.ontology_item.name),
                    "range": [],
                    "spaces": {self.space_id: {"range": ranges, "type": "frame"}},
                }

                ret[obj.object_hash] = object_answer

        return cast(dict[str, ObjectAnswer], ret)

    def _to_classification_answers(
        self, existing_classification_answers: dict[str, ClassificationAnswer]
    ) -> dict[str, ClassificationAnswer]:
        ret: dict[str, ClassificationAnswer] = {}

        for classification in self.get_classification_instances():
            does_classification_exist = classification.classification_hash in existing_classification_answers

            if does_classification_exist:
                existing_classification_answer = existing_classification_answers[classification.classification_hash]
                space_range_to_add: SpaceRange = {"range": [], "type": "frame"}
                spaces = existing_classification_answer["spaces"]

                if spaces is None:
                    spaces = {}

                spaces[self.space_id] = space_range_to_add
                ret[classification.classification_hash] = existing_classification_answer
            else:
                all_static_answers = classification.get_all_static_answers()
                annotation = self._classification_hash_to_annotation_data[classification.classification_hash]
                annotation_metadata = annotation.annotation_metadata
                classification_attributes = [
                    answer.to_encord_dict() for answer in all_static_answers if answer.is_answered()
                ]
                classification_attributes_without_none = cast(list[AttributeDict], classification_attributes)

                classification_answer: ClassificationAnswer = {
                    "classifications": list(reversed(classification_attributes_without_none)),
                    "classificationHash": classification.classification_hash,
                    "featureHash": classification.feature_hash,
                    "range": [],
                    "createdBy": annotation_metadata.created_by,
                    "createdAt": format_datetime_to_long_string_optional(annotation_metadata.created_at),
                    "lastEditedBy": annotation_metadata.last_edited_by,
                    "lastEditedAt": format_datetime_to_long_string_optional(annotation_metadata.last_edited_at),
                    "manualAnnotation": annotation_metadata.manual_annotation,
                    "spaces": {self.space_id: {"range": [], "type": "frame"}},
                }

                ret[classification.classification_hash] = classification_answer

        return ret
