from __future__ import annotations

from typing import TYPE_CHECKING

from encord.constants.enums import SpaceType
from encord.exceptions import LabelRowError
from encord.objects.frames import Ranges
from encord.objects.spaces.range_space.range_space import RangeSpace
from encord.objects.spaces.types import RootSpaceMetadata, SpaceInfo, TimeSeriesSpaceInfo

if TYPE_CHECKING:
    from encord.objects.ontology_labels_impl import LabelRowV2


class TimeSeriesSpace(RangeSpace):
    def __init__(self, space_id: str, label_row: LabelRowV2, space_info: SpaceInfo):
        super().__init__(space_id, label_row, space_info)

    def _are_ranges_valid(self, ranges: Ranges) -> None:
        start_of_range, _ = self._get_start_and_end_of_ranges(ranges)

        if start_of_range < 0:
            raise LabelRowError(f"Range starting with {start_of_range} is invalid. Negative ranges are not supported.")

    def _to_space_dict(self) -> SpaceInfo:
        space_info = TimeSeriesSpaceInfo(
            space_type=SpaceType.TIME_SERIES,
            labels={},
        )
        if isinstance(self.metadata, RootSpaceMetadata):
            space_info["root_info"] = {"file_name": self.metadata.file_name}

        return space_info
