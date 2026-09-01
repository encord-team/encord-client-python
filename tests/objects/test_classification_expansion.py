"""Reconstruction of per-frame classifications from `classification_answers`.

Used to keep the shape of the dicts returned by the deprecated `Project.get_label_row(s)` functions intact,
now that the backend serves classifications through `classification_answers` only.
"""

from copy import deepcopy
from typing import Optional
from unittest.mock import Mock

import pytest

from encord.objects import LabelRowV2
from encord.objects.classification_expansion import expand_classification_answers_into_frame_labels
from encord.objects.classification_ranges import resolve_classification_ranges
from encord.objects.constants import ROOT_SPACE_ID
from encord.objects.frames import ranges_to_frames
from tests.objects.data import video_with_classifications
from tests.objects.data.data_group.all_modalities import DATA_GROUP_METADATA, DATA_GROUP_WITH_LABELS

VIDEO_DATA_HASH = "cd57cf5c-2541-4a46-a836-444540ee987a"
RADIO_CLASSIFICATION_HASH = "3AqiIPrF"


def _without_frame_classifications(label_row_dict: dict) -> dict:
    compact = deepcopy(label_row_dict)
    for data_unit in compact.get("data_units", {}).values():
        labels = data_unit.get("labels", {})
        if "classifications" in labels:
            labels["classifications"] = []
        else:
            for frame_labels in labels.values():
                frame_labels["classifications"] = []
    for space in compact.get("spaces", {}).values():
        for frame_labels in space.get("labels", {}).values():
            if isinstance(frame_labels, dict) and "classifications" in frame_labels:
                frame_labels["classifications"] = []
    return compact


def test_expands_a_video_classification_onto_every_frame_of_its_range() -> None:
    """The expansion reproduces the per-frame classifications the backend used to serve."""
    compact = _without_frame_classifications(video_with_classifications.labels)

    expand_classification_answers_into_frame_labels(compact)

    assert compact == video_with_classifications.labels

    frames = compact["data_units"][VIDEO_DATA_HASH]["labels"]
    for frame in ("0", "1"):
        classifications = frames[frame]["classifications"]
        assert len(classifications) == 1
        assert classifications[0]["classificationHash"] == RADIO_CLASSIFICATION_HASH


def test_expansion_is_idempotent() -> None:
    """Responses that still carry per-frame classifications must be left alone."""
    already_expanded = deepcopy(video_with_classifications.labels)

    expand_classification_answers_into_frame_labels(already_expanded)

    assert already_expanded == video_with_classifications.labels


def test_creates_frames_that_only_the_answer_knows_about() -> None:
    compact = _without_frame_classifications(video_with_classifications.labels)
    del compact["data_units"][VIDEO_DATA_HASH]["labels"]["1"]
    compact["classification_answers"][RADIO_CLASSIFICATION_HASH]["range"] = [[1, 2]]

    expand_classification_answers_into_frame_labels(compact)

    frames = compact["data_units"][VIDEO_DATA_HASH]["labels"]
    assert frames["1"] == {
        "objects": [],
        "classifications": [frames["1"]["classifications"][0]],
    }
    assert frames["2"]["classifications"][0]["classificationHash"] == RADIO_CLASSIFICATION_HASH
    assert frames["0"]["classifications"] == [], "Frame 0 is outside the answer's range"


def test_expands_onto_the_frames_of_an_image_group() -> None:
    compact = {
        "data_type": "img_group",
        "classification_answers": {
            "clf": {
                "classificationHash": "clf",
                "featureHash": "feature",
                "classifications": [{"name": "A classification", "value": "a_classification"}],
                "createdBy": "user@encord.com",
                "createdAt": "Tue, 05 Nov 2024 09:41:37 UTC",
                "range": [[1, 1]],
                "spaces": {},
            }
        },
        "data_units": {
            "first": {"data_sequence": "0", "labels": {"objects": [], "classifications": []}},
            "second": {"data_sequence": "1", "labels": {"objects": [], "classifications": []}},
        },
    }

    expand_classification_answers_into_frame_labels(compact)

    assert compact["data_units"]["first"]["labels"]["classifications"] == []
    assert compact["data_units"]["second"]["labels"]["classifications"][0]["classificationHash"] == "clf"


def test_expands_space_placements_onto_space_frames() -> None:
    compact = _without_frame_classifications(DATA_GROUP_WITH_LABELS)

    expand_classification_answers_into_frame_labels(compact)

    video_frames = compact["spaces"]["video-uuid"]["labels"]
    assert video_frames["0"]["classifications"][0]["classificationHash"] == "video-classification"

    # Global classifications carry no placement, so there is nothing to expand for them.
    all_hashes = {
        classification["classificationHash"]
        for space in compact["spaces"].values()
        for frame_labels in space.get("labels", {}).values()
        if isinstance(frame_labels, dict)
        for classification in frame_labels.get("classifications", [])
    }
    assert not any(hash_.startswith("global-classification") for hash_ in all_hashes)


