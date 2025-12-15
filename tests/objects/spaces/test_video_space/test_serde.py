from unittest.mock import Mock

from deepdiff import DeepDiff

from encord.objects import LabelRowV2
from tests.objects.data.data_group.two_videos import (
    DATA_GROUP_METADATA,
    DATA_GROUP_WITH_TWO_VIDEOS_LABELS,
)


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
        exclude_regex_paths=[r".*\['trackHash'\]", r".*\['child_info'\]"],
        ignore_order_func=lambda x: x.path().endswith("['objects']"),
    )
