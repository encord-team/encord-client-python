from unittest.mock import Mock

import pytest
from deepdiff import DeepDiff

from encord.objects import LabelRowV2
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.two_videos import (
    DATA_GROUP_METADATA,
    DATA_GROUP_WITH_TWO_VIDEOS_LABELS,
)


@pytest.fixture
def ontology():
    ontology_structure = Mock()
    ontology_structure.get_child_by_hash = all_types_structure.get_child_by_hash
    ontology = Mock(structure=ontology_structure)
    yield ontology


def test_parse_spaces_before_initialise_labels(ontology):
    # Arrange

    # Act
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)

    # Assert
    spaces = label_row.get_spaces()
    assert len(spaces) == 2

    # Check getting space by id
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")
    assert video_space_1.space_id == "video-1-uuid"
    assert video_space_1.layout_key == "left-camera"

    video_space_1 = label_row.get_space(layout_key="left-camera", type_="video")
    assert video_space_1.space_id == "video-1-uuid"
    assert video_space_1.layout_key == "left-camera"

    # Check getting space by layout key
    video_space_2 = label_row.get_space(id="video-2-uuid", type_="video")
    assert video_space_2.space_id == "video-2-uuid"
    assert video_space_2.layout_key == "right-camera"

    video_space_2 = label_row.get_space(layout_key="right-camera", type_="video")
    assert video_space_2.space_id == "video-2-uuid"
    assert video_space_2.layout_key == "right-camera"


def test_read_and_export_video_space_labels(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_WITH_TWO_VIDEOS_LABELS)

    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")
    video_space_1_object_annotations = video_space_1.get_object_instance_annotations()
    assert len(video_space_1_object_annotations) == 5

    video_space_1_object_entities = video_space_1.get_object_instances()
    assert len(video_space_1_object_entities) == 3

    video_space_1_classification_annotations = video_space_1.get_classification_instance_annotations()
    assert len(video_space_1_classification_annotations) == 1
    classification_entities = video_space_1.get_classification_instances()
    assert len(classification_entities) == 1

    output_dict = label_row.to_encord_dict()

    assert not DeepDiff(
        DATA_GROUP_WITH_TWO_VIDEOS_LABELS,
        output_dict,
        exclude_regex_paths=[r".*\['trackHash'\]"],
        ignore_order_func=lambda x: x.path().endswith("['objects']"),
    )
