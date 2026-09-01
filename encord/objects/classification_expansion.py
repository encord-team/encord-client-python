from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from encord.constants.enums import DataType, SpaceType
from encord.objects.classification_ranges import resolve_classification_ranges
from encord.objects.constants import DEFAULT_CONFIDENCE, DEFAULT_MANUAL_ANNOTATION, ROOT_SPACE_ID
from encord.objects.frames import ranges_to_frames
from encord.objects.types import ClassificationAnswer, FrameClassification

log = logging.getLogger(__name__)

# Data types whose `labels` are keyed by frame number. Everything else keeps its classifications in
# `classification_answers` only, exactly as the backend has always served them.
_FRAME_KEYED_DATA_TYPES = {
    DataType.VIDEO.value,
    DataType.DICOM.value,
    DataType.NIFTI.value,
    DataType.PDF.value,
    DataType.SCENE.value,
}
_FLAT_LABEL_DATA_TYPES = {DataType.IMAGE.value, DataType.IMG_GROUP.value, DataType.GROUP.value}


def expand_classification_answers_into_frame_labels(label: Dict[str, Any]) -> Dict[str, Any]:
    """Mutates a label row to expand its ``classification_answers`` into frame classifications, and
    places them onto their spaces/data-units."""

    classification_answers: dict[str, ClassificationAnswer] = label.get("classification_answers", {})
    if not classification_answers:
        return label

    data_type = label.get("data_type")
    spaces = label.get("spaces", {})

    for answer in classification_answers.values():
        frame_classification = _to_frame_classification(answer)
        if frame_classification is None:
            continue

        resolved_ranges = resolve_classification_ranges(answer)
        if resolved_ranges is None:
            continue

        root_ranges, space_ranges = resolved_ranges
        if root_ranges:
            frames = ranges_to_frames(root_ranges)
            if ROOT_SPACE_ID not in spaces:
                # The root layer is not a space of its own here, so its labels live in the data units.
                _add_to_data_units(label, data_type, frames, frame_classification)
            else:
                _add_to_space(label, spaces, ROOT_SPACE_ID, frames, frame_classification)

        for space_id, ranges in space_ranges.items():
            if ranges:
                _add_to_space(label, spaces, space_id, ranges_to_frames(ranges), frame_classification)

    return label


def _to_frame_classification(answer: ClassificationAnswer) -> Optional[FrameClassification]:
    attributes = answer.get("classifications") or []
    if not attributes:
        return None

    name = attributes[0].get("name") or ""
    value = attributes[0].get("value") or ""
    classification_hash = answer["classificationHash"]
    feature_hash = answer["featureHash"]
    created_at = answer.get("createdAt") or ""
    confidence = answer.get("confidence") or DEFAULT_CONFIDENCE
    manual_annotation = answer.get("manualAnnotation") or DEFAULT_MANUAL_ANNOTATION

    frame_classification: FrameClassification = {
        "classificationHash": classification_hash,
        "featureHash": feature_hash,
        "name": name,
        "value": value,
        "createdAt": created_at,
        "confidence": confidence,
        "manualAnnotation": manual_annotation,
    }

    if (created_by := answer.get("createdBy")) is not None:
        frame_classification["createdBy"] = created_by
    if (last_edited_at := answer.get("lastEditedAt")) is not None:
        frame_classification["lastEditedAt"] = last_edited_at
    if (last_edited_by := answer.get("lastEditedBy")) is not None:
        frame_classification["lastEditedBy"] = last_edited_by

    return frame_classification


def _add_to_data_units(
    label_row_dict: Dict[str, Any],
    data_type: Optional[str],
    frames: List[int],
    frame_classification: FrameClassification,
) -> None:
    if not frames:
        return

    data_units = label_row_dict.get("data_units") or {}

    for data_unit in data_units.values():
        if data_type in _FLAT_LABEL_DATA_TYPES:
            if int(data_unit.get("data_sequence", 0)) in frames:
                _append_classification(data_unit.setdefault("labels", {}), frame_classification)
        elif data_type in _FRAME_KEYED_DATA_TYPES:
            labels = data_unit.setdefault("labels", {})
            for frame in frames:
                _append_classification(_frame_blob(labels, str(frame)), frame_classification)


def _add_to_space(
    label_row_dict: Dict[str, Any],
    spaces: Dict[str, Any],
    space_id: str,
    frames: List[int],
    frame_classification: FrameClassification,
) -> None:
    space = spaces.get(space_id)
    if space is None or not frames:
        return

    if space.get("space_type") == SpaceType.SCENE_IMAGE.value:
        _add_to_scene_image_data_unit(label_row_dict, space_id, space, frame_classification)
        return

    labels = space.setdefault("labels", {})
    for frame in frames:
        _append_classification(_frame_blob(labels, str(frame)), frame_classification)


def _add_to_scene_image_data_unit(
    label_row_dict: Dict[str, Any],
    space_id: str,
    space: Dict[str, Any],
    frame_classification: FrameClassification,
) -> None:
    scene_info = space.get("scene_info") or {}
    stream_id = scene_info.get("stream_id")
    label_keys = []
    if stream_id is not None:
        for frame in (scene_info.get("start_frame"), scene_info.get("event_index")):
            if frame is not None:
                label_key = f"{stream_id}#{frame}"
                if label_key not in label_keys:
                    label_keys.append(label_key)
    label_keys.append(space_id)

    data_units = list((label_row_dict.get("data_units") or {}).values())
    targets = []
    for data_unit in data_units:
        labels = data_unit.get("labels") or {}
        matching_label_key = next((key for key in label_keys if key in labels), None)
        if matching_label_key is not None:
            targets.append((data_unit, matching_label_key))

    if not targets and len(data_units) == 1:
        targets = [(data_units[0], label_keys[0])]

    for data_unit, label_key in targets:
        labels = data_unit.setdefault("labels", {})
        _append_classification(_frame_blob(labels, label_key), frame_classification)


def _frame_blob(labels: Dict[str, Any], frame: str) -> Dict[str, Any]:
    blob = labels.get(frame)
    if blob is None:
        blob = {"objects": [], "classifications": []}
        labels[frame] = blob
    return blob


def _append_classification(label_blob: Dict[str, Any], frame_classification: FrameClassification) -> None:
    classifications = label_blob.setdefault("classifications", [])
    if any(
        existing.get("classificationHash") == frame_classification["classificationHash"] for existing in classifications
    ):
        return
    classifications.append(dict(frame_classification))
