from dataclasses import asdict
from unittest.mock import Mock

import pytest

from encord.objects import LabelRowV2
from encord.orm.label_row import LabelRowMetadata
from tests.objects.common import FAKE_LABEL_ROW_METADATA
from tests.objects.data import empty_video
from tests.objects.data.all_ontology_types import all_ontology_types
from tests.objects.data.audio_labels import EMPTY_AUDIO_LABELS
from tests.objects.data.html_text_labels import EMPTY_HTML_TEXT_LABELS
from tests.objects.data.plain_text import EMPTY_PLAIN_TEXT_LABELS
from tests.objects.test_label_structure_converter import ontology_from_dict


@pytest.fixture
def empty_video_label_row() -> LabelRowV2:
    label_row_metadata_dict = asdict(FAKE_LABEL_ROW_METADATA)
    label_row_metadata = LabelRowMetadata(**label_row_metadata_dict)

    label_row = LabelRowV2(label_row_metadata, Mock(), ontology_from_dict(all_ontology_types))
    label_row.from_labels_dict(empty_video.labels)
    return label_row


@pytest.fixture
def empty_audio_label_row() -> LabelRowV2:
    label_row_metadata_dict = asdict(FAKE_LABEL_ROW_METADATA)
    label_row_metadata_dict["frames_per_second"] = 1000
    label_row_metadata_dict["data_type"] = "AUDIO"
    label_row_metadata = LabelRowMetadata(**label_row_metadata_dict)

    label_row = LabelRowV2(label_row_metadata, Mock(), ontology_from_dict(all_ontology_types))
    label_row.from_labels_dict(EMPTY_AUDIO_LABELS)

    return label_row


@pytest.fixture
def empty_html_text_label_row() -> LabelRowV2:
    label_row_metadata_dict = asdict(FAKE_LABEL_ROW_METADATA)
    label_row_metadata_dict["data_type"] = "plain_text"
    label_row_metadata_dict["file_type"] = "text/html"
    label_row_metadata = LabelRowMetadata(**label_row_metadata_dict)

    label_row = LabelRowV2(label_row_metadata, Mock(), ontology_from_dict(all_ontology_types))
    label_row.from_labels_dict(EMPTY_HTML_TEXT_LABELS)

    return label_row


@pytest.fixture
def empty_plain_text_label_row() -> LabelRowV2:
    label_row_metadata_dict = asdict(FAKE_LABEL_ROW_METADATA)
    label_row_metadata_dict["data_type"] = "plain_text"
    label_row_metadata_dict["file_type"] = "text/plain"
    label_row_metadata = LabelRowMetadata(**label_row_metadata_dict)

    label_row = LabelRowV2(label_row_metadata, Mock(), ontology_from_dict(all_ontology_types))
    label_row.from_labels_dict(EMPTY_PLAIN_TEXT_LABELS)

    return label_row
