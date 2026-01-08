from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Optional

from encord.constants.enums import SpaceType
from encord.exceptions import LabelRowError
from encord.objects.spaces.multiframe_space.multiframe_space import MultiFrameSpace
from encord.objects.spaces.types import DicomFrameInfo, MedicalStackSpaceInfo
from encord.objects.types import LabelBlob

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from encord.objects.ontology_labels_impl import LabelRowV2


class MedicalStackSpace(MultiFrameSpace):
    """Space for medical files (e.g. DICOM, NIfTI)."""

    def __init__(self, space_id: str, label_row: LabelRowV2, frames: List[DicomFrameInfo]):
        super().__init__(space_id, label_row, number_of_frames=len(frames))
        self._frames = frames

    def _get_frame_dimensions(self, frame_number: int) -> tuple[int, int]:
        if frame_number >= self._number_of_frames:
            raise LabelRowError(
                f"Invalid frame number '{frame_number}'. This file only has {self._number_of_frames} frames."
            )

        frame = self._frames[frame_number]
        return frame["width"], frame["height"]

    def _to_space_dict(self) -> MedicalStackSpaceInfo:
        """Export space to dictionary format."""
        labels: dict[str, LabelBlob] = {}
        frames_with_objects = list(self._frames_to_object_hash_to_annotation_data.keys())
        frames_with_classifications = list(self._frames_to_classification_hash_to_annotation_data.keys())
        frames_with_both_objects_and_classifications = sorted(set(frames_with_objects + frames_with_classifications))

        for frame in frames_with_both_objects_and_classifications:
            frame_label = self._build_frame_label_dict(frame=frame)
            labels[str(frame)] = frame_label

        return MedicalStackSpaceInfo(space_type=SpaceType.MEDICAL_STACK, labels=labels, frames=self._frames)
