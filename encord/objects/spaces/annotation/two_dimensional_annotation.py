from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from encord.exceptions import LabelRowError
from encord.objects.coordinates import Coordinates
from encord.objects.spaces.annotation.base_annotation import AnnotationData, ClassificationAnnotation, ObjectAnnotation
from encord.objects.spaces.entity import SpaceClassification, SpaceObject

if TYPE_CHECKING:
    from encord.objects.spaces.image_space import ImageSpace
    from encord.objects.spaces.video_space import VideoSpace


@dataclass
class TwoDimensionalAnnotationData(AnnotationData):
    coordinates: Coordinates


class TwoDimensionalFrameObjectAnnotation(ObjectAnnotation):
    def __init__(self, space: VideoSpace, object_instance: SpaceObject, frame: int):
        super().__init__(space, object_instance)
        self._space = space
        self._frame = frame

    @property
    def frame(self) -> int:
        return self._frame

    @property
    def coordinates(self) -> Coordinates:
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().coordinates

    @coordinates.setter
    def coordinates(self, coordinates: Coordinates) -> None:
        self._check_if_annotation_is_valid()
        self._space.place_object(object=self._object_instance, coordinates=coordinates, frames=self._frame)

    def _get_annotation_data(self) -> TwoDimensionalAnnotationData:
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


class TwoDimensionalObjectAnnotation(ObjectAnnotation):
    def __init__(self, space: ImageSpace, object_instance: SpaceObject):
        super().__init__(space, object_instance)
        self._space = space

    @property
    def coordinates(self) -> Coordinates:
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().coordinates

    @coordinates.setter
    def coordinates(self, coordinates: Coordinates) -> None:
        self._check_if_annotation_is_valid()
        self._space.place_object(object=self._object_instance, coordinates=coordinates)

    def _get_annotation_data(self) -> TwoDimensionalAnnotationData:
        return self._space._object_hash_to_annotation_data[self._object_instance.object_hash]

    def _check_if_annotation_is_valid(self) -> None:
        if self._object_instance.object_hash not in self._space._object_hash_to_annotation_data:
            raise LabelRowError(
                "Trying to use an ObjectInstance.FrameAnnotation for a VideoObjectInstance that is not on the frame"
            )


class FrameObjectAnnotation(ObjectAnnotation):
    def __init__(self, space: VideoSpace, object_instance: SpaceObject, frame: int):
        super().__init__(space, object_instance)
        self._space = space
        self._frame = frame

    @property
    def frame(self) -> int:
        return self._frame

    # TODO: Here it should be classifiation_hash
    def _get_annotation_data(self) -> AnnotationData:
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
    def __init__(self, space: VideoSpace, classification: SpaceClassification, frame: int):
        super().__init__(space, classification)
        self._space = space
        self._frame = frame

    @property
    def frame(self) -> int:
        return self._frame

    def _get_annotation_data(self) -> AnnotationData:
        return self._space._frames_to_classification_hash_to_annotation_data[self._frame][
            self._classification.object_hash
        ]

    def _check_if_annotation_is_valid(self) -> None:
        if (
            self._frame not in self._space._frames_to_classification_hash_to_annotation_data
            or self._classification.classification_hash
            not in self._space._frames_to_classification_hash_to_annotation_data[self._frame]
        ):
            raise LabelRowError(
                "Trying to use an ObjectInstance.FrameAnnotation for a VideoObjectInstance that is not on the frame"
            )
