from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from encord.common.range_manager import RangeManager
from encord.exceptions import LabelRowError
from encord.objects.coordinates import AudioCoordinates, TextCoordinates
from encord.objects.frames import Range, Ranges
from encord.objects.spaces.annotation.base_annotation import (
    _AnnotationData,
    _ClassificationAnnotation,
    _ObjectAnnotation,
)

if TYPE_CHECKING:
    from encord.objects import ClassificationInstance, ObjectInstance, Shape
    from encord.objects.spaces.range_space.range_space import RangeSpace


@dataclass
class _RangeObjectAnnotationData(_AnnotationData):
    """Annotation Data for Range-based objects. Contains a range manager."""

    range_manager: RangeManager


class _RangeObjectAnnotation(_ObjectAnnotation):
    """Annotations for range-based modalities (e.g. Text, Audio)."""

    def __init__(self, space: RangeSpace, object_instance: ObjectInstance):
        super().__init__(space, object_instance)
        self._space: RangeSpace = space

    @property
    def frame(self) -> int:
        """This field is deprecated. It is only here for backwards compatibility. It always returns 0."""
        return 0

    @property
    def space(self) -> RangeSpace:
        return self._space

    @property
    def ranges(self) -> Ranges:
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().range_manager.get_ranges()

    @ranges.setter
    def ranges(self, ranges: Union[Range, Ranges]) -> None:
        self._check_if_annotation_is_valid()
        new_range_manager = RangeManager(ranges)
        self._space._object_hash_to_range_manager[self._object_instance.object_hash] = new_range_manager

    @property
    def coordinates(self) -> AudioCoordinates | TextCoordinates:
        from encord.objects import Shape

        """This field is deprecated. It is only here for backwards compatibility. Use .ranges instead."""
        self._check_if_annotation_is_valid()

        ranges = self._get_annotation_data().range_manager.get_ranges()
        if self._object_instance._ontology_object.shape == Shape.TEXT:
            return TextCoordinates(range=ranges)
        elif self._object_instance._ontology_object.shape == Shape.AUDIO:
            return AudioCoordinates(range=ranges)
        else:
            raise LabelRowError("This annotation is on an object that is not range-based.")

    @coordinates.setter
    def coordinates(self, coordinates: AudioCoordinates | TextCoordinates) -> None:
        """This field is deprecated. It is only here for backwards compatibility. Use .ranges instead."""
        self._check_if_annotation_is_valid()
        new_range_manager = RangeManager(frame_class=coordinates.range)
        self._space._object_hash_to_range_manager[self._object_instance.object_hash] = new_range_manager

    def _get_annotation_data(self) -> _RangeObjectAnnotationData:
        return _RangeObjectAnnotationData(
            annotation_metadata=self._object_instance._instance_metadata,
            range_manager=self._space._object_hash_to_range_manager[self._object_instance.object_hash],
        )

    def _check_if_annotation_is_valid(self) -> None:
        if self._object_instance.object_hash not in self._space._object_hash_to_range_manager:
            raise LabelRowError(
                "Trying to use a RangeObjectAnnotation for an ObjectInstance that is not on this space."
            )


class _RangeClassificationAnnotation(_ClassificationAnnotation):
    """Annotations for multi-frame classifications (e.g. Video)."""

    def __init__(self, space: RangeSpace, classification_instance: ClassificationInstance):
        super().__init__(space, classification_instance)
        self._space: RangeSpace = space

    @property
    def space(self) -> RangeSpace:
        return self._space

    @property
    def frame(self) -> int:
        """This field is deprecated. It is only here for backwards compatibility. It always returns 0."""
        return 0

    def _get_annotation_data(self) -> _AnnotationData:
        return self._space._classification_hash_to_annotation_data[self._classification_instance.classification_hash]

    def _check_if_annotation_is_valid(self) -> None:
        if self._classification_instance.classification_hash not in self._space._classification_hash_to_annotation_data:
            raise LabelRowError("This annotation is not available on this space.")
