from __future__ import annotations

from typing import TYPE_CHECKING, Any, MutableMapping, Optional, cast

from encord.constants.enums import SpaceType
from encord.objects.constants import ROOT_SPACE_ID
from encord.objects.spaces.base_space import Space
from encord.objects.spaces.range_space.point_cloud_space import PointCloudFileSpace
from encord.objects.spaces.range_space.time_series_space import TimeSeriesSpace
from encord.objects.spaces.types import PointCloudFileSpaceInfo, SpaceInfo, TimeSeriesSpaceInfo
from encord.objects.types import ClassificationAnswer, LabelBlob, ObjectAnswer

if TYPE_CHECKING:
    from encord.objects.ontology_labels_impl import LabelRowV2


class McapSpaceManager:
    """Manage spaces inferred from self-contained MCAP labels and caller-supplied IDs."""

    def __init__(self, label_row: LabelRowV2, space_map: MutableMapping[str, Space]) -> None:
        self._label_row = label_row
        self._space_map = space_map
        self._point_cloud_space_ids: set[str] = set()
        self._time_series_space_ids: set[str] = set()

    def reset(self) -> None:
        """Remove spaces inferred from the previous label payload."""
        for space_id in self._point_cloud_space_ids | self._time_series_space_ids:
            self._space_map.pop(space_id, None)
        self._point_cloud_space_ids.clear()
        self._time_series_space_ids.clear()

    def add_labels_to_spaces(
        self,
        label_row_dict: dict[str, Any],
        spaces_dict: dict[str, SpaceInfo],
        *,
        object_answers: dict[str, ObjectAnswer],
        classification_answers: dict[str, ClassificationAnswer],
    ) -> dict[str, SpaceInfo]:
        """Recover MCAP point-cloud and time-series spaces omitted from top-level metadata."""
        ret = self._add_point_cloud_labels_to_spaces(label_row_dict, spaces_dict)
        return self._add_time_series_labels_to_spaces(
            ret,
            object_answers=object_answers,
            classification_answers=classification_answers,
        )

    def get_or_create_point_cloud_space(self, label_key: str) -> Optional[PointCloudFileSpace]:
        """Trust a valid ``stream@timestamp_ns`` point-cloud ID supplied by a caller."""
        if self._point_cloud_stream(label_key) is None:
            return None

        existing = self._space_map.get(label_key)
        if existing is not None:
            return existing if isinstance(existing, PointCloudFileSpace) else None

        space = PointCloudFileSpace(
            space_id=label_key,
            label_row=self._label_row,
            space_info=self._point_cloud_space_info(label_key, None),
        )
        self._space_map[label_key] = space
        self._point_cloud_space_ids.add(label_key)
        return space

    def get_or_create_time_series_space(self, space_id: str) -> Optional[TimeSeriesSpace]:
        """Trust a non-empty time-series channel ID supplied by a caller."""
        if not space_id or space_id == ROOT_SPACE_ID:
            return None

        existing = self._space_map.get(space_id)
        if existing is not None:
            return existing if isinstance(existing, TimeSeriesSpace) else None

        space = TimeSeriesSpace(
            space_id=space_id,
            label_row=self._label_row,
            space_info=cast(SpaceInfo, self._time_series_space_info(space_id)),
        )
        self._space_map[space_id] = space
        self._time_series_space_ids.add(space_id)
        return space

    def prepare_export(self, label_row_dict: dict[str, Any]) -> None:
        """Restore MCAP labels to their wire locations and omit synthetic space metadata."""
        self._move_point_cloud_labels_to_data_units(label_row_dict)
        for space_id in self._time_series_space_ids:
            label_row_dict["spaces"].pop(space_id, None)

    @staticmethod
    def _point_cloud_stream(label_key: str) -> Optional[str]:
        stream_id, separator, timestamp = str(label_key).rpartition("@")
        if not separator or not stream_id or not timestamp.isdigit():
            return None
        return stream_id

    def _point_cloud_space_info(self, label_key: str, labels: Optional[LabelBlob]) -> PointCloudFileSpaceInfo:
        stream_id = self._point_cloud_stream(label_key)
        assert stream_id is not None
        return {
            "space_type": SpaceType.POINT_CLOUD,
            "scene_info": {"stream_id": stream_id, "event_index": 0, "uri": label_key},
            "labels": labels if labels is not None else {"objects": [], "classifications": []},
        }

    def _add_point_cloud_labels_to_spaces(
        self, label_row_dict: dict[str, Any], spaces_dict: dict[str, SpaceInfo]
    ) -> dict[str, SpaceInfo]:
        ret = dict(spaces_dict)
        for data_unit in label_row_dict["data_units"].values():
            for label_key, labels in data_unit.get("labels", {}).items():
                if label_key in ret or self._point_cloud_stream(label_key) is None:
                    continue
                space_info = self._point_cloud_space_info(label_key, cast(LabelBlob, labels))
                self._space_map[label_key] = PointCloudFileSpace(
                    space_id=label_key,
                    label_row=self._label_row,
                    space_info=space_info,
                )
                self._point_cloud_space_ids.add(label_key)
                ret[label_key] = cast(SpaceInfo, space_info)
        return ret

    def _move_point_cloud_labels_to_data_units(self, label_row_dict: dict[str, Any]) -> None:
        data_unit = label_row_dict["data_units"].get(self._label_row.data_hash)
        if data_unit is None:
            return

        data_unit_labels = data_unit.setdefault("labels", {})
        for space_id in self._point_cloud_space_ids:
            space_info = label_row_dict["spaces"].pop(space_id, None)
            if space_info is None:
                continue
            labels = space_info.get("labels") or {"objects": [], "classifications": []}
            if labels.get("objects") or labels.get("classifications"):
                data_unit_labels[space_id] = labels

    @staticmethod
    def _time_series_space_info(space_id: str) -> TimeSeriesSpaceInfo:
        return {
            "space_type": SpaceType.TIME_SERIES,
            "child_info": {"layout_key": space_id, "file_name": space_id, "data_link": None},
            "labels": {},
        }

    def _add_time_series_labels_to_spaces(
        self,
        spaces_dict: dict[str, SpaceInfo],
        *,
        object_answers: dict[str, ObjectAnswer],
        classification_answers: dict[str, ClassificationAnswer],
    ) -> dict[str, SpaceInfo]:
        ret = dict(spaces_dict)
        answer_space_ids: set[str] = set()
        for object_answer in object_answers.values():
            answer_space_ids.update(cast(dict[str, Any], object_answer.get("spaces") or {}))
        for classification_answer in classification_answers.values():
            answer_space_ids.update(classification_answer.get("spaces") or {})

        for space_id in answer_space_ids:
            if not space_id or space_id == ROOT_SPACE_ID or space_id in ret or space_id in self._space_map:
                continue
            space_info = self._time_series_space_info(space_id)
            self._space_map[space_id] = TimeSeriesSpace(
                space_id=space_id,
                label_row=self._label_row,
                space_info=cast(SpaceInfo, space_info),
            )
            self._time_series_space_ids.add(space_id)
            ret[space_id] = cast(SpaceInfo, space_info)
        return ret
