from unittest.mock import Mock

from deepdiff import DeepDiff

from encord.objects import LabelRowV2
from tests.objects.data.data_group.all_modalities import (
    DATA_GROUP_METADATA,
    DATA_GROUP_WITH_LABELS,
)


def test_read_and_export_all_space_labels(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_WITH_LABELS)

    # Video space: 1 object annotation on frame 0, 1 classification annotation
    video_space = label_row.get_space(id="video-uuid", type_="video")
    assert len(video_space.get_object_instance_annotations()) == 1
    assert len(video_space.get_object_instances()) == 1
    assert len(video_space.get_classification_instance_annotations()) == 1
    assert len(video_space.get_classification_instances()) == 1

    # Image space: 1 object annotation on frame 0, 1 classification annotation
    image_space = label_row.get_space(id="image-uuid", type_="image")
    assert len(image_space.get_object_instance_annotations()) == 1
    assert len(image_space.get_object_instances()) == 1
    assert len(image_space.get_classification_instance_annotations()) == 1
    assert len(image_space.get_classification_instances()) == 1

    # Audio space: 1 object with range, 1 classification
    audio_space = label_row.get_space(id="audio-uuid", type_="audio")
    assert len(audio_space.get_object_instance_annotations()) == 1
    assert len(audio_space.get_object_instances()) == 1
    assert len(audio_space.get_classification_instance_annotations()) == 1
    assert len(audio_space.get_classification_instances()) == 1

    # Text space: 1 object with range, 1 classification
    text_space = label_row.get_space(id="text-uuid", type_="text")
    assert len(text_space.get_object_instance_annotations()) == 1
    assert len(text_space.get_object_instances()) == 1
    assert len(text_space.get_classification_instance_annotations()) == 1
    assert len(text_space.get_classification_instances()) == 1

    # Verify round-trip serialization
    output_dict = label_row.to_encord_dict()
    assert not DeepDiff(
        DATA_GROUP_WITH_LABELS,
        output_dict,
        exclude_regex_paths=[
            r".*\['trackHash'\]",
            r".*\['child_info'\]",
        ],
        ignore_order_func=lambda x: x.path().endswith("['objects']"),
    )
