from __future__ import annotations

from typing import TYPE_CHECKING

from encord.constants.enums import SpaceType
from encord.objects.spaces.multiframe_space.multiframe_space import MultiFrameSpace
from encord.objects.spaces.types import ImageSequenceSpaceInfo

if TYPE_CHECKING:
    from encord.objects.ontology_labels_impl import LabelRowV2


class ImageSequenceSpace(MultiFrameSpace):
    """Image sequence space implementation for frame-based video annotations."""

    def __init__(
        self,
        space_id: str,
        label_row: LabelRowV2,
        number_of_frames: int,
        width: int,
        height: int,
    ):
        super().__init__(space_id, label_row, number_of_frames=number_of_frames)
        self._number_of_frames = number_of_frames
        self._width = width
        self._height = height

    def _get_frame_dimensions(self, frame: int) -> tuple[int, int]:
        return self._width, self._height

    def _to_space_dict(self) -> ImageSequenceSpaceInfo:
        """Export space to dictionary format."""
        frame_labels = self._build_frame_labels_dict()

        return ImageSequenceSpaceInfo(
            space_type=SpaceType.IMAGE_SEQUENCE,
            labels=frame_labels,
            number_of_frames=self._number_of_frames,
            width=self._width,
            height=self._height,
        )
