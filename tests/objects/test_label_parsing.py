from datetime import datetime
from unittest.mock import Mock, PropertyMock

import pytest

from encord.objects import LabelRowV2, Object, Shape
from encord.objects.metadata import DICOMAnnotationMetadata, DICOMSeriesMetadata
from encord.ontology import Ontology
from encord.orm.label_row import AnnotationTaskStatus, LabelRowMetadata, LabelStatus
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
        assert isinstance(frame_metadata, DICOMAnnotationMetadata)
