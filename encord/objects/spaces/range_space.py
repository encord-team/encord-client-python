from __future__ import annotations

import logging
from abc import ABC
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, TypedDict, Unpack

from encord.common.range_manager import RangeManager
from encord.common.time_parser import format_datetime_to_long_string_optional
from encord.constants.enums import DataType, SpaceType
from encord.objects import ClassificationInstance, Shape
from encord.objects.frames import Range, Ranges
from encord.objects.ontology_object_instance import ObjectInstance
from encord.objects.spaces.annotation.base_annotation import AnnotationInfo
from encord.objects.spaces.annotation.range_annotation import (
    RangeAnnotationData,
    RangeClassificationAnnotation,
    RangeObjectAnnotation,
)
from encord.objects.spaces.base_space import Space
from encord.objects.spaces.space_entity import SpaceClassification, SpaceObject
from encord.objects.utils import _lower_snake_case
from encord.orm.label_space import AudioSpaceInfo, BaseSpaceInfo, LabelBlob, SpaceInfo, TextSpaceInfo

logger = logging.getLogger(__name__)


class RangeAnnotationIndex(TypedDict):
    featureHash: str
    classifications: list[dict[str, Any]]
    range: list[list[int]]
    createdBy: Optional[str]
    createdAt: Optional[str]
    lastEditedBy: Optional[str]
    lastEditedAt: Optional[str]
    manualAnnotation: bool


class RangeClassificationIndex(RangeAnnotationIndex):
    classificationHash: str


class RangeObjectIndex(RangeAnnotationIndex):
    objectHash: str
    name: str
    color: str
    shape: Shape
    value: str


if TYPE_CHECKING:
    from encord.objects import Object
    from encord.objects.ontology_labels_impl import LabelRowV2


