"""`classification_answers` is the only source of classifications data.

Per-frame classifications under `data_units[*].labels` and `spaces[*].labels` are never read, so these tests
build label row dicts that carry no per-frame classifications at all and assert the classifications are still
parsed, placed and serialised correctly.
"""

from copy import deepcopy
from dataclasses import asdict
from unittest.mock import Mock

from encord.objects import Classification, LabelRowV2
from encord.objects.constants import ROOT_SPACE_ID
from encord.objects.frames import Range
from encord.orm.label_row import LabelRowMetadata
from tests.objects.common import BASE_LABEL_ROW_METADATA
from tests.objects.data import empty_video, video_with_classifications
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.all_modalities import DATA_GROUP_METADATA, DATA_GROUP_WITH_LABELS
from tests.objects.data.data_group.two_videos import (
    DATA_GROUP_WITH_TWO_VIDEOS_LABELS,
    DATA_GROUP_WITH_TWO_VIDEOS_METADATA,
)

RADIO_CLASSIFICATION_HASH = "3AqiIPrF"
TEXT_CLASSIFICATION = all_types_structure.get_child_by_hash("jPOcEsbw", Classification)
TEXT_ATTRIBUTE = TEXT_CLASSIFICATION.attributes[0]


def _video_label_row(all_types_ontology) -> LabelRowV2:
    label_row_metadata_dict = asdict(BASE_LABEL_ROW_METADATA)
    label_row_metadata_dict["duration"] = 0.08
    label_row_metadata_dict["frames_per_second"] = 25.0
    return LabelRowV2(LabelRowMetadata(**label_row_metadata_dict), Mock(), all_types_ontology)


def _without_frame_classifications(label_row_dict: dict) -> dict:
    """The shape the backend serves: every frame keyed entry carries `classifications: []`."""
    compact = deepcopy(label_row_dict)

    for data_unit in compact.get("data_units", {}).values():
        labels = data_unit.get("labels", {})
        if "classifications" in labels:
            labels["classifications"] = []
        else:
            for frame_labels in labels.values():
                frame_labels["classifications"] = []

    for space in compact.get("spaces", {}).values():
        labels = space.get("labels", {})
        if "classifications" in labels:
            labels["classifications"] = []
        else:
            for frame_labels in labels.values():
                if isinstance(frame_labels, dict) and "classifications" in frame_labels:
                    frame_labels["classifications"] = []

    return compact


def test_video_classifications_are_parsed_without_frame_classifications(all_types_ontology) -> None:
    expanded = _video_label_row(all_types_ontology)
    expanded.from_labels_dict(video_with_classifications.labels)

    compact = _video_label_row(all_types_ontology)
    compact.from_labels_dict(_without_frame_classifications(video_with_classifications.labels))

    compact_classifications = compact.get_classification_instances()
    assert len(compact_classifications) == 1

    classification = compact_classifications[0]
    assert classification.classification_hash == RADIO_CLASSIFICATION_HASH
    assert classification.range_list == [Range(0, 1)]
    assert classification.created_by == "user1Hash"
    assert classification.get_answer().value == "cl_1_option_2"

    # Dropping the per-frame classifications changes nothing, in either direction.
    assert compact.to_encord_dict() == expanded.to_encord_dict()
    assert compact.to_encord_dict() == video_with_classifications.labels


def test_frame_classifications_are_ignored_when_they_contradict_the_answer(all_types_ontology) -> None:
    """The answer wins: per-frame classifications are not read at all, not even to enrich the placement."""
    contradicting = deepcopy(video_with_classifications.labels)
    contradicting["classification_answers"][RADIO_CLASSIFICATION_HASH]["range"] = [[0, 0]]
    frame_labels = contradicting["data_units"]["cd57cf5c-2541-4a46-a836-444540ee987a"]["labels"]
    frame_labels["1"]["classifications"][0]["createdBy"] = "someone-else@encord.com"

    label_row = _video_label_row(all_types_ontology)
    label_row.from_labels_dict(contradicting)

    classification = label_row.get_classification_instances()[0]
    assert classification.range_list == [Range(0, 0)], "Only the answer's range places the classification"
    assert not classification.is_on_frame(1)
    assert classification.created_by == "user1Hash", "Only the answer carries the annotation metadata"


