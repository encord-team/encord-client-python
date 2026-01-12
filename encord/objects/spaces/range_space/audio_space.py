from __future__ import annotations

from typing import TYPE_CHECKING, Union, cast

from encord.constants.enums import SpaceType
from encord.exceptions import LabelRowError
from encord.objects.frames import Range, Ranges
from encord.objects.spaces.annotation.base_annotation import _AnnotationMetadata
from encord.objects.spaces.range_space.range_space import RangeSpace
from encord.objects.spaces.types import AudioSpaceInfo, SpaceInfo
from encord.objects.types import BaseFrameObject, ObjectAnswerForGeometric, ObjectAnswerForNonGeometric

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
        labels = self._build_labels_dict()
        return AudioSpaceInfo(
            space_type=SpaceType.AUDIO,
            duration_ms=self._duration_ms,
            labels=labels,
        )

    def _parse_space_dict(
        self,
        space_info: SpaceInfo,
        object_answers: dict[str, Union[ObjectAnswerForGeometric, ObjectAnswerForNonGeometric]],
        classification_answers: dict,
    ) -> None:
        for object_answer in object_answers.values():
            if "spaces" not in object_answer:
                # skip this object_answer, it is not on a space
                continue

            non_geometric_object_answer = cast(ObjectAnswerForNonGeometric, object_answer)
            object_info_on_this_space = non_geometric_object_answer["spaces"].get(self.space_id)
            if object_info_on_this_space is None or object_info_on_this_space["type"] != "frame":
                continue

            range_on_this_space = object_info_on_this_space["range"]
            ranges = [Range(range[0], range[1]) for range in range_on_this_space]

            object_instance = self._create_new_object(
                object_hash=non_geometric_object_answer["objectHash"],
                feature_hash=non_geometric_object_answer["featureHash"],
            )

            frame_info_dict = {k: v for k, v in object_answer.items() if v is not None}
            frame_info_dict.setdefault("confidence", 1.0)  # confidence sometimes not present.
            frame_object_dict = cast(BaseFrameObject, frame_info_dict)
            object_frame_instance_info = _AnnotationMetadata.from_dict(frame_object_dict)

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

            answer_list = object_answer["classifications"]
            object_instance.set_answer_from_list(answer_list)

        for classification_answer in classification_answers.values():
            spaces = classification_answer["spaces"]
            if spaces is None or self.space_id not in spaces:
                continue

            classification_instance = self._label_row._create_new_classification_instance_from_answer(
                classification_answer
            )

            if classification_instance is None:
                continue

            annotation_metadata = _AnnotationMetadata.from_dict(classification_answer)

            self._put_global_classification_instance(
                classification_instance=classification_instance,
                on_overlap="replace",
                created_at=annotation_metadata.created_at,
                created_by=annotation_metadata.created_by,
                confidence=annotation_metadata.confidence,
                manual_annotation=annotation_metadata.manual_annotation,
                last_edited_at=annotation_metadata.last_edited_at,
                last_edited_by=annotation_metadata.last_edited_by,
            )
