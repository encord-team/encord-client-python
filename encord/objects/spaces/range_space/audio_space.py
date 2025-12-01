from __future__ import annotations

from typing import TYPE_CHECKING

from encord.common.range_manager import RangeManager
from encord.constants.enums import SpaceType
from encord.exceptions import LabelRowError
from encord.objects.frames import Ranges
from encord.objects.spaces.range_space.range_space import RangeSpace
from encord.objects.spaces.types import AudioSpaceInfo, ChildInfo, SpaceInfo

if TYPE_CHECKING:
    from encord.objects.ontology_labels_impl import LabelRowV2


class AudioSpace(RangeSpace):
    """Audio space implementation for range-based annotations."""

    def __init__(self, space_id: str, parent: LabelRowV2, duration_ms: int, child_info: ChildInfo):
        super().__init__(space_id, SpaceType.AUDIO, parent)
        self._duration_ms = duration_ms

        self._layout_key = child_info["layout_key"]
        self._is_readonly = child_info["is_readonly"]
        self._file_name = child_info["file_name"]

    def _are_ranges_valid(self, ranges: Ranges) -> None:
        start_of_range, end_of_range = self._get_start_and_end_of_ranges(ranges)

        if start_of_range < 0:
            raise LabelRowError(f"Range starting with {start_of_range} is invalid. Negative ranges are not supported.")

        if end_of_range > self._duration_ms:
            raise LabelRowError(
                f"Range ending with {end_of_range} is invalid. This audio file is only {self._duration_ms} ms long."
            )

    @property
    def layout_key(self) -> str:
        return self._layout_key

    @property
    def is_readonly(self) -> bool:
        return self._is_readonly

    def _to_space_dict(self) -> SpaceInfo:
        labels = self._build_labels_dict()
        return AudioSpaceInfo(
            space_type=SpaceType.AUDIO,
            duration_ms=self._duration_ms,
            labels=labels,
            info={
                "layout_key": self._layout_key,
                "is_readonly": self._is_readonly,
                "file_name": self._file_name,
            },
        )
