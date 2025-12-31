from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Literal, Optional, Union, cast

from encord.common.time_parser import format_datetime_to_long_string, format_datetime_to_long_string_optional
from encord.constants.enums import SpaceType
from encord.exceptions import LabelRowError
from encord.objects import ClassificationInstance, Shape
from encord.objects.coordinates import HtmlCoordinates
from encord.objects.html_node import HtmlNode, HtmlRange, HtmlRanges
from encord.objects.ontology_object_instance import ObjectInstance
from encord.objects.spaces.annotation.base_annotation import _AnnotationData, _AnnotationMetadata
from encord.objects.spaces.annotation.html_annotation import (
    _HtmlClassificationAnnotation,
    _HtmlObjectAnnotation,
)
from encord.objects.spaces.base_space import Space
from encord.objects.spaces.types import HtmlSpaceInfo, SpaceInfo
from encord.objects.types import (
    AttributeDict,
    ClassificationAnswer,
    LabelBlob,
    ObjectAnswer,
    ObjectAnswerForGeometric,
    ObjectAnswerForNonGeometric,
    SpaceRange,
)
from encord.objects.utils import _lower_snake_case

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from encord.objects.ontology_labels_impl import LabelRowV2

HtmlOverlapStrategy = Union[Literal["error"], Literal["replace"]]