@pytest.mark.parametrize(
    ("scene_info", "existing_label_key", "expected_label_key"),
    [
        pytest.param(
            {"stream_id": "camera1", "start_frame": 10, "event_index": 7},
            "camera1#10",
            "camera1#10",
            id="stream-start-frame",
        ),
        pytest.param(
            {"stream_id": "camera1", "event_index": 7},
            None,
            "camera1#7",
            id="event-index-fallback",
        ),
        pytest.param(
            {"stream_id": "camera1", "start_frame": None, "event_index": 7},
            "camera1#7",
            "camera1#7",
            id="null-start-frame",
        ),
        pytest.param(
            {"stream_id": "camera1", "start_frame": 10, "event_index": 7},
            "path/to/image.jpg",
            "path/to/image.jpg",
            id="legacy-uri-key",
        ),
    ],
)
def test_expands_scene_image_classification_into_data_unit_label(
    scene_info: dict, existing_label_key: Optional[str], expected_label_key: str
) -> None:
    space_id = "path/to/image.jpg"
    data_unit_labels = (
        {existing_label_key: {"objects": [], "classifications": []}} if existing_label_key is not None else {}
    )
    compact = {
        "data_type": "scene",
        "classification_answers": {
            "classification-hash": {
                "classificationHash": "classification-hash",
                "featureHash": "feature-hash",
                "classifications": [{"name": "Question", "value": "answer"}],
                "range": [],
                "spaces": {space_id: {"range": [[0, 0]], "type": "frame"}},
            }
        },
        "data_units": {"scene-data": {"labels": data_unit_labels}},
        "spaces": {
            space_id: {
                "space_type": "scene_image",
                "scene_info": scene_info,
                "labels": {"objects": [], "classifications": []},
            }
        },
    }

    expand_classification_answers_into_frame_labels(compact)

    classifications = compact["data_units"]["scene-data"]["labels"][expected_label_key]["classifications"]
    assert [classification["classificationHash"] for classification in classifications] == ["classification-hash"]
    assert compact["spaces"][space_id]["labels"] == {"objects": [], "classifications": []}


def test_root_space_entry_does_not_override_the_top_level_range() -> None:
    compact = _without_frame_classifications(video_with_classifications.labels)
    answer = compact["classification_answers"][RADIO_CLASSIFICATION_HASH]
    answer["range"] = [[1, 1]]
    answer["spaces"] = {ROOT_SPACE_ID: {"type": "frame", "range": [[0, 0]]}}

    expand_classification_answers_into_frame_labels(compact)

    frames = compact["data_units"][VIDEO_DATA_HASH]["labels"]
    assert frames["0"]["classifications"] == []
    assert frames["1"]["classifications"][0]["classificationHash"] == RADIO_CLASSIFICATION_HASH


@pytest.mark.parametrize(
    "answer_overrides",
    [
        pytest.param({"classifications": []}, id="no_attribute_answers"),
        pytest.param({"range": [], "spaces": {}}, id="no_placement"),
    ],
)
def test_answers_that_cannot_be_expanded_are_skipped(answer_overrides) -> None:
    compact = _without_frame_classifications(video_with_classifications.labels)
    compact["classification_answers"][RADIO_CLASSIFICATION_HASH].update(answer_overrides)

    expand_classification_answers_into_frame_labels(compact)

    for frame_labels in compact["data_units"][VIDEO_DATA_HASH]["labels"].values():
        assert frame_labels["classifications"] == []


def test_parsing_and_expansion_agree_on_where_classifications_sit(ontology) -> None:
    """Both consumers of `classification_answers` must honour the same resolved placements.

    Reading a label row and reconstructing its per-frame classifications are the two readers of the format,
    and a classification has to end up on the same frames either way.
    """
    compact = _without_frame_classifications(DATA_GROUP_WITH_LABELS)

    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(compact)
    expanded = expand_classification_answers_into_frame_labels(deepcopy(compact))

    compared = 0
    for answer in compact["classification_answers"].values():
        classification_hash = answer["classificationHash"]

        resolved_ranges = resolve_classification_ranges(answer)
        assert resolved_ranges is not None
        _, space_ranges = resolved_ranges

        for space_id, ranges in space_ranges.items():
            if not ranges:
                continue

            expected_frames = set(ranges_to_frames(ranges))

            expanded_frames = {
                int(frame)
                for frame, frame_labels in expanded["spaces"][space_id]["labels"].items()
                if any(
                    classification["classificationHash"] == classification_hash
                    for classification in frame_labels["classifications"]
                )
            }
            assert expanded_frames == expected_frames, f"{classification_hash} expanded onto the wrong frames"

            parsed_frames = {
                annotation.frame
                for annotation in label_row._space_map[space_id].get_annotations(type_="classification")
                if annotation.classification_hash == classification_hash
            }
            assert parsed_frames == expected_frames, f"{classification_hash} was parsed onto the wrong frames"

            compared += 1

    assert compared, "The fixture carries no frame placed classifications to compare"


def test_no_classification_answers_is_a_no_op() -> None:
    compact = _without_frame_classifications(video_with_classifications.labels)
    compact["classification_answers"] = {}
    expected = deepcopy(compact)

    assert expand_classification_answers_into_frame_labels(compact) == expected
