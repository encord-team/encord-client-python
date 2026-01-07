from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List

from encord.constants.enums import SpaceType
from encord.objects.spaces.multiframe_space.multiframe_space import MultiFrameSpace
from encord.objects.spaces.types import DicomFrameInfo, MedicalStackSpaceInfo
from encord.objects.types import LabelBlob

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tests.objects.spaces.test_serde import LabelRowV2


class MedicalStackSpace(MultiFrameSpace):
    """Space for medical files (e.g. DICOM, NIfTI)."""

    def __init__(self, space_id: str, label_row: LabelRowV2, frames: List[DicomFrameInfo]):
        super().__init__(space_id, label_row, number_of_frames=len(frames), height=0, width=0)
        self._frames = frames

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