def test_classification_only_on_the_root_space_entry_is_ignored(all_types_ontology) -> None:
    label_row_dict = _without_frame_classifications(video_with_classifications.labels)
    answer = label_row_dict["classification_answers"][RADIO_CLASSIFICATION_HASH]
    del answer["range"]
    answer["spaces"] = {ROOT_SPACE_ID: {"type": "frame", "range": [[1, 1]]}}

    label_row = _video_label_row(all_types_ontology)
    label_row.from_labels_dict(label_row_dict)

    assert label_row.get_classification_instances() == []


def test_root_space_entry_does_not_override_the_top_level_range(all_types_ontology) -> None:
    label_row_dict = _without_frame_classifications(video_with_classifications.labels)
    answer = label_row_dict["classification_answers"][RADIO_CLASSIFICATION_HASH]
    answer["range"] = [[0, 0]]
    answer["spaces"] = {ROOT_SPACE_ID: {"type": "frame", "range": [[1, 1]]}}

    label_row = _video_label_row(all_types_ontology)
    label_row.from_labels_dict(label_row_dict)

    classification = label_row.get_classification_instances()[0]
    assert classification.range_list == [Range(0, 0)]


def test_space_classifications_are_parsed_without_frame_classifications(ontology) -> None:
    expanded = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    expanded.from_labels_dict(DATA_GROUP_WITH_LABELS)

    compact = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    compact.from_labels_dict(_without_frame_classifications(DATA_GROUP_WITH_LABELS))

    for space_id in ("video-uuid", "image-uuid", "image-sequence-uuid", "dicom-uuid", "pdf-uuid"):
        expected = set(expanded._space_map[space_id]._classifications_map)
        actual = set(compact._space_map[space_id]._classifications_map)
        assert actual == expected, f"Classifications on space {space_id} were not parsed from the answers"
        assert expected, f"Space {space_id} has no classifications to compare"

    video_space = compact.get_space(id="video-uuid", type_="video")
    frame_placed = video_space._classifications_map["video-classification"]
    annotations = [
        annotation
        for annotation in video_space.get_annotations(type_="classification")
        if annotation.classification_hash == "video-classification"
    ]
    assert [annotation.frame for annotation in annotations] == [0]
    assert annotations[0].created_by == "user@example.com"
    assert frame_placed.get_answer() == "Video answer"

    assert compact.to_encord_dict() == expanded.to_encord_dict()


def test_data_group_root_classification_is_parsed_from_the_top_level_range(ontology) -> None:
    """A root placement on a data group reaches the SDK as the answer's top-level range."""
    label_row_dict = _without_frame_classifications(DATA_GROUP_WITH_TWO_VIDEOS_LABELS)
    answer = label_row_dict["classification_answers"]["classification1"]
    answer["spaces"] = {}
    answer["range"] = [[0, 0]]

    label_row = LabelRowV2(DATA_GROUP_WITH_TWO_VIDEOS_METADATA, Mock(), ontology)
    label_row.from_labels_dict(label_row_dict)

    classifications = label_row.get_classification_instances()
    assert [c.classification_hash for c in classifications] == ["classification1"]
    assert classifications[0].range_list == [Range(0, 0)]

    for space in label_row.get_spaces():
        assert space.get_classification_instances() == []

    serialised = label_row.to_encord_dict()["classification_answers"]["classification1"]
    assert serialised["range"] == [[0, 0]]
    assert serialised["spaces"] == {}


