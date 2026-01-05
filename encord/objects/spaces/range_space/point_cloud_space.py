from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Literal, Union, cast

from encord.common.bitmask_operations.bitmask_operations import points_to_rle_string, rle_string_to_points
from encord.common.range_manager import RangeManager
from encord.common.time_parser import format_datetime_to_long_string
from encord.constants.enums import SpaceType
from encord.objects.common import Shape
from encord.objects.frames import Ranges, frames_to_ranges
from encord.objects.spaces.annotation.base_annotation import _AnnotationMetadata
from encord.objects.spaces.range_space.range_space import RangeSpace
from encord.objects.spaces.types import FileInSceneInfo, PointCloudFileSpaceInfo, SceneMetadata, SpaceInfo
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
        pass

    def _parse_space_dict(
        self,
        space_info: SpaceInfo,
        object_answers: dict[str, Union[ObjectAnswerForGeometric, ObjectAnswerForNonGeometric]],
        classification_answers: dict[str, Any],
    ) -> None:
        """Parse object and classification answers from RLE-encoded segmentation.

        Point cloud segmentation can be stored in two places:
        1. object_answers - for objects that span multiple spaces
        2. space_info.labels - for space-specific labels
        """
        # Point cloud spaces have a single labels dict (not frame-keyed)
        labels = space_info.get("labels", {})
        objects_list = cast(list[dict[str, Any]], labels.get("objects", []))

        for obj_data in objects_list:
            segmentation = obj_data.get("segmentation", "")
            if not isinstance(segmentation, str) or not segmentation:
                continue

            points = rle_string_to_points(segmentation)
            ranges = frames_to_ranges(points)

            if not ranges:
                continue

            object_instance = self._create_new_object(
                feature_hash=obj_data["featureHash"],
                object_hash=obj_data["objectHash"],
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

        # Also check object_answers for objects that might have segmentation in spaces
        for object_answer in object_answers.values():
            obj_dict = cast(dict[str, Any], object_answer)

            # Check if this object has space-specific segmentation data
            spaces_data = obj_dict.get("spaces", {})
            space_data = spaces_data.get(self.space_id, {})
            segmentation = space_data.get("segmentation", "")

            if not isinstance(segmentation, str) or not segmentation:
                continue

            # Skip if already parsed from space labels
            if obj_dict.get("objectHash") in self._objects_map:
                continue

            points = rle_string_to_points(segmentation)
            ranges = frames_to_ranges(points)

            if not ranges:
                continue

            object_instance = self._create_new_object(
                feature_hash=obj_dict["featureHash"],
                object_hash=obj_dict["objectHash"],
            )

            frame_info_dict = {k: v for k, v in object_answer.items() if v is not None}
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

        for classification_answer in classification_answers.values():
            classification_instance = self._label_row._create_new_classification_instance_from_answer(
                classification_answer
            )
            if classification_instance is None:
                continue

            annotation_metadata = _AnnotationMetadata.from_dict(classification_answer)

            self.put_classification_instance(
                classification_instance=classification_instance,
                created_at=annotation_metadata.created_at,
                created_by=annotation_metadata.created_by,
                confidence=annotation_metadata.confidence,
                manual_annotation=annotation_metadata.manual_annotation,
                last_edited_at=annotation_metadata.last_edited_at,
                last_edited_by=annotation_metadata.last_edited_by,
            )

    def _build_labels_dict(self) -> LabelBlob:
        """Build labels dict with RLE-encoded segmentation for objects."""
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
                "createdBy": annotation_metadata.created_by,
                "lastEditedAt": format_datetime_to_long_string(annotation_metadata.last_edited_at),
                "lastEditedBy": annotation_metadata.last_edited_by,
                "confidence": annotation_metadata.confidence,
                "manualAnnotation": annotation_metadata.manual_annotation,
            }

            objects.append(segmentation_obj)

        return {"objects": objects, "classifications": []}

    def _to_object_answers(self, existing_object_answers: Dict[str, ObjectAnswer]) -> dict[str, ObjectAnswer]:
        """Override to handle segmentation shape for point cloud objects."""
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
                shape = cast(Literal[Shape.SEGMENTATION], obj.ontology_item.shape.value)
                all_static_answers = self._label_row._get_all_static_answers(obj)

                new_space_data: SpaceFrameData = {"range": [], "type": "frame"}
                object_answer: ObjectAnswerForNonGeometric = {
                    "classifications": list(reversed(all_static_answers)),
                    "objectHash": obj.object_hash,
                    "createdBy": annotation_metadata.created_by,
                    "createdAt": format_datetime_to_long_string(annotation_metadata.created_at),
                    "lastEditedAt": format_datetime_to_long_string(annotation_metadata.last_edited_at),
                    "lastEditedBy": annotation_metadata.last_edited_by,
                    "manualAnnotation": annotation_metadata.manual_annotation,
                    "featureHash": obj.feature_hash,
                    "name": obj.ontology_item.name,
                    "color": obj.ontology_item.color,
                    "shape": shape,
                    "value": _lower_snake_case(obj.ontology_item.name),
                    "range": [],
                    "spaces": {self.space_id: new_space_data},
                }

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
    points: set[int] = set()
    for range_obj in manager.get_ranges():
        points.update(range(range_obj.start, range_obj.end + 1))
    return points_to_rle_string(points)
