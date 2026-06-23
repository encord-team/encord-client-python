from __future__ import annotations

from typing import TYPE_CHECKING, List

from encord.constants.enums import SpaceType
from encord.objects.spaces.multiframe_space.multiframe_space import MultiFrameSpace
from encord.objects.spaces.types import (
    ImageSequenceFrameInfo,
    ImageSequenceSpaceInfo,
    SpaceInfo,
    VideoSpaceInfo,
)

if TYPE_CHECKING:
    from encord.objects.ontology_labels_impl import LabelRowV2


class VideoSpace(MultiFrameSpace):
    """Space implementation for frame-based video and image-sequence annotations."""

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
        """Initialize a video or image-sequence space.

        Args:
            space_id: The unique identifier of the space.
            label_row: The label row that owns the space.
            space_info: The raw space information used to populate the space.
            number_of_frames: The total number of frames in the space.
            width: The width of each frame in pixels.
            height: The height of each frame in pixels.
            is_image_sequence: Whether the space represents an image sequence
                rather than a video.
        """
        super().__init__(space_id, label_row, space_info, number_of_frames=number_of_frames)

        self._number_of_frames = number_of_frames
        self._width = width
        self._height = height
        self._is_image_sequence = is_image_sequence

        if space_info["space_type"] == SpaceType.VIDEO:
            self._data_duration = space_info["data_duration"]
            self._data_fps = space_info["data_fps"]
        else:
            self._data_duration = 0.0
            self._data_fps = 0.0

        if space_info["space_type"] == SpaceType.IMAGE_SEQUENCE:
            self._frames: List[ImageSequenceFrameInfo] = space_info["frames"]
        else:
            self._frames = []

    def _get_frame_dimensions(self, frame: int) -> tuple[int, int]:
        return self._width, self._height

    def _to_space_dict(self) -> VideoSpaceInfo | ImageSequenceSpaceInfo:
        frame_labels = self._build_frame_labels_dict()

        if self._is_image_sequence:
            return ImageSequenceSpaceInfo(
                space_type=SpaceType.IMAGE_SEQUENCE,
                labels=frame_labels,
                number_of_frames=self._number_of_frames,
                width=self._width,
                height=self._height,
                frames=self._frames,
            )

        return VideoSpaceInfo(
            space_type=SpaceType.VIDEO,
            labels=frame_labels,
            number_of_frames=self._number_of_frames,
            width=self._width,
            height=self._height,
            data_duration=self._data_duration,
            data_fps=self._data_fps,
        )