def test_classification_on_two_spaces_is_a_single_instance(ontology) -> None:
    """Every placement of a classification belongs to one instance, however many spaces hold it."""
    label_row_dict = _without_frame_classifications(DATA_GROUP_WITH_TWO_VIDEOS_LABELS)
    answer = label_row_dict["classification_answers"]["classification1"]
    answer["spaces"]["video-2-uuid"] = {"type": "frame", "range": [[2, 3]]}

    label_row = LabelRowV2(DATA_GROUP_WITH_TWO_VIDEOS_METADATA, Mock(), ontology)
    label_row.from_labels_dict(label_row_dict)

    video_1 = label_row.get_space(id="video-1-uuid", type_="video")
    video_2 = label_row.get_space(id="video-2-uuid", type_="video")

    classification_1 = video_1._classifications_map["classification1"]
    classification_2 = video_2._classifications_map["classification1"]
    assert classification_1 is classification_2
    assert set(classification_1._spaces) == {"video-1-uuid", "video-2-uuid"}

    # Both placements survive serialisation: neither space overwrites the other.
    serialised = label_row.to_encord_dict()["classification_answers"]["classification1"]
    assert serialised["spaces"]["video-1-uuid"]["range"] == [[0, 0]]
    assert serialised["spaces"]["video-2-uuid"]["range"] == [[2, 3]]


def test_classification_on_the_root_layer_and_a_space_keeps_the_space_placement(ontology) -> None:
    """A classification can sit on the root layer as well as on a space, and the space placement wins.

    The SDK models a classification as living either on the root layer or on spaces, never both, which is the
    placement it has always parsed for these rows.
    """
    label_row_dict = _without_frame_classifications(DATA_GROUP_WITH_TWO_VIDEOS_LABELS)
    label_row_dict["classification_answers"]["classification1"]["range"] = [[0, 0]]

    label_row = LabelRowV2(DATA_GROUP_WITH_TWO_VIDEOS_METADATA, Mock(), ontology)
    label_row.from_labels_dict(label_row_dict)

    assert label_row.get_classification_instances() == []

    video_1 = label_row.get_space(id="video-1-uuid", type_="video")
    assert "classification1" in video_1._classifications_map


def test_confidence_round_trips_through_the_answer(all_types_ontology) -> None:
    """The answer carries the whole annotation metadata, `confidence` included.

    Per-frame classifications are never read, so a `confidence` that only reaches the frame labels is lost.
    """
    label_row = _video_label_row(all_types_ontology)
    label_row.from_labels_dict(empty_video.labels)

    classification = TEXT_CLASSIFICATION.create_instance()
    classification.set_answer("Text answer", attribute=TEXT_ATTRIBUTE)
    classification.set_for_frames(Range(0, 1), confidence=0.42)
    label_row.add_classification_instance(classification)

    serialised = label_row.to_encord_dict()
    assert serialised["classification_answers"][classification.classification_hash]["confidence"] == 0.42

    label_row.from_labels_dict(serialised)
    assert label_row.get_classification_instances()[0].confidence == 0.42


def test_confidence_round_trips_through_the_answer_for_range_only_classifications(empty_audio_label_row) -> None:
    """Range based classifications have no frame labels at all, so the answer is the only carrier."""
    classification = TEXT_CLASSIFICATION.create_instance(range_only=True)
    classification.set_answer("Text answer", attribute=TEXT_ATTRIBUTE)
    classification.set_for_frames(Range(0, 1000), confidence=0.42)
    empty_audio_label_row.add_classification_instance(classification)

    serialised = empty_audio_label_row.to_encord_dict()
    assert serialised["classification_answers"][classification.classification_hash]["confidence"] == 0.42
    for data_unit in serialised["data_units"].values():
        assert data_unit["labels"] == {}, "Nothing but the answer can carry the confidence here"

    empty_audio_label_row.from_labels_dict(serialised)
    assert empty_audio_label_row.get_classification_instances()[0].confidence == 0.42


def test_reparsing_a_label_row_does_not_duplicate_space_classifications(ontology) -> None:
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_WITH_LABELS)
    first_pass = label_row.to_encord_dict()

    label_row.from_labels_dict(DATA_GROUP_WITH_LABELS)

    assert label_row.to_encord_dict() == first_pass
