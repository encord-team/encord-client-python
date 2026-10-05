from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Optional

from encord.common.time_parser import format_datetime_to_long_string
from encord.objects.attributes import Attribute
from encord.objects.spaces.annotation.base_annotation import _AnnotationMetadata
from encord.objects.types import BaseFrameObject, FrameClassification
from encord.objects.utils import _lower_snake_case

if TYPE_CHECKING:
    from encord.objects import Classification, Object


def _read_object_id(source: Mapping[str, Any]) -> Optional[int]:
    """Read a caller-visible objectID from a payload fragment."""
    value = source.get("objectId")
    if value is None:
        value = source.get("objectID")
    return value


def create_frame_object_dict(
    ontology_object: Object, object_instance_annotation: _AnnotationMetadata, object_hash: str
) -> BaseFrameObject:
    frame_object_dict: BaseFrameObject = {
        "objectHash": object_hash,
        "featureHash": ontology_object.feature_node_hash,
        "name": ontology_object.name,
        "color": ontology_object.color,
        "value": _lower_snake_case(ontology_object.name),
        "createdAt": format_datetime_to_long_string(object_instance_annotation.created_at),
        "manualAnnotation": object_instance_annotation.manual_annotation,
        "confidence": object_instance_annotation.confidence,
    }

    if object_instance_annotation.last_edited_at is not None:
        frame_object_dict["lastEditedAt"] = format_datetime_to_long_string(object_instance_annotation.last_edited_at)
    if object_instance_annotation.last_edited_by is not None:
        frame_object_dict["lastEditedBy"] = object_instance_annotation.last_edited_by
    if object_instance_annotation.created_by is not None:
        frame_object_dict["createdBy"] = object_instance_annotation.created_by

    if object_instance_annotation.is_deleted is not None:
        frame_object_dict["isDeleted"] = object_instance_annotation.is_deleted

    return frame_object_dict


def create_frame_classification_dict(
    ontology_classification: Classification,
    classification_instance_annotation: _AnnotationMetadata,
    classification_hash: str,
    attribute: Attribute,
) -> FrameClassification:
    frame_classification_dict: FrameClassification = {
        "classificationHash": classification_hash,
        "featureHash": ontology_classification.feature_node_hash,
        "name": attribute.name,
        "value": _lower_snake_case(attribute.name),
        "createdAt": format_datetime_to_long_string(classification_instance_annotation.created_at),
        "confidence": classification_instance_annotation.confidence,
        "manualAnnotation": classification_instance_annotation.manual_annotation,
    }

    if classification_instance_annotation.last_edited_at is not None:
        frame_classification_dict["lastEditedAt"] = format_datetime_to_long_string(
            classification_instance_annotation.last_edited_at
        )
    if classification_instance_annotation.last_edited_by is not None:
        frame_classification_dict["lastEditedBy"] = classification_instance_annotation.last_edited_by

    if classification_instance_annotation.created_by is not None:
        frame_classification_dict["createdBy"] = classification_instance_annotation.created_by

    return frame_classification_dict
