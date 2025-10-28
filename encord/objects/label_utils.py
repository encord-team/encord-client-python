from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, TypedDict, Unpack

from encord.common.time_parser import format_datetime_to_long_string_optional
from encord.objects.attributes import Attribute
from encord.objects.spaces.annotation.base_annotation import Annotation, AnnotationInfo
from encord.objects.spaces.annotation_instance.base_instance import BaseObjectInstance
from encord.objects.utils import _lower_snake_case

if TYPE_CHECKING:
    from encord.objects import Object, ObjectInstance, Classification


def create_frame_object_dict(
    ontology_object: Object,
    object_instance_annotation: AnnotationInfo,
    object_hash: str
) -> Dict[str, Any]:
    frame_object_dict: Dict[str, Any] = {}

    frame_object_dict["name"] = ontology_object.name
    frame_object_dict["color"] = ontology_object.color
    frame_object_dict["shape"] = ontology_object.shape.value
    frame_object_dict["value"] = _lower_snake_case(ontology_object.name)
    frame_object_dict["createdAt"] = format_datetime_to_long_string_optional(object_instance_annotation.created_at)
    frame_object_dict["createdBy"] = object_instance_annotation.created_by
    frame_object_dict["confidence"] = object_instance_annotation.confidence
    frame_object_dict["objectHash"] = object_hash
    frame_object_dict["featureHash"] = ontology_object.feature_node_hash
    frame_object_dict["manualAnnotation"] = object_instance_annotation.manual_annotation

    if object_instance_annotation.last_edited_at is not None:
        frame_object_dict["lastEditedAt"] = format_datetime_to_long_string_optional(
            object_instance_annotation.last_edited_at
        )
    if object_instance_annotation.last_edited_by is not None:
        frame_object_dict["lastEditedBy"] = object_instance_annotation.last_edited_by
    if object_instance_annotation.is_deleted is not None:
        frame_object_dict["isDeleted"] = object_instance_annotation.is_deleted

    return frame_object_dict


def create_frame_classification_dict(
    ontology_classification: Classification,
    classification_instance_annotation: AnnotationInfo,
    classification_hash: str,
    attribute: Attribute,
) -> Dict[str, Any]:
    frame_classification_dict: Dict[str, Any] = {}

    frame_classification_dict["name"] = attribute.name
    frame_classification_dict["value"] = _lower_snake_case(attribute.name)
    frame_classification_dict["createdAt"] = format_datetime_to_long_string_optional(classification_instance_annotation.created_at)
    frame_classification_dict["createdBy"] = classification_instance_annotation.created_by
    frame_classification_dict["confidence"] = classification_instance_annotation.confidence
    frame_classification_dict["featureHash"] = ontology_classification.feature_node_hash
    frame_classification_dict["classificationHash"] = classification_hash
    frame_classification_dict["manualAnnotation"] = classification_instance_annotation.manual_annotation

    if classification_instance_annotation.last_edited_at is not None:
        frame_classification_dict["lastEditedAt"] = format_datetime_to_long_string_optional(
            classification_instance_annotation.last_edited_at
        )
    if classification_instance_annotation.last_edited_by is not None:
        frame_classification_dict["lastEditedBy"] = classification_instance_annotation.last_edited_by

    return frame_classification_dict
