from __future__ import annotations

import logging
from abc import ABC
from collections import defaultdict
from typing import TYPE_CHECKING, Dict, Iterable, Optional, Set, TypeVar, Union

from encord.constants.enums import DataType, SpaceType
from encord.objects import ClassificationInstance
from encord.objects.common import Shape
from encord.objects.coordinates import AudioCoordinates, Coordinates, TextCoordinates
from encord.objects.frames import Frames, Range, frames_class_to_frames_list
from encord.orm.label_space import LabelBlob, SpaceInfo

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from encord.objects.ontology_labels_impl import LabelRowV2
    from encord.objects.ontology_object import Object
    from encord.objects.ontology_object_instance import ObjectInstance


SpaceT = TypeVar("SpaceT", bound="Space")


class Space(ABC):
    def __init__(
        self, id: str, title: str, space_type: SpaceType, parent: LabelRowV2
    ):
        self.id = id
        # Title would probably be:
        # name of storage_item, OR
        # key in data group
        self.title = title
        self.space_type = space_type
        self.parent = parent

    def move_object_instance_to_space(self, object_hash: str, target_space_id: str):
        raise NotImplementedError()

    
class VisionSpace(Space):
    def __init__(self, id: str, title: str, parent: LabelRowV2):
        super().__init__(id, title, SpaceType.VISION, parent)
        self._frames_to_hashes: defaultdict[int, Set[str]] = defaultdict(set)
        self._objects_map: Dict[str, ObjectInstance] = dict()

    def _add_to_single_frame_to_hashes_map(self, label: Union[ObjectInstance, ClassificationInstance], frame: int) -> None:
        self._frames_to_hashes[frame].add(label.object_hash)

    def _add_object_instance(self, object_instance: ObjectInstance) -> ObjectInstance:
        self._objects_map[object_instance.object_hash] = object_instance
        object_instance._set_space(self)

        frames_list = object_instance.get_annotation_frames()
        for frame in frames_list:
            self._frames_to_hashes[frame].add(object_instance.object_hash)

        return object_instance

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

        return self._add_object_instance(object_instance)

    def get_object_instances(
        self
        # TODO: Should this be iterable? Or a list?
    ) -> list[ObjectInstance]:
        return list(self._objects_map.values())

    def remove_object_instance(self, object_hash: str) -> Optional[ObjectInstance]:
        object_instance = self._objects_map.pop(object_hash)

        if object_instance is None:
            logger.warning(f"Object instance {object_hash} not found.")
        else:
            object_instance_frame_list = object_instance.get_annotation_frames()
            for frame in object_instance_frame_list:
                self._frames_to_hashes[frame].discard(object_hash)

            object_instance._set_space(None)

        return object_instance

    def move_object_instance_from_space(self, object_to_move: ObjectInstance) -> Optional[ObjectInstance]:
        original_space = object_to_move._space

        if isinstance(original_space, VisionSpace):
            original_space.remove_object_instance(object_to_move.object_hash)
            self._add_object_instance(object_to_move)
            return object_to_move
        else:
            logger.warning(f"Unable to move object instance from space of type {original_space.space_type} to {self.space_type}")
            return None

    def _to_encord_space(self) -> SpaceInfo:
        labels: dict[str, LabelBlob] = {}

        for frame, object_hashes in self._frames_to_hashes.items():
            object_list = []
            for object_hash in object_hashes:
                frame_object_instance = self._objects_map.get(object_hash)
                if frame_object_instance is None:
                    continue

                object_list.append(self.parent._to_encord_object(frame_object_instance, frame))

            labels[str(frame)] = LabelBlob(objects=object_list, classifications=[])

        res = SpaceInfo(
            space_type=self.space_type,
            data_type=DataType.VIDEO,
            labels=labels,
        )

        return res


class SceneStreamSpace(Space):
    def __init__(self, id: str, title: str, parent: LabelRowV2):
        super().__init__(id, title, SpaceType.SCENE_STREAM, parent)

    def get_object_instances(
        self,
        filter_ontology_object: Optional[Object] = None,
    ) -> Iterable[ObjectInstance]:
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
    def __init__(self, id: str, title: str, parent: LabelRowV2):
        super().__init__(id, title, SpaceType.AUDIO, parent)

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
    def __init__(self, id: str, title: str, parent: LabelRowV2):
        super().__init__(id, title, SpaceType.TEXT, parent)

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

