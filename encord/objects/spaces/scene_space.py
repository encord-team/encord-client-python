from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from encord.constants.enums import SpaceType
from encord.objects.common import Shape
from encord.objects.coordinates import AudioCoordinates, Coordinates, TextCoordinates, TwoDimensionalCoordinates
from encord.objects.frames import Range
from encord.objects.ontology_object_instance import ObjectInstance
from encord.objects.spaces.base_space import Space

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from encord.objects.ontology_labels_impl import LabelRowV2
    from encord.objects.ontology_object import Object


class SceneStreamSpace(Space):
    def __init__(self, space_id: str, title: str, parent: LabelRowV2):
        super().__init__(space_id, title, SpaceType.SCENE_STREAM, parent)

    def get_object_instances(
        self,
        filter_ontology_object: Optional[Object] = None,
    ) -> list[ObjectInstance]:
        raise NotImplementedError()

    def add_object_instance(self, obj: Object, coordinates: Coordinates) -> ObjectInstance:
        if obj.shape != Shape.SEGMENTATION:
            raise ValueError(f"Only segmentation spaces are allowed on SceneStreamSpace.")

        object_instance = obj.create_instance()
        # For Point Cloud, no frames, it applies to whole file
        object_instance.set_for_frames(coordinates=coordinates)
        self.parent.add_object_instance(object_instance=object_instance)
        return object_instance


class AudioSpace(Space):
    def __init__(self, space_id: str, title: str, parent: LabelRowV2):
        super().__init__(space_id, title, SpaceType.AUDIO, parent)

    def get_object_instances(
        self,
        filter_ontology_object: Optional[Object] = None,
        filter_ranges: Optional[Range | list[Range]] = None,
    ) -> list[ObjectInstance]:
        raise NotImplementedError()

    def add_object_instance(self, obj: Object, ranges: list[Range] | Range):
        if obj.shape != Shape.AUDIO:
            raise ValueError(f"AudioSpace requires objects with Shape.AUDIO, got {obj.shape}")

        ranges = ranges if isinstance(ranges, list) else [ranges]

        object_instance = obj.create_instance()
        object_instance.set_for_frames(coordinates=AudioCoordinates(range=ranges))
        self.parent.add_object_instance(object_instance=object_instance)


class TextSpace(Space):
    def __init__(self, space_id: str, title: str, parent: LabelRowV2):
        super().__init__(space_id, title, SpaceType.TEXT, parent)

    def get_object_instances(
        self,
        filter_ontology_object: Optional[Object] = None,
        filter_ranges: Optional[Range | list[Range]] = None,
    ) -> list[ObjectInstance]:
        raise NotImplementedError()

    def add_object_instance(self, obj: Object, ranges: list[Range] | Range):
        if obj.shape != Shape.TEXT:
            raise ValueError(f"TextSpace requires objects with Shape.TEXT, got {obj.shape}")

        text_ranges = ranges if isinstance(ranges, list) else [ranges]

        object_instance = obj.create_instance()
        object_instance.set_for_frames(coordinates=TextCoordinates(range=text_ranges))
        self.parent.add_object_instance(object_instance=object_instance)
