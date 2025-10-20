from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import TYPE_CHECKING, Dict, Iterable, Optional, Set, TypeVar, Union

from typing_extensions import Unpack

from encord.constants.enums import SpaceType
from encord.exceptions import LabelRowError
from encord.objects import Classification, ClassificationInstance
from encord.objects.common import Shape
from encord.objects.coordinates import AudioCoordinates, Coordinates, TextCoordinates, TwoDimensionalCoordinates
from encord.objects.frames import Frames, Range
from encord.orm.label_space import BaseSpaceInfo, ImageSpaceInfo, LabelBlob, SpaceInfo, VideoSpaceInfo

logger = logging.getLogger(__name__)
from encord.objects.ontology_object_instance import ObjectInstance, SetFramesKwargs

if TYPE_CHECKING:
    from encord.objects.ontology_labels_impl import LabelRowV2
    from encord.objects.ontology_object import Object


SpaceT = TypeVar("SpaceT", bound="Space")


class Space(ABC):
    """Manages the objects on a space within LabelRowV2.

    Users should not instantiate this class directly, but must obtain these instances via LabelRow.list_spaces().
    """

    def __init__(self, space_id: str, title: str, space_type: SpaceType, parent: LabelRowV2):
        self.space_id = space_id
        self.title = title
        self.space_type = space_type
        self.parent = parent

    @abstractmethod
    def get_object_instances(
        self,
    ) -> list[ObjectInstance]:
        pass

    @abstractmethod
    def remove_object_instance(self, object_hash: str) -> Optional[ObjectInstance]:
        pass

    @abstractmethod
    def move_object_instance_from_space(self, object_to_move: ObjectInstance) -> Optional[ObjectInstance]:
        pass

    @abstractmethod
    def get_classification_instances(
        self,
    ) -> list[ClassificationInstance]:
        pass

    @abstractmethod
    def remove_classification_instance(self, object_hash: str) -> Optional[ClassificationInstance]:
        pass

    @abstractmethod
    def move_classification_instance_from_space(
        self, object_to_move: ClassificationInstance
    ) -> Optional[ClassificationInstance]:
        pass

    @abstractmethod
    def _parse_space_dict(self, space_info: SpaceInfo, classification_answers: dict) -> None:
        pass

    @abstractmethod
    def _to_space_dict(self) -> SpaceInfo:
        pass


