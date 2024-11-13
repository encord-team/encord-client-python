from datetime import datetime
from unittest.mock import Mock, PropertyMock

import pytest
from deepdiff import DeepDiff

from encord.objects import LabelRowV2, Object, ObjectInstance, Shape
from encord.objects.frames import Range
from encord.objects.metadata import DICOMSeriesMetadata, DICOMSliceMetadata
from encord.ontology import Ontology
from encord.orm.label_row import AnnotationTaskStatus, LabelRowMetadata, LabelStatus
from tests.objects.data.audio_labels import AUDIO_LABELS, EMPTY_AUDIO_LABELS
from tests.objects.data.dicom_labels_with_metadata import (
    DICOM_LABELS_WITH_METADATA_TEST_BLURB,
)


@pytest.fixture
def ontology() -> Ontology:
    get_child_by_hash = PropertyMock(
        return_value=Object(
            uid=1, name="Box", color="#D33115", shape=Shape.BOUNDING_BOX, feature_node_hash="MjI2NzEy", attributes=[]
        )
    )
    ontology_structure = Mock(get_child_by_hash=get_child_by_hash)
    yield Mock(structure=ontology_structure)


@pytest.fixture
def label_row_metadata() -> LabelRowMetadata:
    return LabelRowMetadata(
        label_hash="",
        branch_name="main",
        created_at=datetime.now(),
        last_edited_at=datetime.now(),
        data_hash="",
        data_title="",
        data_type="DICOM",
        data_link="",
        dataset_hash="",
        dataset_title="",
        label_status=LabelStatus.NOT_LABELLED,
        annotation_task_status=AnnotationTaskStatus.QUEUED,
        workflow_graph_node=None,
        is_shadow_data=False,
        duration=100,
        frames_per_second=25,
        number_of_frames=55,
        height=512,
        width=512,
        audio_codec=None,
        audio_sample_rate=None,
        audio_num_channels=None,
        audio_bit_depth=None
    )


def test_label_row_metadata_accessor(ontology, label_row_metadata):
    label_row = LabelRowV2(label_row_metadata, Mock(), ontology)
    label_row.from_labels_dict(DICOM_LABELS_WITH_METADATA_TEST_BLURB)

    row_metadata = label_row.metadata
    assert row_metadata is not None
    assert isinstance(row_metadata, DICOMSeriesMetadata)

    for frame_view in label_row.get_frame_views():
        frame_metadata = frame_view.metadata
        assert frame_metadata is not None
        assert isinstance(frame_metadata, DICOMSliceMetadata)


def test_label_row_audio_metadata_accessor(ontology, label_row_metadata):
    label_row = LabelRowV2(label_row_metadata, Mock(), ontology)
    label_row.from_labels_dict(EMPTY_AUDIO_LABELS)

    assert label_row.audio_codec == "mp3"
    assert label_row.audio_num_channels == 2
    assert label_row.audio_sample_rate == 44100
    assert label_row.audio_bit_depth == 8


def test_checklist_parsing_merging_single_frame_events(ontology, label_row_metadata):
    answer_ranges = [
        (Range(start=536, end=536), ["abcDeFGH"]),
        (Range(start=1695, end=1695), ["abcDeFGH"]),
        (Range(start=541, end=541), ["xGvnZsqe"]),
        (Range(start=1730, end=1730), ["xGvnZsqe"]),
        (Range(start=1695, end=1695), ["lMT3lsvM"]),
    ]

    merged_result = ObjectInstance._merge_answers_to_non_overlapping_ranges(answer_ranges)
    expected_results = [
        (Range(start=536, end=536), {"abcDeFGH"}),
        (Range(start=541, end=541), {"xGvnZsqe"}),
        (Range(start=1695, end=1695), {"abcDeFGH", "lMT3lsvM"}),
        (Range(start=1730, end=1730), {"xGvnZsqe"}),
    ]

    assert not DeepDiff(merged_result, expected_results)


def test_checklist_parsing_merging_included_events(ontology, label_row_metadata):
    answer_ranges = [
        (Range(start=0, end=100), ["abcDeFGH"]),
        (Range(start=10, end=90), ["xGvnZsqe"]),
        (Range(start=20, end=80), ["nMakrEgd"]),
    ]

    merged_result = ObjectInstance._merge_answers_to_non_overlapping_ranges(answer_ranges)
    expected_results = [
        (Range(start=0, end=9), {"abcDeFGH"}),
        (Range(start=10, end=19), {"abcDeFGH", "xGvnZsqe"}),
        (Range(start=20, end=80), {"abcDeFGH", "xGvnZsqe", "nMakrEgd"}),
        (Range(start=81, end=90), {"abcDeFGH", "xGvnZsqe"}),
        (Range(start=91, end=100), {"abcDeFGH"}),
    ]

    assert not DeepDiff(merged_result, expected_results)


def test_checklist_parsing_merging_overlapped_events(ontology, label_row_metadata):
    answer_ranges = [
        (Range(start=0, end=60), ["abcDeFGH"]),
        (Range(start=40, end=80), ["xGvnZsqe"]),
        (Range(start=20, end=100), ["nMakrEgd"]),
    ]

    merged_result = ObjectInstance._merge_answers_to_non_overlapping_ranges(answer_ranges)
    expected_results = [
        (Range(start=0, end=19), {"abcDeFGH"}),
        (Range(start=20, end=39), {"abcDeFGH", "nMakrEgd"}),
        (Range(start=40, end=60), {"abcDeFGH", "nMakrEgd", "xGvnZsqe"}),
        (Range(start=61, end=80), {"xGvnZsqe", "nMakrEgd"}),
        (Range(start=81, end=100), {"nMakrEgd"}),
    ]

    assert not DeepDiff(merged_result, expected_results)
