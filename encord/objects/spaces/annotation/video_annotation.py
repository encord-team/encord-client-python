from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from encord.exceptions import LabelRowError
from encord.objects.coordinates import Coordinates
from encord.objects.spaces.annotation.base_annotation import Annotation, AnnotationData
from encord.objects.spaces.entity import ObjectEntity

if TYPE_CHECKING:
    from encord.objects.spaces.video_space import VideoSpace


@dataclass
class TwoDimensionalAnnotationData(AnnotationData):
    coordinates: Coordinates


class TwoDimensionalFrameAnnotation(Annotation):
    def __init__(self, space: VideoSpace, entity: ObjectEntity, frame: int):
        super().__init__(space, entity)
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
        self._space.place_object_entity(entity=self._entity, coordinates=coordinates, frames=self._frame)

    def _get_annotation_data(self) -> TwoDimensionalAnnotationData:
        return self._space._frames_to_entity_hash_to_annotation_data[self._frame][self._entity.object_hash]

    def _check_if_annotation_is_valid(self) -> None:
        if (
            self._frame not in self._space._frames_to_entity_hash_to_annotation_data
            or self._entity.object_hash not in self._space._frames_to_entity_hash_to_annotation_data[self._frame]
        ):
            raise LabelRowError(
                "Trying to use an ObjectInstance.FrameAnnotation for a VideoObjectInstance that is not on the frame"
            )


class FrameAnnotation(Annotation):
    def __init__(self, space: VideoSpace, entity: ObjectEntity, frame: int):
        super().__init__(space, entity)
        self._space = space
        self._frame = frame

    @property
    def frame(self) -> int:
        return self._frame

    # TODO: Here it should be classifiation_hash
    def _get_annotation_data(self) -> AnnotationData:
        return self._space._frames_to_entity_hash_to_annotation_data[self._frame][self._entity.object_hash]

    def _check_if_annotation_is_valid(self) -> None:
        if (
            self._frame not in self._space._frames_to_entity_hash_to_annotation_data
            or self._entity.object_hash not in self._space._frames_to_entity_hash_to_annotation_data[self._frame]
        ):
            raise LabelRowError(
                "Trying to use an ObjectInstance.FrameAnnotation for a VideoObjectInstance that is not on the frame"
            )