class HTMLSpace(Space):
    """HTML space implementation for XPath-based annotations.

    This space handles annotations on HTML content where positions are
    specified using XPath expressions with character offsets.
    """

    def __init__(self, space_id: str, label_row: LabelRowV2):
        super().__init__(space_id, label_row)
        self._objects_map: dict[str, ObjectInstance] = dict()
        self._classifications_map: dict[str, ClassificationInstance] = dict()
        self._classification_hash_to_annotation_data: dict[str, _AnnotationData] = dict()
        self._object_hash_to_html_ranges: dict[str, HtmlRanges] = dict()

        # Since we can only have one classification of a particular class, this keeps track to make sure we don't add duplicates
        self._classification_ontologies: set[str] = set()

    def put_object_instance(
        self,
        object_instance: ObjectInstance,
        ranges: Union[HtmlRange, List[HtmlRange]],
        *,
        on_overlap: HtmlOverlapStrategy = "error",
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
    ) -> None:
        """Add an object instance to the HTML space.

        Args:
            object_instance: The object instance to add to the space.
            ranges: HtmlRange or list of HtmlRange specifying the XPath-based location(s) for the annotation.
            on_overlap: Strategy for handling existing annotations.
                - "error" (default): Raises an error if annotation already exists.
                - "replace": Replaces existing annotation.
            created_at: Optional timestamp when the annotation was created.
            created_by: Optional identifier of who created the annotation.
            last_edited_at: Optional timestamp when the annotation was last edited.
            last_edited_by: Optional identifier of who last edited the annotation.
            confidence: Optional confidence score for the annotation (0.0 to 1.0).
            manual_annotation: Optional flag indicating if this was manually annotated.

        Raises:
            LabelRowError: If annotation already exists when on_overlap="error".
        """
        self._method_not_supported_for_object_instance_with_frames(object_instance=object_instance)
        self._method_not_supported_for_object_instance_with_dynamic_attributes(object_instance=object_instance)

        # Normalize to list of HtmlRange
        if isinstance(ranges, HtmlRange):
            ranges_list = [ranges]
        else:
            ranges_list = ranges

        already_exists = object_instance.object_hash in self._objects_map

        if already_exists and on_overlap == "error":
            raise LabelRowError(
                f"Annotation for object instance {object_instance.object_hash} already exists. "
                "Set 'on_overlap' to 'replace' to overwrite existing annotations."
            )

        self._objects_map[object_instance.object_hash] = object_instance
        object_instance._add_to_space(self)

        object_instance._instance_metadata.update_from_optional_fields(
            created_at=created_at,
            created_by=created_by,
            last_edited_at=last_edited_at,
            last_edited_by=last_edited_by,
            confidence=confidence,
            manual_annotation=manual_annotation,
        )

        self._object_hash_to_html_ranges[object_instance.object_hash] = ranges_list

    def put_classification_instance(
        self,
        classification_instance: ClassificationInstance,
        *,
        on_overlap: HtmlOverlapStrategy = "error",
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
    ) -> None:
        """Add a classification instance to the HTML space.

        Args:
            classification_instance: The classification instance to add to the space.
            on_overlap: Strategy for handling existing classifications.
                - "error" (default): Raises an error if classification of the same ontology item already exists.
                - "replace": Overwrites existing classifications.
            created_at: Optional timestamp when the annotation was created.
            created_by: Optional identifier of who created the annotation.
            last_edited_at: Optional timestamp when the annotation was last edited.
            last_edited_by: Optional identifier of who last edited the annotation.
            confidence: Optional confidence score for the annotation (0.0 to 1.0).
            manual_annotation: Optional flag indicating if this was manually annotated.

        Raises:
            LabelRowError: If classification already exists when on_overlap="error".
        """
        self._method_not_supported_for_classification_instance_with_frames(
            classification_instance=classification_instance
        )
        is_classification_of_same_ontology_present = (
            classification_instance._ontology_classification.feature_node_hash in self._classification_ontologies
        )

        if is_classification_of_same_ontology_present and on_overlap == "error":
            ontology_classification = classification_instance._ontology_classification
            raise LabelRowError(
                f"Annotation for the classification '{ontology_classification.title}' already exists. "
                "Set the 'on_overlap' parameter to 'replace' to overwrite this annotation."
            )
        elif is_classification_of_same_ontology_present and on_overlap == "replace":
            classification_to_remove = None
            for existing_classification_instance in self._classifications_map.values():
                if (
                    existing_classification_instance._ontology_classification.feature_node_hash
                    == classification_instance._ontology_classification.feature_node_hash
                ):
                    classification_to_remove = existing_classification_instance

            if classification_to_remove is not None:
                self._classifications_map.pop(classification_to_remove.classification_hash)
                self._classification_hash_to_annotation_data.pop(classification_to_remove.classification_hash)

        self._classifications_map[classification_instance.classification_hash] = classification_instance
        classification_instance._add_to_space(self)

        existing_annotation_data = self._classification_hash_to_annotation_data.get(
            classification_instance.classification_hash
        )

        if existing_annotation_data is None:
            existing_annotation_data = _AnnotationData(
                annotation_metadata=_AnnotationMetadata(),
            )

            self._classification_hash_to_annotation_data[classification_instance.classification_hash] = (
                existing_annotation_data
            )

        existing_annotation_data.annotation_metadata.update_from_optional_fields(
            created_at=created_at,
            created_by=created_by,
            last_edited_at=last_edited_at,
            last_edited_by=last_edited_by,
            confidence=confidence,
            manual_annotation=manual_annotation,
        )

        self._classification_ontologies.add(classification_instance._ontology_classification.feature_node_hash)

    def _create_object_annotation(self, obj_hash: str) -> _HtmlObjectAnnotation:
        return _HtmlObjectAnnotation(space=self, object_instance=self._objects_map[obj_hash])

    def _create_classification_annotation(self, classification_hash: str) -> _HtmlClassificationAnnotation:
        return _HtmlClassificationAnnotation(
            space=self, classification_instance=self._classifications_map[classification_hash]
        )

    def get_object_instance_annotations(
        self, filter_object_instances: Optional[list[str]] = None
    ) -> List[_HtmlObjectAnnotation]:
        """Get all object instance annotations in the html space.

        Args:
            filter_object_instances: Optional list of object hashes to filter by.
                If provided, only annotations for these objects will be returned.

        Returns:
            List[_HtmlObjectAnnotation]: List of all object annotations
        """

        filter_set = set(filter_object_instances) if filter_object_instances is not None else None
        return [
            self._create_object_annotation(obj_hash)
            for obj_hash in self._objects_map.keys()
            if filter_set is None or obj_hash in filter_set
        ]

    def remove_object_instance(self, object_hash: str) -> Optional[ObjectInstance]:
        """Remove an object instance from the HTML space.

        Args:
            object_hash: The hash identifier of the object instance to remove.

        Returns:
            Optional[ObjectInstance]: The removed object instance, or None if the object wasn't found.
        """
        object_instance = self._objects_map.pop(object_hash, None)
        self._object_hash_to_html_ranges.pop(object_hash, None)
        if object_instance is not None:
            object_instance._remove_from_space(self.space_id)

        return object_instance

    def remove_classification_instance(self, classification_hash: str) -> Optional[ClassificationInstance]:
        """Remove a classification instance from the HTML space.

        Args:
            classification_hash: The hash identifier of the classification instance to remove.

        Returns:
            Optional[ClassificationInstance]: The removed classification instance, or None if the classification wasn't found.
        """
        classification_instance = self._classifications_map.pop(classification_hash, None)

        if classification_instance is not None:
            classification_instance._remove_from_space(self.space_id)
            self._classification_hash_to_annotation_data.pop(classification_hash)
            self._classification_ontologies.remove(classification_instance._ontology_classification.feature_node_hash)

        return classification_instance

    def _create_new_object(self, feature_hash: str, object_hash: str) -> ObjectInstance:
        from encord.objects.ontology_object import Object, ObjectInstance

        ontology = self._label_row._ontology.structure
        label_class = ontology.get_child_by_hash(feature_hash, type_=Object)
        return ObjectInstance(ontology_object=label_class, object_hash=object_hash)

    def _build_labels_dict(self) -> dict[str, LabelBlob]:
        """For HTML-based annotations, labels are stored in objects/classifications index"""
        return {}

    def _to_space_dict(self) -> HtmlSpaceInfo:
        """Export HTML space to dictionary format."""
        labels = self._build_labels_dict()
        return HtmlSpaceInfo(
            space_type=SpaceType.HTML,
            labels=labels,
        )

    def _parse_space_dict(
        self,
        space_info: SpaceInfo,
        object_answers: dict[str, Union[ObjectAnswerForGeometric, ObjectAnswerForNonGeometric]],
        classification_answers: dict[str, ClassificationAnswer],
    ) -> None:
        for object_answer in object_answers.values():
            if "spaces" not in object_answer:
                # skip this object_answer, it is not on a space
                continue

            non_geometric_object_answer = cast(ObjectAnswerForNonGeometric, object_answer)
            object_info_on_this_space = non_geometric_object_answer["spaces"].get(self.space_id)
            if object_info_on_this_space is None:
                continue

            # Parse HTML ranges from dict format
            html_ranges = self._parse_html_ranges_from_space_info(object_info_on_this_space)  # type: ignore[arg-type]

            object_instance = self._create_new_object(
                object_hash=non_geometric_object_answer["objectHash"],
                feature_hash=non_geometric_object_answer["featureHash"],
            )

            frame_info_dict = {k: v for k, v in object_answer.items() if v is not None}
            frame_info_dict.setdefault("confidence", 1.0)
            object_frame_instance_info = _AnnotationMetadata.from_dict(frame_info_dict)  # type: ignore[arg-type]

            self.put_object_instance(
                object_instance=object_instance,
                ranges=html_ranges,
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
            annotation_metadata = _AnnotationMetadata.from_dict(classification_answer)  # type: ignore[arg-type]

            self.put_classification_instance(
                classification_instance=classification_instance,
                created_at=annotation_metadata.created_at,
                created_by=annotation_metadata.created_by,
                confidence=annotation_metadata.confidence,
                manual_annotation=annotation_metadata.manual_annotation,
                last_edited_at=annotation_metadata.last_edited_at,
                last_edited_by=annotation_metadata.last_edited_by,
            )

    def _parse_html_ranges_from_space_info(self, space_info: dict) -> List[HtmlRange]:
        raw_ranges = space_info.get("range", [])
        html_ranges: List[HtmlRange] = []

        for raw_range in raw_ranges:
            # Backend returns tuples: [start_node, end_node]
            start_data = raw_range[0]
            end_data = raw_range[1]
            html_range = HtmlRange(
                start=HtmlNode(xpath=start_data["xpath"], offset=start_data["offset"]),
                end=HtmlNode(xpath=end_data["xpath"], offset=end_data["offset"]),
            )
            html_ranges.append(html_range)

        return html_ranges

    def _html_ranges_to_dict(self, ranges: HtmlRanges) -> list:
        # Backend expects tuples: [[start_node, end_node], ...]
        return [
            [
                {"xpath": html_range.start.xpath, "offset": html_range.start.offset},
                {"xpath": html_range.end.xpath, "offset": html_range.end.offset},
            ]
            for html_range in ranges
        ]

    def _to_object_answers(self, existing_object_answers: Dict[str, ObjectAnswer]) -> dict[str, ObjectAnswer]:
        ret: Dict[str, ObjectAnswerForNonGeometric] = {}

        for obj in self.get_object_instances():
            coordinates = self._object_hash_to_html_ranges[obj.object_hash]
            annotation_metadata = obj._instance_metadata
            ranges = self._html_ranges_to_dict(coordinates)
            does_obj_exist = obj.object_hash in existing_object_answers

            if does_obj_exist:
                existing_object_answer = cast(ObjectAnswerForNonGeometric, existing_object_answers[obj.object_hash])
                space_range_to_add: SpaceRange = {"range": ranges, "type": "html"}
                existing_object_answer["spaces"][self.space_id] = space_range_to_add
            else:
                shape = cast(Literal[Shape.TEXT], obj.ontology_item.shape.value)
                all_static_answers = self._label_row._get_all_static_answers(obj)

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
                    "spaces": {self.space_id: {"range": ranges, "type": "html"}},
                }

                ret[obj.object_hash] = object_answer

        return cast(dict[str, ObjectAnswer], ret)

    def _to_classification_answers(
        self, existing_classification_answers: dict[str, ClassificationAnswer]
    ) -> dict[str, ClassificationAnswer]:
        ret: dict[str, ClassificationAnswer] = {}

        for classification in self.get_classification_instances():
            does_classification_exist = classification.classification_hash in existing_classification_answers

            if does_classification_exist:
                existing_classification_answer = existing_classification_answers[classification.classification_hash]
                space_range_to_add: SpaceRange = {"range": [], "type": "html"}
                spaces = existing_classification_answer["spaces"]

                if spaces is None:
                    spaces = {}

                spaces[self.space_id] = space_range_to_add
                ret[classification.classification_hash] = existing_classification_answer
            else:
                all_static_answers = classification.get_all_static_answers()
                annotation = self._classification_hash_to_annotation_data[classification.classification_hash]
                annotation_metadata = annotation.annotation_metadata
                classification_attributes = [
                    answer.to_encord_dict() for answer in all_static_answers if answer.is_answered()
                ]
                classification_attributes_without_none = cast(list[AttributeDict], classification_attributes)

                classification_answer: ClassificationAnswer = {
                    "classifications": list(reversed(classification_attributes_without_none)),
                    "classificationHash": classification.classification_hash,
                    "featureHash": classification.feature_hash,
                    "range": [],
                    "createdBy": annotation_metadata.created_by,
                    "createdAt": format_datetime_to_long_string_optional(annotation_metadata.created_at),
                    "lastEditedBy": annotation_metadata.last_edited_by,
                    "lastEditedAt": format_datetime_to_long_string_optional(annotation_metadata.last_edited_at),
                    "manualAnnotation": annotation_metadata.manual_annotation,
                    "spaces": {self.space_id: {"range": [], "type": "html"}},
                }

                ret[classification.classification_hash] = classification_answer

        return ret
