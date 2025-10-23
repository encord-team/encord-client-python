from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Optional

from encord.exceptions import LabelRowError
from encord.objects.classification_instance import BaseClassificationInstance
from encord.objects.constants import DEFAULT_CONFIDENCE, DEFAULT_MANUAL_ANNOTATION
from encord.objects.coordinates import Coordinates
from encord.objects.frames import Frames, frames_class_to_frames_list, frames_to_ranges
from encord.objects.ontology_object_instance import check_coordinate_type
from encord.objects.spaces.annotation_instance.base_instance import BaseObjectInstance

if TYPE_CHECKING:
    from encord.objects.classification import Classification
    from encord.objects.ontology_object import Object
    from encord.objects.spaces.video_space import VideoSpace


class VideoObjectInstance(BaseObjectInstance):
    def __init__(self, ontology_object: Object, *, object_hash: Optional[str] = None, space: VideoSpace):
        super().__init__(ontology_object, object_hash=object_hash)
        self._space = space
        self._frames_to_annotation_data: Dict[int, BaseObjectInstance.AnnotationData] = {}

    @property
    def _last_frame(self) -> int:
        return self._space._number_of_frames

    def check_within_range(self, frame: int) -> None:
        """Check if the given frame is within the acceptable range.

        Args:
            frame: The frame number to check.

        Raises:
            LabelRowError: If the frame is out of the acceptable range.
        """
        if frame < 0 or frame >= self._last_frame:
            raise LabelRowError(
                f"The supplied frame of `{frame}` is not within the acceptable bounds of `0` to `{self._last_frame}`."
            )

    def add_annotation(
        self,
        coordinates: Coordinates,
        frames: Frames = 0,
        *,
        overwrite: bool = False,
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
        reviews: Optional[List[dict]] = None,
        is_deleted: Optional[bool] = None,
    ) -> None:
        """Place the object onto the specified frame(s).

        If the object already exists on the frame and overwrite is set to `True`,
        the currently specified values will be overwritten.

        Args:
            coordinates: The coordinates of the object in the frame.
                This will throw an error if the type of the coordinates does not match the type of the attribute in the object instance.
            frames: The frames to add the object instance to. Defaults to the first frame for convenience.
            overwrite: If `True`, overwrite existing data for the given frames.
                This will not reset all the non-specified values.
                If `False` and data already exists for the given frames, raises an error.
            created_at: Optionally specify the creation time of the object instance on this frame.
                Defaults to `datetime.now()`.
            created_by: Optionally specify the creator of the object instance on this frame.
                Defaults to the current SDK user.
            last_edited_at: Optionally specify the last edit time of the object instance on this frame.
                Defaults to `datetime.now()`.
            last_edited_by: Optionally specify the last editor of the object instance on this frame.
                Defaults to the current SDK user.
            confidence: Optionally specify the confidence of the object instance on this frame. Defaults to `1.0`.
            manual_annotation: Optionally specify whether the object instance on this frame was manually annotated. Defaults to `True`.
            reviews: Should only be set by internal functions.
            is_deleted: Should only be set by internal functions.
        """
        frames_list = frames_class_to_frames_list(frames)

        for frame in frames_list:
            existing_frame_data = self._frames_to_annotation_data.get(frame)

            if overwrite is False and existing_frame_data is not None:
                raise LabelRowError(
                    "Cannot overwrite existing data for a frame. Set `overwrite` to `True` to overwrite."
                )

            check_coordinate_type(coordinates, self._ontology_object, self._parent)

            self.check_within_range(frame)

            if existing_frame_data is None:
                existing_frame_data = BaseObjectInstance.AnnotationData(
                    coordinates=coordinates, object_frame_instance_info=BaseObjectInstance.AnnotationInfo()
                )
                self._frames_to_annotation_data[frame] = existing_frame_data

            existing_frame_data.object_frame_instance_info.update_from_optional_fields(
                created_at=created_at,
                created_by=created_by,
                last_edited_at=last_edited_at,
                last_edited_by=last_edited_by,
                confidence=confidence,
                manual_annotation=manual_annotation,
                reviews=reviews,
                is_deleted=is_deleted,
            )
            existing_frame_data.coordinates = coordinates
            self._space._track_hash_for_frames(item_hash=self.object_hash, frames=[frame])

    def remove_annotation(self, frames: Frames) -> None:
        """Remove the object instance from the specified frames.

        Args:
            frames: The frames from which to remove the object instance.
        """
        frames_list = frames_class_to_frames_list(frames)
        for frame in frames_list:
            self._frames_to_annotation_data.pop(frame)

        self._space._untrack_hash_for_frames(item_hash=self.object_hash, frames=frames_list)

    def get_annotation(self, frame: int) -> FrameAnnotation:
        """Get annotation for the object instance on a particular frame.

        Args:
            frame: The frame to get the annotation for.

        Returns:
            FrameAnnotation: `VideoObjectInstance.FrameAnnotation` on a particular frame.
        """
        return self.FrameAnnotation(self, frame)

    def get_annotation_frames(self) -> List[int]:
        """Get all frames where an annotation exists.

        Returns:
            List[int]: An ordered list of frames where an annotation exists.
        """
        return sorted(self._frames_to_annotation_data.keys())

    def get_annotations(self) -> List[FrameAnnotation]:
        """Get all annotations for the object instance on all frames it has been placed on.

        Returns:
            List[Annotation]: A list of `ObjectInstance.Annotation` in order of available frames.
        """
        return [self.FrameAnnotation(self, frame_num) for frame_num in sorted(self._frames_to_annotation_data.keys())]

    class FrameAnnotation(BaseObjectInstance.Annotation):
        def __init__(self, object_instance: VideoObjectInstance, frame: int):
            super().__init__(object_instance)
            self._object_instance = object_instance
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
            self._object_instance.add_annotation(coordinates, self._frame, overwrite=True)

        def _get_annotation_data(self) -> BaseObjectInstance.AnnotationData:
            return self._object_instance._frames_to_annotation_data[self._frame]

        def _check_if_annotation_is_valid(self) -> None:
            if self._frame not in self._object_instance._frames_to_annotation_data:
                raise LabelRowError(
                    "Trying to use an ObjectInstance.FrameAnnotation for a VideoObjectInstance that is not on the frame"
                )


