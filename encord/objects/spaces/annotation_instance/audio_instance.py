from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from encord.exceptions import LabelRowError
from encord.objects.classification_instance import BaseClassificationInstance
from encord.objects.constants import DEFAULT_CONFIDENCE, DEFAULT_MANUAL_ANNOTATION
from encord.objects.coordinates import Coordinates, AudioCoordinates
from encord.objects.frames import Frames, frames_class_to_frames_list, frames_to_ranges, Ranges
from encord.objects.ontology_object_instance import BaseObjectInstance, ObjectInstance, check_coordinate_type

if TYPE_CHECKING:
    from encord.objects.classification import Classification
    from encord.objects.ontology_object import Object
    from encord.objects.spaces.range_space import RangeBasedSpace


class AudioObjectInstance(BaseObjectInstance):
    def __init__(self, ontology_object: Object, *, object_hash: Optional[str] = None, space: AudioSpace):
        super().__init__(ontology_object, object_hash=object_hash)
        self._space = space

    def set_annotation_for_ranges(
        self,
        ranges: Ranges,
        *,
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
        reviews: Optional[List[dict]] = None,
        is_deleted: Optional[bool] = None,
    ) -> None:
        """Place the object onto the specified range.

        If the object already exists on the range and overwrite is set to `True`,
        the currently specified values will be overwritten.

        Args:
            ranges: The range to add the object instance to.
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

        existing_frame_data = self._frames_to_instance_data.get(0)
        audio_coordinates = AudioCoordinates(range=ranges)

        # No overwrite
        # No checking frame instance data, as its only on one frame

        if existing_frame_data is None:
            existing_frame_data = ObjectInstance.FrameData(
                coordinates=audio_coordinates, object_frame_instance_info=ObjectInstance.FrameInfo()
            )
            self._frames_to_instance_data[0] = existing_frame_data

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
        existing_frame_data.coordinates = audio_coordinates


class AudioClassificationInstance(BaseClassificationInstance):
    def __init__(self, ontology_classification: Classification, *, classification_hash: Optional[str] = None, space: AudioSpace):
        super().__init__(ontology_classification, classification_hash=classification_hash)
        self._space = space
