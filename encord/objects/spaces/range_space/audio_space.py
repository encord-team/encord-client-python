from __future__ import annotations

from typing import TYPE_CHECKING

from encord.constants.enums import SpaceType
from encord.exceptions import LabelRowError
from encord.objects.frames import Ranges
from encord.objects.spaces.range_space.range_space import RangeSpace
from encord.objects.spaces.types import AudioSpaceInfo, SpaceInfo

if TYPE_CHECKING:
    from encord.objects.ontology_labels_impl import LabelRowV2


class AudioSpace(RangeSpace):
    """Audio space implementation for range-based annotations."""

    def __init__(self, space_id: str, label_row: LabelRowV2, space_info: SpaceInfo, duration_ms: int):
        super().__init__(space_id, label_row, space_info)
        self._duration_ms = duration_ms

    def _are_ranges_valid(self, ranges: Ranges) -> None:
        start_of_range, end_of_range = self._get_start_and_end_of_ranges(ranges)

        if start_of_range < 0:
            raise LabelRowError(f"Range starting with {start_of_range} is invalid. Negative ranges are not supported.")

        if end_of_range > self._duration_ms:
            raise LabelRowError(
                f"Range ending with {end_of_range} is invalid. This audio file is only {self._duration_ms} ms long."
            )

    def _to_space_dict(self) -> SpaceInfo:
        return AudioSpaceInfo(
            space_type=SpaceType.AUDIO,
            duration_ms=self._duration_ms,
            labels={},
        )