class VideoClassificationInstance(BaseClassificationInstance):
    def __init__(
        self, ontology_classification: Classification, *, classification_hash: Optional[str] = None, space: VideoSpace
    ):
        super().__init__(ontology_classification, classification_hash=classification_hash)
        self._space = space

    def set_annotation_for_frames(
        self,
        frames: Frames = 0,
        *,
        overwrite: bool = False,
        created_at: Optional[datetime] = datetime.now(),
        created_by: Optional[str] = None,
        confidence: float = DEFAULT_CONFIDENCE,
        manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION,
        last_edited_at: Optional[datetime] = datetime.now(),
        last_edited_by: Optional[str] = None,
        reviews: Optional[List[dict]] = None,
    ) -> None:
        """Places the classification onto the specified frame. If the classification already exists on the frame and
        overwrite is set to `True`, the currently specified values will be overwritten.

        Args:
            frames: The frame to add the classification instance to. Defaulting to the first frame for convenience.
            overwrite: If `True`, overwrite existing data for the given frames. This will not reset all the
                non-specified values. If `False` and data already exists for the given frames,
                raises an error.
            created_at: Optionally specify the creation time of the classification instance on this frame. Defaults to `datetime.now()`.
            created_by: Optionally specify the creator of the classification instance on this frame. Defaults to the current SDK user.
            last_edited_at: Optionally specify the last edit time of the classification instance on this frame. Defaults to `datetime.now()`.
            last_edited_by: Optionally specify the last editor of the classification instance on this frame. Defaults to the current SDK
                user.
            confidence: Optionally specify the confidence of the classification instance on this frame. Defaults to `1.0`.
            manual_annotation: Optionally specify whether the classification instance on this frame was manually annotated. Defaults to `True`.
            reviews: Should only be set by internal functions.
        """

        frames_list = frames_class_to_frames_list(frames)

        conflicting_frames_list = self._is_classification_already_present(frames_list)
        if conflicting_frames_list and not overwrite:
            raise LabelRowError(
                f"The classification '{self.classification_hash}' already exists "
                f"on the frames {frames_to_ranges(conflicting_frames_list)}. "
                f"Set 'overwrite' parameter to True to override."
            )

        frames_to_add = set(frames_list) - conflicting_frames_list if conflicting_frames_list else frames_list
        if not frames_to_add:
            return

        for frame in frames_list:
            self._check_within_range(frame)
            self._set_frame_and_frame_data(
                frame,
                overwrite=overwrite,
                created_at=created_at,
                created_by=created_by,
                confidence=confidence,
                manual_annotation=manual_annotation,
                last_edited_at=last_edited_at,
                last_edited_by=last_edited_by,
                reviews=reviews,
            )

        self._space._track_hash_for_frames(item_hash=self.classification_hash, frames=frames_list)
