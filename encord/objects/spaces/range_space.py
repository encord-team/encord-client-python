from __future__ import annotations

import logging
from abc import ABC
from typing import TYPE_CHECKING, Any, Dict, Optional, TypedDict, Unpack

from encord.common.time_parser import format_datetime_to_long_string_optional
from encord.constants.enums import DataType, SpaceType
from encord.exceptions import LabelRowError
from encord.objects import Classification, ClassificationInstance, Shape
from encord.objects.coordinates import AudioCoordinates, TextCoordinates
from encord.objects.frames import Range, Ranges
from encord.objects.ontology_object_instance import ObjectInstance, SetFramesKwargs
from encord.objects.spaces.base_space import Space
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
        self._objects_map: Dict[str, ObjectInstance] = dict()
        self._classifications_map: Dict[str, ClassificationInstance] = dict()

    def _add_object_instance(self, object_instance: ObjectInstance) -> ObjectInstance:
        self._objects_map[object_instance.object_hash] = object_instance
        object_instance._set_space(self)

        return object_instance

    def _add_classification_instance(self, classification_instance: ClassificationInstance) -> ClassificationInstance:
        self._classifications_map[classification_instance.classification_hash] = classification_instance
        classification_instance._set_space(self)

        return classification_instance

    def _on_set_for_frames(self, frame: int, object_hash: str):
        pass

    def get_object_instances(self) -> list[ObjectInstance]:
        """Get all object instances in this space."""
        return list(self._objects_map.values())

    def get_classification_instances(self) -> list[ClassificationInstance]:
        """Get all classification instances in this space."""
        return list(self._classifications_map.values())

    def remove_object_instance(self, object_hash: str) -> Optional[ObjectInstance]:
        """Remove an object instance from this space by its hash."""
        object_instance = self._objects_map.pop(object_hash, None)

        if object_instance is None:
            logger.warning(f"Object instance {object_hash} not found.")
        else:
            object_instance._set_space(None)

        return object_instance

    def remove_classification_instance(self, classification_hash: str) -> Optional[ClassificationInstance]:
        """Remove a classification instance from this space by its hash."""
        classification_instance = self._classifications_map.pop(classification_hash, None)

        if classification_instance is None:
            logger.warning(f"Classification instance {classification_hash} not found.")
        else:
            classification_instance._set_space(None)

        return classification_instance

    def move_object_instance_from_space(self, object_to_move: ObjectInstance) -> Optional[ObjectInstance]:
        """Move an object instance from another space to this space."""
        original_space = object_to_move._space

        if original_space is None:
            raise LabelRowError("Unable to move object instance, as it currently does not belong to any space.")

        if isinstance(original_space, RangeBasedSpace):
            original_space.remove_object_instance(object_to_move.object_hash)
            self._add_object_instance(object_to_move)
            return object_to_move
        else:
            logger.warning(
                f"Unable to move object instance from space of type {original_space.space_type} to {self.space_type}"
            )
            return None

    def move_classification_instance_from_space(
        self, classification_to_move: ClassificationInstance
    ) -> Optional[ClassificationInstance]:
        """Move a classification instance from another space to this space."""
        original_space = classification_to_move._space

        if original_space is None:
            raise LabelRowError("Unable to move classification instance, as it currently does not belong to any space.")

        if isinstance(original_space, RangeBasedSpace):
            original_space.remove_classification_instance(classification_to_move.classification_hash)
            self._add_classification_instance(classification_to_move)
            return classification_to_move
        else:
            logger.warning(
                f"Unable to move classification instance from space of type {original_space.space_type} to {self.space_type}"
            )
            return None

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
            elif self.space_type == SpaceType.AUDIO:
                object_instance = self.parent._create_new_object_instance_with_ranges(
                    object_answer, ranges, DataType.AUDIO
                )
            else:
                raise ValueError(f"Space type {self.space_type} is invalid for this space.")

            self._add_object_instance(object_instance)

        for classification_answer in classification_answers.values():
            classification_instance = self.parent._create_new_classification_instance_with_ranges(classification_answer)
            self._add_classification_instance(classification_instance)

    def _build_labels_dict(self) -> dict[str, LabelBlob]:
        """For range-based annotations, labels are stored in objects/classifications index"""
        return {}

    def _to_object_answers(self) -> dict[str, RangeObjectIndex]:
        ret: dict[str, RangeObjectIndex] = {}
        for obj in self.get_object_instances():
            all_static_answers = self.parent._get_all_static_answers(obj)
            annotation = obj.get_annotation(0)
            object_index_element: RangeObjectIndex = {
                "classifications": list(reversed(all_static_answers)),
                "objectHash": obj.object_hash,
                "createdBy": annotation.created_by,
                "createdAt": format_datetime_to_long_string_optional(annotation.created_at),
                "lastEditedBy": annotation.last_edited_by,
                "lastEditedAt": format_datetime_to_long_string_optional(annotation.last_edited_at),
                "manualAnnotation": annotation.manual_annotation,
                "featureHash": obj.feature_hash,
                "name": obj.ontology_item.name,
                "color": obj.ontology_item.color,
                "shape": obj.ontology_item.shape.value,
                "value": _lower_snake_case(obj.ontology_item.name),
                "range": [[range.start, range.end] for range in obj.range_list],
            }

            ret[obj.object_hash] = object_index_element

        return ret

    def _to_classification_answers(self) -> dict[str, RangeClassificationIndex]:
        ret: dict[str, RangeClassificationIndex] = {}
        for classification in self.get_classification_instances():
            all_static_answers = classification.get_all_static_answers()
            annotation = classification.get_annotations()[0]
            classifications = [answer.to_encord_dict() for answer in all_static_answers if answer.is_answered()]

            classification_index_element: RangeClassificationIndex = {
                "classifications": list(reversed(classifications)),
                "classificationHash": classification.classification_hash,
                "featureHash": classification.feature_hash,
                "range": [],
                "createdBy": annotation.created_by,
                "createdAt": format_datetime_to_long_string_optional(annotation.created_at),
                "lastEditedBy": annotation.last_edited_by,
                "lastEditedAt": format_datetime_to_long_string_optional(annotation.last_edited_at),
                "manualAnnotation": annotation.manual_annotation,
            }

            ret[classification.classification_hash] = classification_index_element

        return ret