class RangeBasedSpace(Space, ABC):
    """Abstract base class for spaces that manage one dimensional range-based annotations. (Audio, Text and HTML).

    This class extracts common logic for managing object and classification instances
    across ranges.
    """

    def __init__(self, space_id: str, title: str, space_type: SpaceType, parent: LabelRowV2):
        super().__init__(space_id, title, space_type, parent)
        self._objects_map: dict[str, SpaceObject] = dict()
        self._classifications_map: dict[str, SpaceClassification] = dict()
        self._object_hash_to_annotation_data: dict[str, RangeAnnotationData] = dict()
        self._classification_hash_to_annotation_data: dict[str, RangeAnnotationData] = dict()

    # TODO: Problem here is that its abit confusing because
    # for non-range objects, each frame has their own annotation_info
    # but here, we overwrite the annotation_info for everytime you do place
    def place_object(
        self,
        object: SpaceObject,
        ranges: Ranges | Range,
        *,
        overwrite: bool = False,
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
        reviews: Optional[List[dict]] = None,
        is_deleted: Optional[bool] = None,
    ) -> None:
        self._objects_map[object.object_hash] = object
        object._add_to_space(self)

        if isinstance(ranges, Range):
            ranges = [ranges]

        # TODO: Check overwrites

        existing_frame_annotation_data = self._object_hash_to_annotation_data.get(object.object_hash)
        if existing_frame_annotation_data is None:
            existing_frame_annotation_data = RangeAnnotationData(
                annotation_info=AnnotationInfo(),
                range_manager=RangeManager(),
            )

            self._object_hash_to_annotation_data[object.object_hash] = existing_frame_annotation_data

        existing_frame_annotation_data.annotation_info.update_from_optional_fields(
            created_at=created_at,
            created_by=created_by,
            last_edited_at=last_edited_at,
            last_edited_by=last_edited_by,
            confidence=confidence,
            manual_annotation=manual_annotation,
            reviews=reviews,
            is_deleted=is_deleted,
        )

        existing_frame_annotation_data.range_manager.add_ranges(ranges)

    def place_classification(
        self,
        classification: SpaceClassification,
        ranges: Ranges | Range,
        *,
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
        reviews: Optional[List[dict]] = None,
    ) -> None:
        self._classifications_map[classification.classification_hash] = classification
        classification._add_to_space(self)

        if isinstance(ranges, Range):
            ranges = [ranges]

        # TODO: Check overwrites

        existing_frame_classification_annotation_data = self._classification_hash_to_annotation_data.get(
            classification.classification_hash
        )
        if existing_frame_classification_annotation_data is None:
            existing_frame_classification_annotation_data = RangeAnnotationData(
                annotation_info=AnnotationInfo(),
                range_manager=RangeManager(),
            )

            self._classification_hash_to_annotation_data[classification.classification_hash] = (
                existing_frame_classification_annotation_data
            )

        existing_frame_classification_annotation_data.annotation_info.update_from_optional_fields(
            created_at=created_at,
            created_by=created_by,
            last_edited_at=last_edited_at,
            last_edited_by=last_edited_by,
            confidence=confidence,
            manual_annotation=manual_annotation,
            reviews=reviews,
        )

    def get_object_annotations(self) -> list[RangeObjectAnnotation]:
        res: list[RangeObjectAnnotation] = []

        for obj_hash, annotation in self._object_hash_to_annotation_data.items():
            res.append(RangeObjectAnnotation(space=self, object_instance=self._objects_map[obj_hash]))

        return res

    def get_classification_annotations(self) -> list[RangeClassificationAnnotation]:
        res: list[RangeClassificationAnnotation] = []

        for classification_hash, annotation_data in dict(
            sorted(self._classification_hash_to_annotation_data.items())
        ).items():
            res.append(
                RangeClassificationAnnotation(
                    space=self,
                    classification_instance=self._classifications_map[classification_hash],
                )
            )

        return res

    def get_objects(self) -> list[SpaceObject]:
        return list(self._objects_map.values())

    def get_classifications(self) -> list[SpaceClassification]:
        return list(self._classifications_map.values())

    def remove_space_object(self, object_hash: str) -> Optional[SpaceObject]:
        obj_entity = self._objects_map.pop(object_hash, None)
        self._object_hash_to_annotation_data.pop(object_hash)
        obj_entity._remove_from_space(self)

        return obj_entity

    def remove_space_classification(self, classification_hash: str) -> Optional[SpaceClassification]:
        classification_entity = self._classifications_map.pop(classification_hash, None)
        classification_entity._remove_from_space(self)
        self._classification_hash_to_annotation_data.pop(classification_hash)

        return classification_entity

    def _create_new_space_object_from_object_answers(self, object_answer: dict):
        feature_hash = object_answer["featureHash"]
        object_hash = object_answer["objectHash"]

        label_class = self.parent._ontology.structure.get_child_by_hash(feature_hash, type_=Object)

        frame_info_dict = {k: v for k, v in object_answer.items() if v is not None}
        frame_info_dict.setdefault("confidence", 1.0)  # confidence sometimes not present.
        object_frame_instance_info = AnnotationInfo.from_dict(frame_info_dict)

        object_instance = self.parent.create_space_object(ontology_class=label_class, entity_hash=object_hash)

        self.place_object(
            object=object_instance,
            ranges=object_answer["ranges"],
            created_at=object_frame_instance_info.created_at,
            created_by=object_frame_instance_info.created_by,
            confidence=object_frame_instance_info.confidence,
            manual_annotation=object_frame_instance_info.manual_annotation,
            last_edited_at=object_frame_instance_info.last_edited_at,
            last_edited_by=object_frame_instance_info.last_edited_by,
            reviews=object_frame_instance_info.reviews,
            overwrite=True,
        )

        answer_list = object_answer["classifications"]
        object_instance._object_instance.set_answer_from_list(answer_list)

        return object_instance

    def _parse_space_dict(self, space_info: BaseSpaceInfo, object_answers: dict, classification_answers: dict) -> None:
        """Parse object and classification answers, and populate object and classification instances."""
        for object_answer in object_answers.values():
            ranges: Ranges = []
            for range_elem in object_answer["range"]:
                ranges.append(Range(start=range_elem[0], end=range_elem[1]))

            if self.space_type == SpaceType.TEXT:
                object_instance = self.parent._create_new_object_instance_with_ranges(
                    object_answer, ranges, DataType.PLAIN_TEXT
                )
                space_object = SpaceObject(label_row=self.parent, object_instance=object_instance)
                frame_info_dict = {k: v for k, v in object_answer.items() if v is not None}
                frame_info_dict.setdefault("confidence", 1.0)  # confidence sometimes not present.
                object_frame_instance_info = AnnotationInfo.from_dict(frame_info_dict)

                self.place_object(
                    object=space_object,
                    ranges=ranges,
                    created_at=object_frame_instance_info.created_at,
                    created_by=object_frame_instance_info.created_by,
                    last_edited_at=object_frame_instance_info.last_edited_at,
                    last_edited_by=object_frame_instance_info.last_edited_by,
                    manual_annotation=object_frame_instance_info.manual_annotation,
                    reviews=object_frame_instance_info.reviews,
                    confidence=object_frame_instance_info.confidence,
                )

            elif self.space_type == SpaceType.AUDIO:
                object_instance = self.parent._create_new_object_instance_with_ranges(
                    object_answer, ranges, DataType.AUDIO
                )
                space_object = SpaceObject(label_row=self.parent, object_instance=object_instance)
                frame_info_dict = {k: v for k, v in object_answer.items() if v is not None}
                frame_info_dict.setdefault("confidence", 1.0)  # confidence sometimes not present.
                object_frame_instance_info = AnnotationInfo.from_dict(frame_info_dict)

                self.place_object(
                    object=space_object,
                    ranges=ranges,
                    created_at=object_frame_instance_info.created_at,
                    created_by=object_frame_instance_info.created_by,
                    last_edited_at=object_frame_instance_info.last_edited_at,
                    last_edited_by=object_frame_instance_info.last_edited_by,
                    manual_annotation=object_frame_instance_info.manual_annotation,
                    reviews=object_frame_instance_info.reviews,
                    confidence=object_frame_instance_info.confidence,
                )

            else:
                raise ValueError(f"Space type {self.space_type} is invalid for this space.")

        for classification_answer in classification_answers.values():
            classification_instance = self.parent._create_new_classification_instance_with_ranges(classification_answer)
            classification_instance_info = AnnotationInfo.from_dict(classification_answer)

            space_classification = SpaceClassification(
                label_row=self.parent, classification_instance=classification_instance
            )
            # TODO: Need to use global classifications here
            self.place_classification(
                space_classification,
                ranges=Range(start=0, end=200),
                created_at=classification_instance_info.created_at,
                created_by=classification_instance_info.created_by,
                confidence=classification_instance_info.confidence,
                manual_annotation=classification_instance_info.manual_annotation,
                last_edited_at=classification_instance_info.last_edited_at,
                last_edited_by=classification_instance_info.last_edited_by,
                reviews=classification_instance_info.reviews,
            )

    def _build_labels_dict(self) -> dict[str, LabelBlob]:
        """For range-based annotations, labels are stored in objects/classifications index"""
        return {}

    def _to_object_answers(self) -> dict[str, RangeObjectIndex]:
        ret: dict[str, RangeObjectIndex] = {}
        for obj in self.get_objects():
            all_static_answers = self.parent._get_all_static_answers(obj._object_instance)
            annotation = self._object_hash_to_annotation_data[obj.object_hash]
            annotation_info = annotation.annotation_info
            object_index_element: RangeObjectIndex = {
                "classifications": list(reversed(all_static_answers)),
                "objectHash": obj.object_hash,
                "createdBy": annotation_info.created_by,
                "createdAt": format_datetime_to_long_string_optional(annotation_info.created_at),
                "lastEditedBy": annotation_info.last_edited_by,
                "lastEditedAt": format_datetime_to_long_string_optional(annotation_info.last_edited_at),
                "manualAnnotation": annotation_info.manual_annotation,
                "featureHash": obj._object_instance.feature_hash,
                "name": obj._object_instance.ontology_item.name,
                "color": obj._object_instance.ontology_item.color,
                "shape": obj._object_instance.ontology_item.shape.value,
                "value": _lower_snake_case(obj._object_instance.ontology_item.name),
                "range": [[range.start, range.end] for range in annotation.range_manager.ranges],
            }

            ret[obj.object_hash] = object_index_element

        return ret

    def _to_classification_answers(self) -> dict[str, RangeClassificationIndex]:
        ret: dict[str, RangeClassificationIndex] = {}
        for classification in self.get_classifications():
            all_static_answers = classification._classification_instance.get_all_static_answers()
            annotation = self._classification_hash_to_annotation_data[classification.classification_hash]
            annotation_info = annotation.annotation_info
            classifications = [answer.to_encord_dict() for answer in all_static_answers if answer.is_answered()]

            classification_index_element: RangeClassificationIndex = {
                "classifications": list(reversed(classifications)),
                "classificationHash": classification.classification_hash,
                "featureHash": classification._classification_instance.feature_hash,
                "range": [],
                "createdBy": annotation_info.created_by,
                "createdAt": format_datetime_to_long_string_optional(annotation_info.created_at),
                "lastEditedBy": annotation_info.last_edited_by,
                "lastEditedAt": format_datetime_to_long_string_optional(annotation_info.last_edited_at),
                "manualAnnotation": annotation_info.manual_annotation,
            }

            ret[classification.classification_hash] = classification_index_element

        return ret


class AudioSpace(RangeBasedSpace):
    """Audio space implementation for range-based annotations."""

    def __init__(self, space_id: str, title: str, parent: LabelRowV2, duration_ms: int):
        super().__init__(space_id, title, SpaceType.AUDIO, parent)
        self._duration_ms = duration_ms

    def _to_space_dict(self) -> SpaceInfo:
        labels = self._build_labels_dict()
        return AudioSpaceInfo(
            space_type=SpaceType.AUDIO,
            duration_ms=self._duration_ms,
            labels=labels,
        )


class TextSpace(RangeBasedSpace):
    """Text space implementation for range-based annotations."""

    def __init__(self, space_id: str, title: str, parent: LabelRowV2, number_of_characters: int):
        super().__init__(space_id, title, SpaceType.TEXT, parent)
        self._number_of_characters = number_of_characters

    def _to_space_dict(self) -> TextSpaceInfo:
        labels = self._build_labels_dict()
        return TextSpaceInfo(
            space_type=SpaceType.TEXT,
            number_of_characters=self._number_of_characters,
            labels=labels,
        )
