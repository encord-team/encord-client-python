from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, List, Literal, Optional, Union, cast

from encord.common.range_manager import RangeManager
from encord.common.time_parser import format_datetime_to_long_string, format_datetime_to_long_string_optional
from encord.constants.enums import DataType, SpaceType
from encord.exceptions import LabelRowError
from encord.objects import ClassificationInstance
from encord.objects.frames import Range, Ranges
from encord.objects.ontology_object_instance import ObjectInstance
from encord.objects.spaces.annotation.base_annotation import AnnotationData, AnnotationMetadata
from encord.objects.spaces.annotation.range_annotation import (
    RangeClassificationAnnotation,
    RangeObjectAnnotation,
    RangeObjectAnnotationData,
)
from encord.objects.spaces.base_space import Space
from encord.objects.spaces.types import SpaceInfo
from encord.objects.types import (
    BaseFrameObject,
    ClassificationAnswer,
    FrameClassification,
    LabelBlob,
    ObjectAnswerForNonGeometric,
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
        self._object_hash_to_annotation_data: dict[str, RangeObjectAnnotationData] = dict()
        self._classification_hash_to_annotation_data: dict[str, AnnotationData] = dict()

        # Since we can only have one classification of a particular class, this keeps track to make sure we don't add duplicates
        self._classification_ontologies: set[str] = set()

    @abstractmethod
    def _are_ranges_valid(self, ranges: Ranges) -> None:
        pass

    def _get_start_and_end_of_ranges(self, ranges: Ranges) -> tuple[int, int]:
        if len(ranges) == 0:
            raise LabelRowError("The array of ranges is empty. Please specify at least one range.")

        range_manager = RangeManager(ranges)

        sorted_ranges = range_manager.get_ranges()
        start_of_range = sorted_ranges[0].start
        end_of_range = sorted_ranges[-1].end

        return start_of_range, end_of_range

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
        self._objects_map[object_instance.object_hash] = object_instance
        object_instance._add_to_space(self)

        if isinstance(ranges, Range):
            ranges = [ranges]

        self._are_ranges_valid(ranges)

        existing_annotation_data = self._object_hash_to_annotation_data.get(object_instance.object_hash)
        has_overlap = False

        if existing_annotation_data is not None:
            overlapping_ranges = existing_annotation_data.range_manager.intersection(ranges)
            has_overlap = len(overlapping_ranges) > 0
            if has_overlap and on_overlap == "error":
                raise LabelRowError(
                    f"Annotations already exist on the ranges {overlapping_ranges}. "
                    "Set the 'on_overlap' parameter to 'merge' to add the object instance to the new ranges while keeping existing annotations. "
                    "Set the 'on_overlap' parameter to 'replace' to remove object instance from existing ranges before adding it to the new ranges."
                )

        if existing_annotation_data is None:
            existing_annotation_data = RangeObjectAnnotationData(
                annotation_metadata=AnnotationMetadata(),
                range_manager=RangeManager(),
            )

            self._object_hash_to_annotation_data[object_instance.object_hash] = existing_annotation_data

        existing_annotation_data.annotation_metadata.update_from_optional_fields(
            created_at=created_at,
            created_by=created_by,
            last_edited_at=last_edited_at,
            last_edited_by=last_edited_by,
            confidence=confidence,
            manual_annotation=manual_annotation,
        )

        if has_overlap:
            if on_overlap == "merge":
                existing_annotation_data.range_manager.add_ranges(ranges)
            elif on_overlap == "replace":
                existing_annotation_data.range_manager.clear_ranges()
                existing_annotation_data.range_manager.add_ranges(ranges)
        else:
            existing_annotation_data.range_manager.add_ranges(ranges)

    def remove_object_instance_from_range(self, object: ObjectInstance, ranges: Ranges | Range) -> None:
        if isinstance(ranges, Range):
            ranges = [ranges]

        self._object_hash_to_annotation_data[object.object_hash].range_manager.remove_ranges(ranges)

    def put_classification_instance(
        self,
        classification_instance: ClassificationInstance,
        *,
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
    ) -> None:
        is_classification_instance_present = classification_instance.classification_hash in self._classifications_map
        is_classification_of_same_ontology_present = (
            classification_instance._ontology_classification.feature_node_hash in self._classification_ontologies
        )

        if is_classification_instance_present:
            raise LabelRowError(f"The classification '{classification_instance.classification_hash}' already exists.")

        if is_classification_of_same_ontology_present:
            raise LabelRowError(
                f"A classification instance for the classification with feature hash '{classification_instance._ontology_classification.feature_node_hash}' already exists."
            )

        self._classifications_map[classification_instance.classification_hash] = classification_instance
        classification_instance._add_to_space(self)

        existing_annotation_data = self._classification_hash_to_annotation_data.get(
            classification_instance.classification_hash
        )
        if existing_annotation_data is None:
            existing_annotation_data = AnnotationData(
                annotation_metadata=AnnotationMetadata(),
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

    def get_object_instance_annotations(
        self, filter_object_instances: Optional[list[str]] = None
    ) -> list[RangeObjectAnnotation]:
        res: list[RangeObjectAnnotation] = []

        for obj_hash, annotation in self._object_hash_to_annotation_data.items():
            if filter_object_instances is None or obj_hash in filter_object_instances:
                res.append(RangeObjectAnnotation(space=self, object_instance=self._objects_map[obj_hash]))

        return res

    def get_classification_instance_annotations(
        self, filter_classification_instances: Optional[list[str]] = None
    ) -> list[RangeClassificationAnnotation]:
        res: list[RangeClassificationAnnotation] = []

        for classification_hash, annotation_data in self._classification_hash_to_annotation_data.items():
            if filter_classification_instances is None or classification_hash in filter_classification_instances:
                res.append(
                    RangeClassificationAnnotation(
                        space=self,
                        classification_instance=self._classifications_map[classification_hash],
                    )
                )

        return res

    def get_object_instances(self) -> list[ObjectInstance]:
        return list(self._objects_map.values())

    def get_classification_instances(self) -> list[ClassificationInstance]:
        return list(self._classifications_map.values())

    def remove_object_instance(self, object_hash: str) -> Optional[ObjectInstance]:
        object_instance = self._objects_map.pop(object_hash, None)
        self._object_hash_to_annotation_data.pop(object_hash)

        if object_instance is not None:
            object_instance._remove_from_space(self.space_id)

        return object_instance

    def remove_classification_instance(self, classification_hash: str) -> Optional[ClassificationInstance]:
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

    def _parse_space_dict(
        self,
        space_info: SpaceInfo,
        object_answers: dict[str, ObjectAnswerForNonGeometric],
        classification_answers: dict,
    ) -> None:
        pass
        """Parse object and classification answers, and populate object and classification instances."""
        # for object_answer in object_answers.values():
        #     ranges_in_object_answer = object_answer["range"] if object_answer["range"] is not None else []
        #     ranges = [Range(range[0], range[1]) for range in ranges_in_object_answer]
        # if self.space_type == SpaceType.TEXT:
        #     object_instance = self.parent._create_new_object_instance_with_ranges(
        #         object_answer, ranges, DataType.PLAIN_TEXT
        #     )
        #     frame_info_dict = {k: v for k, v in object_answer.items() if v is not None}
        #     frame_info_dict.setdefault("confidence", 1.0)  # confidence sometimes not present.
        #     object_frame_instance_info = AnnotationMetadata.from_dict(frame_info_dict)
        #
        #     self.place_object(
        #         object=object_instance,
        #         ranges=ranges,
        #         created_at=object_frame_instance_info.created_at,
        #         created_by=object_frame_instance_info.created_by,
        #         last_edited_at=object_frame_instance_info.last_edited_at,
        #         last_edited_by=object_frame_instance_info.last_edited_by,
        #         manual_annotation=object_frame_instance_info.manual_annotation,
        #         reviews=object_frame_instance_info.reviews,
        #         confidence=object_frame_instance_info.confidence,
        #     )

        #     object_instance = self._create_new_object(
        #         object_hash=object_answer["objectHash"],
        #         feature_hash=object_answer["featureHash"],
        #     )
        #
        #     frame_info_dict = {k: v for k, v in object_answer.items() if v is not None}
        #     frame_info_dict.setdefault("confidence", 1.0)  # confidence sometimes not present.
        #     frame_object_dict = cast(BaseFrameObject, frame_info_dict)
        #     object_frame_instance_info = AnnotationMetadata.from_dict(frame_object_dict)
        #
        #     self.put_object_instance(
        #         object_instance=object_instance,
        #         ranges=ranges,
        #         created_at=object_frame_instance_info.created_at,
        #         created_by=object_frame_instance_info.created_by,
        #         last_edited_at=object_frame_instance_info.last_edited_at,
        #         last_edited_by=object_frame_instance_info.last_edited_by,
        #         manual_annotation=object_frame_instance_info.manual_annotation,
        #         confidence=object_frame_instance_info.confidence,
        #     )
        #
        #     answer_list = object_answer["classifications"]
        #     object_instance.set_answer_from_list(answer_list)
        #
        # else:
        #     raise ValueError(f"Space type {self.space_type} is invalid for this space.")

        # for classification_answer in classification_answers.values():
        #     classification_instance = self._label_row._create_new_classification_instance_with_ranges(
        #         classification_answer
        #     )
        #     annotation_metadata = AnnotationMetadata.from_dict(classification_answer)
        #
        #     # TODO: Need to use global classifications here
        #     self.put_classification_instance(
        #         classification_instance=classification_instance,
        #         created_at=annotation_metadata.created_at,
        #         created_by=annotation_metadata.created_by,
        #         confidence=annotation_metadata.confidence,
        #         manual_annotation=annotation_metadata.manual_annotation,
        #         last_edited_at=annotation_metadata.last_edited_at,
        #         last_edited_by=annotation_metadata.last_edited_by,
        #     )

    def _build_labels_dict(self) -> dict[str, LabelBlob]:
        """For range-based annotations, labels are stored in objects/classifications index"""
        return {}

    def _to_object_answers(self) -> dict[str, ObjectAnswerForNonGeometric]:
        ret: dict[str, ObjectAnswerForNonGeometric] = {}

        for obj in self.get_object_instances():
            all_static_answers = self._label_row._get_all_static_answers(obj)
            annotation = self._object_hash_to_annotation_data[obj.object_hash]
            annotation_metadata = annotation.annotation_metadata
            object_index_element: ObjectAnswerForNonGeometric = {
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
                "shape": obj.ontology_item.shape.value,
                "value": _lower_snake_case(obj.ontology_item.name),
                "range": [[range.start, range.end] for range in annotation.range_manager.get_ranges()],
            }

            ret[obj.object_hash] = object_index_element

        return ret

    def _to_classification_answers(self) -> dict[str, ClassificationAnswer]:
        ret: dict[str, ClassificationAnswer] = {}
        for classification in self.get_classification_instances():
            all_static_answers = classification.get_all_static_answers()
            annotation = self._classification_hash_to_annotation_data[classification.classification_hash]
            annotation_metadata = annotation.annotation_metadata
            classifications = [answer.to_encord_dict() for answer in all_static_answers if answer.is_answered()]

            classification_index_element: ClassificationAnswer = {
                "classifications": list(reversed(classifications)),
                "classificationHash": classification.classification_hash,
                "featureHash": classification.feature_hash,
                "range": [],
                "createdBy": annotation_metadata.created_by,
                "createdAt": format_datetime_to_long_string_optional(annotation_metadata.created_at),
                "lastEditedBy": annotation_metadata.last_edited_by,
                "lastEditedAt": format_datetime_to_long_string_optional(annotation_metadata.last_edited_at),
                "manualAnnotation": annotation_metadata.manual_annotation,
            }

            ret[classification.classification_hash] = classification_index_element

        return ret
