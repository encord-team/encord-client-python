from __future__ import annotations

from encord.constants.enums import SpaceType
from encord.objects.spaces.multiframe_space.multiframe_space import MultiFrameSpace
from encord.objects.spaces.types import VideoSpaceInfo
from encord.objects.types import LabelBlob


class VideoSpace(MultiFrameSpace):
    """Video space implementation for frame-based video annotations."""

    def _to_space_dict(self) -> VideoSpaceInfo:
        """Export space to dictionary format."""
        labels: dict[str, LabelBlob] = {}
        frames_with_objects = list(self._frames_to_object_hash_to_annotation_data.keys())
        frames_with_classifications = list(self._frames_to_classification_hash_to_annotation_data.keys())
        frames_with_both_objects_and_classifications = sorted(set(frames_with_objects + frames_with_classifications))

        for frame in frames_with_both_objects_and_classifications:
            frame_label = self._build_frame_label_dict(frame=frame)
            labels[str(frame)] = frame_label

        return VideoSpaceInfo(
            space_type=SpaceType.VIDEO,
            labels=labels,
            number_of_frames=self._number_of_frames,
            width=self._width,
            height=self._height,
        )
