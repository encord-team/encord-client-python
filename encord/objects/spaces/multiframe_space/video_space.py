from __future__ import annotations

from typing import TYPE_CHECKING, List

from encord.constants.enums import SpaceType
from encord.objects.spaces.multiframe_space.multiframe_space import MultiFrameSpace
from encord.objects.spaces.types import DicomFrameInfo, ImageSequenceSpaceInfo, SpaceInfo, VideoSpaceInfo
from encord.objects.types import LabelBlob

if TYPE_CHECKING:
    from encord.objects.ontology_labels_impl import LabelRowV2


class VideoSpace(MultiFrameSpace):
    """Video space implementation for frame-based video annotations."""

    def __init__(
        self,
        space_id: str,
        label_row: LabelRowV2,
        space_info: SpaceInfo,
        number_of_frames: int,
        width: int,
        height: int,
        is_image_sequence: bool,
    ):
        super().__init__(space_id, label_row, space_info, number_of_frames=number_of_frames)
        self._number_of_frames = number_of_frames
        self._width = width
        self._height = height
        self._is_image_sequence = is_image_sequence

    def _get_frame_dimensions(self, frame: int) -> tuple[int, int]:
        return self._width, self._height

    def _to_space_dict(self) -> VideoSpaceInfo | ImageSequenceSpaceInfo:
        """Export space to dictionary format."""
        frame_labels = self._build_frame_labels_dict()

        if self._is_image_sequence:
            return ImageSequenceSpaceInfo(
                space_type=SpaceType.IMAGE_SEQUENCE,
                labels=frame_labels,
                number_of_frames=self._number_of_frames,
                width=self._width,
                height=self._height,
            )
        else:
            return VideoSpaceInfo(
                space_type=SpaceType.VIDEO,
                labels=frame_labels,
                number_of_frames=self._number_of_frames,
                width=self._width,
                height=self._height,
            )
