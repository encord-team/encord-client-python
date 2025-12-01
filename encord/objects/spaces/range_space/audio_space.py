from __future__ import annotations

from typing import TYPE_CHECKING, Union, cast

from encord.constants.enums import SpaceType
from encord.exceptions import LabelRowError
from encord.objects.frames import Range, Ranges
from encord.objects.spaces.annotation.base_annotation import AnnotationMetadata
from encord.objects.spaces.range_space.range_space import RangeSpace
from encord.objects.spaces.types import AudioSpaceInfo, ChildInfo, SpaceInfo
from encord.objects.types import BaseFrameObject, ObjectAnswer, ObjectAnswerForNonGeometric

if TYPE_CHECKING:
    from encord.objects.ontology_labels_impl import LabelRowV2


class AudioSpace(RangeSpace):
    """Audio space implementation for range-based annotations."""

    def __init__(self, space_id: str, label_row: LabelRowV2, duration_ms: int, child_info: ChildInfo):
        super().__init__(space_id, label_row)
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

    def _parse_space_dict(
        self,
        space_info: SpaceInfo,
        object_answers: dict[str, Union[ObjectAnswer, ObjectAnswerForNonGeometric]],
        classification_answers: dict,
    ) -> None:
        object_answers_for_non_geometric = cast(dict[str, ObjectAnswerForNonGeometric], object_answers)
        for object_answer in object_answers_for_non_geometric.values():
            ranges_in_object_answer = object_answer["range"] if object_answer["range"] is not None else []
            ranges = [Range(range[0], range[1]) for range in ranges_in_object_answer]

            object_instance = self._create_new_object(
                object_hash=object_answer["objectHash"],
                feature_hash=object_answer["featureHash"],
            )

            frame_info_dict = {k: v for k, v in object_answer.items() if v is not None}
            frame_info_dict.setdefault("confidence", 1.0)  # confidence sometimes not present.
            frame_object_dict = cast(BaseFrameObject, frame_info_dict)
            object_frame_instance_info = AnnotationMetadata.from_dict(frame_object_dict)

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
            classification_instance = self._label_row._create_new_classification_instance_with_ranges(
                classification_answer
            )
            annotation_metadata = AnnotationMetadata.from_dict(classification_answer)

            # TODO: Need to use global classifications here
            self.put_classification_instance(
                classification_instance=classification_instance,
                created_at=annotation_metadata.created_at,
                created_by=annotation_metadata.created_by,
                confidence=annotation_metadata.confidence,
                manual_annotation=annotation_metadata.manual_annotation,
                last_edited_at=annotation_metadata.last_edited_at,
                last_edited_by=annotation_metadata.last_edited_by,
            )
