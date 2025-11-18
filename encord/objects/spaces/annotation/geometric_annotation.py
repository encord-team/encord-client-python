from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from encord.exceptions import LabelRowError
from encord.objects.coordinates import Coordinates, GeometricCoordinates
from encord.objects.spaces.annotation.base_annotation import AnnotationData, ClassificationAnnotation, ObjectAnnotation
from encord.objects.spaces.base_space import FramePlacement, Space

if TYPE_CHECKING:
    from encord.objects import ClassificationInstance, ObjectInstance
    from encord.objects.spaces.image_space import ImageSpace
    from encord.objects.spaces.video_space import VideoSpace


@dataclass
class GeometricAnnotationData(AnnotationData):
    """Annotation Data for 2D objects. Contains coordinates."""

    coordinates: GeometricCoordinates


class GeometricObjectAnnotation(ObjectAnnotation):
    """Annotations for single-frame 2D objects."""

    def __init__(self, space: ImageSpace, object_instance: ObjectInstance):
        super().__init__(space, object_instance)
        self._space: ImageSpace = space

    @property
    def frame(self) -> int:
        return 0

    @property
    def space(self) -> ImageSpace:
        return self._space

    @property
    def coordinates(self) -> GeometricCoordinates:
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().coordinates

    @coordinates.setter
    def coordinates(self, coordinates: GeometricCoordinates) -> None:
        self._check_if_annotation_is_valid()
        self._space._object_hash_to_annotation_data[self._object_instance.object_hash].coordinates = coordinates

    def _get_annotation_data(self) -> GeometricAnnotationData:
        return self._space._object_hash_to_annotation_data[self._object_instance.object_hash]

    def _check_if_annotation_is_valid(self) -> None:
        if self._object_instance.object_hash not in self._space._object_hash_to_annotation_data:
            raise LabelRowError(
                "Trying to use an ObjectInstance.FrameAnnotation for a VideoObjectInstance that is not on the frame"
            )


class GeometricFrameObjectAnnotation(ObjectAnnotation):
    """Annotations for multi-frame geometric object labels (e.g. Video)."""

    def __init__(self, space: VideoSpace, object_instance: ObjectInstance, frame: int):
        super().__init__(space, object_instance)
        self._space: VideoSpace = space
        self._frame = frame

    @property
    def space(self) -> VideoSpace:
        return self._space

    @property
    def frame(self) -> int:
        return self._frame

    @property
    def coordinates(self) -> GeometricCoordinates:
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().coordinates

    @coordinates.setter
    def coordinates(self, coordinates: GeometricCoordinates) -> None:
        self._check_if_annotation_is_valid()
        self._space.place_object(
            object_instance=self._object_instance,
            placement=FramePlacement(coordinates=coordinates, frames=self.frame),
            overwrite=True,
        )

    def _get_annotation_data(self) -> GeometricAnnotationData:
        return self._space._frames_to_object_hash_to_annotation_data[self._frame][self._object_instance.object_hash]

    def _check_if_annotation_is_valid(self) -> None:
        if (
            self._frame not in self._space._frames_to_object_hash_to_annotation_data
            or self._object_instance.object_hash
            not in self._space._frames_to_object_hash_to_annotation_data[self._frame]
        ):
            raise LabelRowError(
                "Trying to use an ObjectInstance.FrameAnnotation for a VideoObjectInstance that is not on the frame"
            )


class FrameClassificationAnnotation(ClassificationAnnotation):
    """Annotations for multi-frame classifications (e.g. Video)."""

    def __init__(self, space: VideoSpace, classification_instance: ClassificationInstance, frame: int):
        super().__init__(space, classification_instance)
        self._space: VideoSpace = space
        self._frame = frame

    @property
    def space(self) -> VideoSpace:
        return self._space

    @property
    def frame(self) -> int:
        return self._frame

    def _get_annotation_data(self) -> AnnotationData:
        return self._space._frames_to_classification_hash_to_annotation_data[self._frame][
            self._classification_instance.classification_hash
        ]

    def _check_if_annotation_is_valid(self) -> None:
        if (
            self._frame not in self._space._frames_to_classification_hash_to_annotation_data
            or self._classification_instance.classification_hash
            not in self._space._frames_to_classification_hash_to_annotation_data[self._frame]
        ):
            raise LabelRowError(
                "Trying to use an ObjectInstance.FrameAnnotation for a VideoObjectInstance that is not on the frame"
            )


class SingleFrameClassificationAnnotation(ClassificationAnnotation):
    """Annotations for single-frame classifications (e.g. Image)."""

    def __init__(self, space: ImageSpace, classification_instance: ClassificationInstance):
        super().__init__(space, classification_instance)
        self._space: ImageSpace = space
        self._classification_instance = classification_instance

    @property
    def frame(self) -> int:
        return 0

    @property
    def space(self) -> ImageSpace:
        return self._space

    def _get_annotation_data(self) -> AnnotationData:
        return self._space._classification_hash_to_annotation_data[self._classification_instance.classification_hash]

    def _check_if_annotation_is_valid(self) -> None:
        if not self._classification_instance.classification_hash in self._space._classification_hash_to_annotation_data:
            raise LabelRowError("Annotation is invalid")