class VideoSpace(Space):
    def __init__(self, space_id: str, title: str, parent: LabelRowV2, number_of_frames: int):
        super().__init__(space_id, title, SpaceType.VIDEO, parent)
        self._frames_to_hashes: defaultdict[int, Set[str]] = defaultdict(set)
        self._objects_map: Dict[str, ObjectInstance] = dict()
        self._classifications_map: Dict[str, ClassificationInstance] = dict()
        self._number_of_frames: int = number_of_frames

    def _add_to_single_frame_to_hashes_map(self, label: Union[ObjectInstance], frame: int) -> None:
        if isinstance(label, ObjectInstance):
            self._frames_to_hashes[frame].add(label.object_hash)

    def _add_object_instance(self, object_instance: ObjectInstance) -> ObjectInstance:
        self._objects_map[object_instance.object_hash] = object_instance
        object_instance._set_space(self)

        frames_list = object_instance.get_annotation_frames()
        for frame in frames_list:
            self._frames_to_hashes[frame].add(object_instance.object_hash)

        return object_instance

    def _add_classification_instance(self, classification_instance: ClassificationInstance) -> ClassificationInstance:
        self._classifications_map[classification_instance.classification_hash] = classification_instance
        classification_instance._set_space(self)

        frames_list = classification_instance.get_annotation_frames()
        for frame in frames_list:
            self._frames_to_hashes[frame].add(classification_instance.classification_hash)

        return classification_instance

    def add_object_instance(
        self, obj: Object, coordinates: TwoDimensionalCoordinates, frames: Frames = 0, **kwargs: Unpack[SetFramesKwargs]
    ) -> ObjectInstance:
        object_instance = obj.create_instance()
        object_instance.set_for_frames(coordinates=coordinates, frames=frames, overwrite=False, **kwargs)

        return self._add_object_instance(object_instance)

    def get_object_instances(
        self,
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

        if original_space is None:
            raise LabelRowError("Unable to move object instance, as it currently does not belong to any space.")

        if isinstance(original_space, VideoSpace):
            original_space.remove_object_instance(object_to_move.object_hash)
            self._add_object_instance(object_to_move)
            return object_to_move
        else:
            logger.warning(
                f"Unable to move object instance from space of type {original_space.space_type} to {self.space_type}"
            )
            return None

    def add_classification_instance(
        self, classification: Classification, frames: Frames = 0, **kwargs: Unpack[SetFramesKwargs]
    ) -> ClassificationInstance:
        classification_instance = classification.create_instance()
        classification_instance.set_for_frames(frames=frames, overwrite=False, **kwargs)

        return self._add_classification_instance(classification_instance)

    def get_classification_instances(
        self,
    ) -> list[ClassificationInstance]:
        return list(self._classifications_map.values())

    def remove_classification_instance(self, classification_hash: str) -> Optional[ClassificationInstance]:
        classification_instance = self._classifications_map.pop(classification_hash)

        if classification_instance is None:
            logger.warning(f"Classification instance {classification_hash} not found.")
        else:
            classification_instance_frame_list = classification_instance.get_annotation_frames()
            for frame in classification_instance_frame_list:
                self._frames_to_hashes[frame].discard(classification_hash)

            classification_instance._set_space(None)

        return classification_instance

    def move_classification_instance_from_space(
        self, classification_to_move: ClassificationInstance
    ) -> Optional[ClassificationInstance]:
        original_space = classification_to_move._space

        if original_space is None:
            raise LabelRowError("Unable to move object instance, as it currently does not belong to any space.")

        if isinstance(original_space, VideoSpace):
            original_space.remove_classification_instance(classification_to_move.classification_hash)
            self._add_classification_instance(classification_to_move)
            return classification_to_move
        else:
            logger.warning(
                f"Unable to move classification instance from space of type {original_space.space_type} to {self.space_type}"
            )
            return None

    def _parse_space_dict(self, space_info: VideoSpaceInfo, classification_answers: dict) -> None:
        for frame, frame_label in space_info["labels"].items():
            for obj in frame_label["objects"]:
                object_hash = obj["objectHash"]
                if object_hash not in self._objects_map:
                    new_object_instance = self.parent._create_new_object_instance(obj, int(frame))
                    self._add_object_instance(new_object_instance)
                else:
                    object_instance = self._objects_map[object_hash]

                    coordinates = self.parent._get_coordinates(obj)
                    object_frame_instance_info = ObjectInstance.FrameInfo.from_dict(obj)

                    object_instance.set_for_frames(
                        coordinates=coordinates,
                        frames=int(frame),
                        created_at=object_frame_instance_info.created_at,
                        created_by=object_frame_instance_info.created_by,
                        last_edited_at=object_frame_instance_info.last_edited_at,
                        last_edited_by=object_frame_instance_info.last_edited_by,
                        confidence=object_frame_instance_info.confidence,
                        manual_annotation=object_frame_instance_info.manual_annotation,
                        reviews=object_frame_instance_info.reviews,
                        is_deleted=object_frame_instance_info.is_deleted,
                    )

            for classification in frame_label["classifications"]:
                classification_hash = classification["classificationHash"]
                if classification_hash not in self._classifications_map:
                    new_classification_instance = self.parent._create_new_classification_instance(
                        classification, int(frame), classification_answers
                    )
                    self._add_classification_instance(new_classification_instance)
                else:
                    classification_instance = self._classifications_map[classification_hash]
                    classification_frame_instance_info = ClassificationInstance.FrameData.from_dict(classification)

                    classification_instance.set_for_frames(
                        frames=int(frame),
                        created_at=classification_frame_instance_info.created_at,
                        created_by=classification_frame_instance_info.created_by,
                        last_edited_at=classification_frame_instance_info.last_edited_at,
                        last_edited_by=classification_frame_instance_info.last_edited_by,
                        confidence=classification_frame_instance_info.confidence,
                        manual_annotation=classification_frame_instance_info.manual_annotation,
                        reviews=classification_frame_instance_info.reviews,
                    )

    def _to_space_dict(self) -> BaseSpaceInfo:
        labels: dict[str, LabelBlob] = {}

        for frame, label_hashes in self._frames_to_hashes.items():
            object_list = []
            classification_list = []

            for label_hash in label_hashes:
                frame_object_instance = self._objects_map.get(label_hash)
                frame_classification_instance = self._classifications_map.get(label_hash)

                if frame_object_instance is None and frame_classification_instance is None:
                    continue
                elif frame_object_instance is not None:
                    object_list.append(self.parent._to_encord_object(frame_object_instance, frame))
                else:
                    classification_list.append(
                        self.parent._to_encord_classification(frame_classification_instance, frame)
                    )

            labels[str(frame)] = LabelBlob(objects=object_list, classifications=classification_list)

        res = VideoSpaceInfo(
            space_type=self.space_type,
            labels=labels,
            number_of_frames=self._number_of_frames,
        )

        return res


class ImageSpace(Space):
    def __init__(self, space_id: str, title: str, parent: LabelRowV2):
        super().__init__(space_id, title, SpaceType.IMAGE, parent)
        self._label_hashes: set[str] = set()
        self._objects_map: Dict[str, ObjectInstance] = dict()
        self._classifications_map: Dict[str, ClassificationInstance] = dict()

    def _add_object_instance(self, object_instance: ObjectInstance) -> ObjectInstance:
        self._objects_map[object_instance.object_hash] = object_instance
        object_instance._set_space(self)

        self._label_hashes.add(object_instance.object_hash)

        return object_instance

    def _add_classification_instance(self, classification_instance: ClassificationInstance) -> ClassificationInstance:
        self._classifications_map[classification_instance.classification_hash] = classification_instance
        classification_instance._set_space(self)

        self._label_hashes.add(classification_instance.classification_hash)

        return classification_instance

    def add_object_instance(
        self, obj: Object, coordinates: TwoDimensionalCoordinates, **kwargs: Unpack[SetFramesKwargs]
    ) -> ObjectInstance:
        object_instance = obj.create_instance()
        object_instance.set_for_frames(coordinates=coordinates, frames=0, overwrite=False, **kwargs)

        return self._add_object_instance(object_instance)

    def get_object_instances(
        self,
        # TODO: Should this be iterable? Or a list?
    ) -> list[ObjectInstance]:
        return list(self._objects_map.values())

    def remove_object_instance(self, object_hash: str) -> Optional[ObjectInstance]:
        object_instance = self._objects_map.pop(object_hash)

        if object_instance is None:
            logger.warning(f"Object instance {object_hash} not found.")
        else:
            self._label_hashes.discard(object_hash)
            object_instance._set_space(None)

        return object_instance

    def move_object_instance_from_space(self, object_to_move: ObjectInstance) -> Optional[ObjectInstance]:
        original_space = object_to_move._space

        if original_space is None:
            raise LabelRowError("Unable to move object instance, as it currently does not belong to any space.")

        if isinstance(original_space, ImageSpace):
            original_space.remove_object_instance(object_to_move.object_hash)
            self._add_object_instance(object_to_move)
            return object_to_move
        else:
            logger.warning(
                f"Unable to move object instance from space of type {original_space.space_type} to {self.space_type}"
            )
            return None

    def add_classification_instance(
        self, classification: Classification, **kwargs: Unpack[SetFramesKwargs]
    ) -> ClassificationInstance:
        classification_instance = classification.create_instance()
        classification_instance.set_for_frames(frames=0, overwrite=False, **kwargs)

        return self._add_classification_instance(classification_instance)

    def get_classification_instances(
        self,
    ) -> list[ClassificationInstance]:
        return list(self._classifications_map.values())

    def remove_classification_instance(self, classification_hash: str) -> Optional[ClassificationInstance]:
        classification_instance = self._classifications_map.pop(classification_hash)

        if classification_instance is None:
            logger.warning(f"Classification instance {classification_hash} not found.")
        else:
            self._label_hashes.discard(classification_hash)

            classification_instance._set_space(None)

        return classification_instance

    def move_classification_instance_from_space(
        self, classification_to_move: ClassificationInstance
    ) -> Optional[ClassificationInstance]:
        original_space = classification_to_move._space

        if original_space is None:
            raise LabelRowError("Unable to move object instance, as it currently does not belong to any space.")

        if isinstance(original_space, ImageSpace):
            original_space.remove_classification_instance(classification_to_move.classification_hash)
            self._add_classification_instance(classification_to_move)
            return classification_to_move
        else:
            logger.warning(
                f"Unable to move classification instance from space of type {original_space.space_type} to {self.space_type}"
            )
            return None

    def _parse_space_dict(self, space_info: BaseSpaceInfo, classification_answers: dict) -> None:
        frame_label = space_info["labels"].get("0")

        if frame_label is None:
            return

        for obj in frame_label["objects"]:
            object_hash = obj["objectHash"]
            if object_hash not in self._objects_map:
                new_object_instance = self.parent._create_new_object_instance(obj, int(0))
                self._add_object_instance(new_object_instance)
            else:
                object_instance = self._objects_map[object_hash]

                coordinates = self.parent._get_coordinates(obj)
                object_frame_instance_info = ObjectInstance.FrameInfo.from_dict(obj)

                object_instance.set_for_frames(
                    coordinates=coordinates,
                    frames=0,
                    created_at=object_frame_instance_info.created_at,
                    created_by=object_frame_instance_info.created_by,
                    last_edited_at=object_frame_instance_info.last_edited_at,
                    last_edited_by=object_frame_instance_info.last_edited_by,
                    confidence=object_frame_instance_info.confidence,
                    manual_annotation=object_frame_instance_info.manual_annotation,
                    reviews=object_frame_instance_info.reviews,
                    is_deleted=object_frame_instance_info.is_deleted,
                )

        for classification in frame_label["classifications"]:
            classification_hash = classification["classificationHash"]
            if classification_hash not in self._classifications_map:
                new_classification_instance = self.parent._create_new_classification_instance(
                    classification, 0, classification_answers
                )
                self._add_classification_instance(new_classification_instance)
            else:
                classification_instance = self._classifications_map[classification_hash]
                classification_frame_instance_info = ClassificationInstance.FrameData.from_dict(classification)

                classification_instance.set_for_frames(
                    frames=0,
                    created_at=classification_frame_instance_info.created_at,
                    created_by=classification_frame_instance_info.created_by,
                    last_edited_at=classification_frame_instance_info.last_edited_at,
                    last_edited_by=classification_frame_instance_info.last_edited_by,
                    confidence=classification_frame_instance_info.confidence,
                    manual_annotation=classification_frame_instance_info.manual_annotation,
                    reviews=classification_frame_instance_info.reviews,
                )

    def _to_space_dict(self) -> BaseSpaceInfo:
        labels: dict[str, LabelBlob] = {}

        object_list = []
        classification_list = []

        for label_hash in self._label_hashes:
            frame_object_instance = self._objects_map.get(label_hash)
            frame_classification_instance = self._classifications_map.get(label_hash)

            if frame_object_instance is None and frame_classification_instance is None:
                continue
            elif frame_object_instance is not None:
                object_list.append(self.parent._to_encord_object(frame_object_instance, 0))
            else:
                classification_list.append(self.parent._to_encord_classification(frame_classification_instance, 0))

        labels["0"] = LabelBlob(objects=object_list, classifications=classification_list)

        res = ImageSpaceInfo(
            space_type=self.space_type,
            labels=labels,
        )

        return res


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
            raise ValueError(f"AudioSpace requires objects with Shape.AUDIO, got {obj.shape}")

        text_ranges = ranges if isinstance(ranges, list) else [ranges]

        object_instance = obj.create_instance()
        object_instance.set_for_frames(coordinates=TextCoordinates(range=text_ranges))
        self.parent.add_object_instance(object_instance=object_instance)
