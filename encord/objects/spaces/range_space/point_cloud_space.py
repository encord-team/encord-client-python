from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Union, cast

from encord.common.bitmask_operations.bitmask_operations import (
    _rle_to_string,
    rle_string_to_points,
    sparse_indices_to_rle_counts,
)
from encord.common.range_manager import RangeManager
from encord.common.time_parser import format_datetime_to_long_string
from encord.constants.enums import SpaceType
from encord.exceptions import LabelRowError
from encord.objects.common import Shape
from encord.objects.frames import Ranges, frames_to_ranges
from encord.objects.spaces.annotation.base_annotation import _AnnotationMetadata
from encord.objects.spaces.range_space.range_space import RangeSpace
from encord.objects.spaces.types import PointCloudFileSpaceInfo, SceneMetadata, SpaceInfo
from encord.objects.types import (
    FrameObject,
    LabelBlob,
    ObjectAnswer,
    ObjectAnswerForGeometric,
    ObjectAnswerForNonGeometric,
    SegmentationObject,
    SpaceFrameData,
)
from encord.objects.utils import _lower_snake_case

if TYPE_CHECKING:
    from encord.objects.ontology_labels_impl import LabelRowV2


class PointCloudFileSpace(RangeSpace):
    metadata: SceneMetadata

    def __init__(self, space_id: str, label_row: LabelRowV2, space_info: PointCloudFileSpaceInfo):
        super().__init__(space_id, label_row, space_info)
        self._scene_info = space_info["scene_info"]

    def _are_ranges_valid(self, ranges: Ranges) -> None:
        start_of_range, _ = self._get_start_and_end_of_ranges(ranges)
        # we do not have information on the numnber of points in the point cloud file

        if start_of_range < 0:
            raise LabelRowError(f"Range starting with {start_of_range} is invalid. Negative ranges are not supported.")

    def _parse_space_dict(
        self,
        space_info: SpaceInfo,
        object_answers: dict[str, Union[ObjectAnswerForGeometric, ObjectAnswerForNonGeometric]],
        classification_answers: dict[str, Any],
    ) -> None:
        # Point cloud spaces have a single labels dict (not frame-keyed)
        labels = cast(LabelBlob, space_info.get("labels", {}))

        for obj_data in labels.get("objects", []):
            segmentation = obj_data.get("segmentation", "")
            if not isinstance(segmentation, str) or not segmentation:
                continue

            points = rle_string_to_points(segmentation)
            ranges = frames_to_ranges(points)

            if not ranges:
                continue

            object_instance = self._create_new_object(
                feature_hash=obj_data["featureHash"], object_hash=obj_data["objectHash"]
            )

            frame_info_dict = {k: v for k, v in obj_data.items() if v is not None}
            frame_info_dict.setdefault("confidence", 1.0)
            object_frame_instance_info = _AnnotationMetadata.from_dict(cast(Any, frame_info_dict))

            self.put_object_instance(
                object_instance=object_instance,
                ranges=ranges,
                created_at=object_frame_instance_info.created_at,
                created_by=object_frame_instance_info.created_by,
                last_edited_at=object_frame_instance_info.last_edited_at,
                last_edited_by=object_frame_instance_info.last_edited_by,
                manual_annotation=object_frame_instance_info.manual_annotation,
                confidence=object_frame_instance_info.confidence,
            )

    def _build_labels_dict(self) -> LabelBlob:
        objects: list[FrameObject] = []

        for obj in self.get_object_instances():
            ontology_object = obj._ontology_object
            range_manager = self._object_hash_to_range_manager[obj.object_hash]
            annotation_metadata = obj._instance_metadata

            segmentation_obj: SegmentationObject = {
                "shape": Shape.SEGMENTATION,
                "objectHash": obj.object_hash,
                "featureHash": obj.feature_hash,
                "name": ontology_object.name,
                "color": ontology_object.color,
                "value": _lower_snake_case(ontology_object.name),
                "segmentation": _to_rle_string(range_manager),
                "createdAt": format_datetime_to_long_string(annotation_metadata.created_at),
                "lastEditedAt": format_datetime_to_long_string(annotation_metadata.last_edited_at),
                "confidence": annotation_metadata.confidence,
                "manualAnnotation": annotation_metadata.manual_annotation,
            }

            if annotation_metadata.created_by is not None:
                segmentation_obj["createdBy"] = annotation_metadata.created_by
            if annotation_metadata.last_edited_by is not None:
                segmentation_obj["lastEditedBy"] = annotation_metadata.last_edited_by

            objects.append(segmentation_obj)

        return {"objects": objects, "classifications": []}

    def _to_object_answers(self, existing_object_answers: Dict[str, ObjectAnswer]) -> dict[str, ObjectAnswer]:
        ret: Dict[str, ObjectAnswerForNonGeometric] = {}

        for obj in self.get_object_instances():
            annotation_metadata = obj._instance_metadata

            does_obj_exist = obj.object_hash in existing_object_answers

            if does_obj_exist:
                existing_object_answer = cast(ObjectAnswerForNonGeometric, existing_object_answers[obj.object_hash])
                space_data: SpaceFrameData = {"range": [], "type": "frame"}
                existing_object_answer["spaces"][self.space_id] = space_data
                ret[obj.object_hash] = existing_object_answer
            else:
                all_static_answers = self._label_row._get_all_static_answers(obj)

                new_space_data: SpaceFrameData = {"range": [], "type": "frame"}
                object_answer: ObjectAnswerForNonGeometric = {
                    "classifications": list(reversed(all_static_answers)),
                    "objectHash": obj.object_hash,
                    "createdAt": format_datetime_to_long_string(annotation_metadata.created_at),
                    "lastEditedAt": format_datetime_to_long_string(annotation_metadata.last_edited_at),
                    "manualAnnotation": annotation_metadata.manual_annotation,
                    "featureHash": obj.feature_hash,
                    "name": obj.ontology_item.name,
                    "color": obj.ontology_item.color,
                    "shape": Shape.SEGMENTATION,
                    "value": _lower_snake_case(obj.ontology_item.name),
                    "range": [],
                    "spaces": {self.space_id: new_space_data},
                }

                # Only include createdBy and lastEditedBy if they have actual values
                # When None, the backend will use the current user as default
                if annotation_metadata.created_by is not None:
                    object_answer["createdBy"] = annotation_metadata.created_by
                if annotation_metadata.last_edited_by is not None:
                    object_answer["lastEditedBy"] = annotation_metadata.last_edited_by

                ret[obj.object_hash] = object_answer

        return cast(dict[str, ObjectAnswer], ret)

    def _to_space_dict(self) -> PointCloudFileSpaceInfo:
        labels = self._build_labels_dict()
        return PointCloudFileSpaceInfo(
            space_type=SpaceType.POINT_CLOUD,
            scene_info=self._scene_info,
            labels=labels,
        )


def _to_rle_string(manager: RangeManager) -> str:
    points: list[int] = []
    for range_obj in manager.get_ranges():
        points.extend(range(range_obj.start, range_obj.end + 1))
    rle_counts = sparse_indices_to_rle_counts(points)
    return _rle_to_string(rle_counts)