class AudioSpace(RangeBasedSpace):
    """Audio space implementation for range-based annotations."""

    def __init__(self, space_id: str, title: str, parent: LabelRowV2, duration_ms: int):
        super().__init__(space_id, title, SpaceType.AUDIO, parent)
        self._duration_ms = duration_ms
        self._objects_map: Dict[str, ObjectInstance] = dict()
        self._classifications_map: Dict[str, ClassificationInstance] = dict()

    def _to_space_dict(self) -> SpaceInfo:
        labels = self._build_labels_dict()
        return AudioSpaceInfo(
            space_type=self.space_type,
            duration_ms=self._duration_ms,
            labels=labels,
        )

    def add_object_instance(self, obj: Object, range: Range, **kwargs: Unpack[SetFramesKwargs]):
        """Add an object instance to the audio space."""
        object_instance = obj.create_instance()
        object_instance.set_for_frames(coordinates=AudioCoordinates(range=[range]), frames=0, **kwargs)
        return self._add_object_instance(object_instance)

    def add_classification_instance(self, classification: Classification, **kwargs: Unpack[SetFramesKwargs]):
        """Add an object instance to the audio space."""
        classification_instance = classification.create_instance(range_only=True)
        classification_instance.set_for_frames(frames=0, **kwargs)
        return self._add_classification_instance(classification_instance)


class TextSpace(RangeBasedSpace):
    """Text space implementation for range-based annotations."""

    def __init__(self, space_id: str, title: str, parent: LabelRowV2, number_of_characters: int):
        super().__init__(space_id, title, SpaceType.TEXT, parent)
        self._number_of_characters = number_of_characters
        self._objects_map: Dict[str, ObjectInstance] = dict()
        self._classifications_map: Dict[str, ClassificationInstance] = dict()

    def _to_space_dict(self) -> TextSpaceInfo:
        labels = self._build_labels_dict()
        return TextSpaceInfo(
            space_type=self.space_type,
            number_of_characters=self._number_of_characters,
            labels=labels,
        )

    def add_object_instance(self, obj: Object, range: Range, **kwargs: Unpack[SetFramesKwargs]):
        """Add an object instance to the audio space."""
        object_instance = obj.create_instance()
        object_instance.set_for_frames(coordinates=TextCoordinates(range=[range]), frames=0, **kwargs)
        return self._add_object_instance(object_instance)

    def add_classification_instance(self, classification: Classification, **kwargs: Unpack[SetFramesKwargs]):
        """Add an object instance to the audio space."""
        classification_instance = classification.create_instance(range_only=True)
        classification_instance.set_for_frames(frames=0, **kwargs)
        return self._add_classification_instance(classification_instance)
