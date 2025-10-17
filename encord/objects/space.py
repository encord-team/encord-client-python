from abc import ABC
from enum import StrEnum
from typing import Iterable, Optional, TypeVar

from encord.objects import LabelRowV2, Object, ObjectInstance, Shape
from encord.objects.coordinates import AudioCoordinates, Coordinates, TextCoordinates
from encord.objects.frames import Frames, Range


class SpaceType(StrEnum):
    """Fixed set of available space types"""

    AUDIO = "AUDIO"
    TEXT = "TEXT"
    VISION = "VISION"
    POINT_CLOUD = "POINT_CLOUD"


SpaceT = TypeVar("SpaceT", bound="Space")


class Space(ABC):
    def __init__(
        self, id: str, title: str, space_type: SpaceType, parent: LabelRowV2, layout_key: Optional[str] = None
    ):
        self.id = id
        # Title would probably be:
        # name of storage_item, OR
        # key in data group
        self.title = title
        self.space_type = space_type
        self.parent = parent

        # This will only be not None when space is a data group child
        # This refers to the key of the data group child in the layout (e.g. video-left)
        self.layout_key = layout_key

    def remove_object_instance(self, object_hash: str) -> ObjectInstance:
        raise NotImplementedError()

    def move_object_instance_to_space(self, object_hash: str, target_space_id: str):
        raise NotImplementedError()


class VisionSpace(Space):
    def __init__(self, id: str, title: str, layout_key: Optional[str], parent: LabelRowV2):
        super().__init__(id, title, SpaceType.VISION, parent, layout_key)

    def add_object_instance(self, obj: Object, coordinates: Coordinates, frames: Frames = 0) -> ObjectInstance:
        if obj.shape not in [
            Shape.BOUNDING_BOX,
            Shape.ROTATABLE_BOUNDING_BOX,
            Shape.BITMASK,
            Shape.POLYGON,
            Shape.POLYLINE,
            Shape.POINT,
            Shape.SKELETON,
        ]:
            raise ValueError(f"Shapes of type: {obj.shape} are not allowed on Vision Space.")

        object_instance = obj.create_instance()
        object_instance.set_for_frames(coordinates=coordinates, frames=frames)
        self.parent.add_object_instance(object_instance=object_instance)
        return object_instance

    def get_object_instances(
        self, filter_ontology_object: Optional[Object] = None, filter_frames: Optional[Frames] = None
    ) -> Iterable[ObjectInstance]:
        raise NotImplementedError()


class PointCloudSpace(Space):
    def __init__(self, id: str, title: str, layout_key: Optional[str], parent: LabelRowV2):
        super().__init__(id, title, SpaceType.POINT_CLOUD, parent, layout_key)

    def get_object_instances(
        self,
        filter_ontology_object: Optional[Object] = None,
    ) -> Iterable[ObjectInstance]:
        raise NotImplementedError()

    def add_object_instance(self, obj: Object, coordinates: Coordinates) -> ObjectInstance:
        if obj.shape != Shape.SEGMENTATION:
            raise ValueError(f"Only segmentation spaces are allowed on PointCloudSpace.")

        object_instance = obj.create_instance()
        # For Point Cloud, no frames, it applies to whole file
        object_instance.set_for_frames(coordinates=coordinates)
        self.parent.add_object_instance(object_instance=object_instance)
        return object_instance


class AudioSpace(Space):
    def __init__(self, id: str, title: str, layout_key: Optional[str], parent: LabelRowV2):
        super().__init__(id, title, SpaceType.AUDIO, parent, layout_key)

    def get_object_instances(
        self,
        filter_ontology_object: Optional[Object] = None,
        filter_ranges: Optional[Range | list[Range]] = None,
    ) -> Iterable[ObjectInstance]:
        raise NotImplementedError()

    def add_object_instance(self, obj: Object, ranges: list[Range] | Range):
        if obj.shape != Shape.AUDIO:
            raise ValueError(f"AudioSpace requires objects with Shape.AUDIO, got {obj.shape}")

        ranges = ranges if isinstance(ranges, list) else [ranges]

        object_instance = obj.create_instance()
        object_instance.set_for_frames(coordinates=AudioCoordinates(range=ranges))
        self.parent.add_object_instance(object_instance=object_instance)


class TextSpace(Space):
    def __init__(self, id: str, title: str, layout_key: Optional[str], parent: LabelRowV2):
        super().__init__(id, title, SpaceType.TEXT, parent, layout_key)

    def get_object_instances(
        self,
        filter_ontology_object: Optional[Object] = None,
        filter_ranges: Optional[Range | list[Range]] = None,
    ) -> Iterable[ObjectInstance]:
        raise NotImplementedError()

    def add_object_instance(self, obj: Object, ranges: list[Range] | Range):
        if obj.shape != Shape.TEXT:
            raise ValueError(f"AudioSpace requires objects with Shape.AUDIO, got {obj.shape}")

        text_ranges = ranges if isinstance(ranges, list) else [ranges]

        object_instance = obj.create_instance()
        object_instance.set_for_frames(coordinates=TextCoordinates(range=text_ranges))
        self.parent.add_object_instance(object_instance=object_instance)
