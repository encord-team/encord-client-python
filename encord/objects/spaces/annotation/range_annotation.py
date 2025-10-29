from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from encord.common.range_manager import RangeManager
from encord.exceptions import LabelRowError
from encord.objects.frames import Ranges
from encord.objects.spaces.annotation.base_annotation import (
    AnnotationData,
    ClassificationAnnotation,
    ObjectAnnotation,
)
from encord.objects.spaces.space_entity import SpaceClassification, SpaceObject

if TYPE_CHECKING:
    from encord.objects.spaces.range_space import RangeBasedSpace


@dataclass
class RangeAnnotationData(AnnotationData):
    """Annotation Data for 1D objects."""

    range_manager: RangeManager


class RangeObjectAnnotation(ObjectAnnotation):
    """Annotations for 1D objects (e.g. Audio and Text)."""

    def __init__(self, space: RangeBasedSpace, object_instance: SpaceObject):
        super().__init__(space, object_instance)
        self._space = space

    @property
    def ranges(self) -> Ranges:
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().range_manager.get_ranges()

    # TODO: Should we allow setting of ranges?

    def _get_annotation_data(self) -> RangeAnnotationData:
        return self._space._object_hash_to_annotation_data[self._object_instance.object_hash]

    def _check_if_annotation_is_valid(self) -> None:
        if self._object_instance.object_hash not in self._space._object_hash_to_annotation_data:
            raise LabelRowError(
                "Trying to use an ObjectInstance.FrameAnnotation for a VideoObjectInstance that is not on the frame"
            )


class RangeClassificationAnnotation(ClassificationAnnotation):
    """Annotations for 1D classifications (e.g. Audio and Text)."""

    def __init__(self, space: RangeBasedSpace, classification: SpaceClassification):
        super().__init__(space, classification)
        self._space = space

    @property
    def ranges(self) -> Ranges:
        return self._get_annotation_data().range_manager.get_ranges()

    # TODO: Should we allow setting of ranges?

    def _get_annotation_data(self) -> RangeAnnotationData:
        return self._space._classification_hash_to_annotation_data[self._classification.classification_hash]

    def _check_if_annotation_is_valid(self) -> None:
        if self._classification.classification_hash not in self._space._classification_hash_to_annotation_data:
            raise LabelRowError(
                "Trying to use an ObjectInstance.FrameAnnotation for a VideoObjectInstance that is not on the frame"
            )
