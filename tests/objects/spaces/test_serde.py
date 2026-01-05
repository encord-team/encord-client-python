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

    # Global Classification exists on LabelRowV2
    assert len(label_row.get_classification_instances()) == 1

    # Video space: 1 object, 1 normal classification, 1 global classification
    video_space = label_row._get_space(id="video-uuid", type_="video")
    assert len(video_space.get_object_instances()) == 1
    assert video_space.get_object_instances()[0].object_hash == "video-box-object"
    assert len(list(video_space.get_object_instance_annotations())) == 1
    assert len(video_space.get_classification_instances()) == 2
    assert video_space.get_classification_instances()[0].classification_hash == "video-classification"
    assert len(list(video_space.get_classification_instance_annotations())) == 2

    # Image space: 1 object, 1 normal classification, 1 global classification
    image_space = label_row._get_space(id="image-uuid", type_="image")
    assert len(image_space.get_object_instances()) == 1
    assert image_space.get_object_instances()[0].object_hash == "image-box-object"
    assert len(list(image_space.get_object_instance_annotations())) == 1
    assert len(image_space.get_classification_instances()) == 2
    assert image_space.get_classification_instances()[0].classification_hash == "image-classification"
    assert len(list(image_space.get_classification_instance_annotations())) == 2

    # Audio space: 1 object, 1 normal classification, 1 global classification
    audio_space = label_row._get_space(id="audio-uuid", type_="audio")
    assert len(audio_space.get_object_instances()) == 1
    assert audio_space.get_object_instances()[0].object_hash == "audio-object"
    assert len(list(audio_space.get_object_instance_annotations())) == 1
    assert len(audio_space.get_classification_instances()) == 1
    assert audio_space.get_classification_instances()[0].classification_hash == "audio-classification"
    assert len(list(audio_space.get_classification_instance_annotations())) == 1

    # Text space: 1 object, 1 normal classification, 1 global classification
    text_space = label_row._get_space(id="text-uuid", type_="text")
    assert len(text_space.get_object_instances()) == 1
    assert text_space.get_object_instances()[0].object_hash == "text-object"
    assert len(list(text_space.get_object_instance_annotations())) == 1
    assert len(text_space.get_classification_instances()) == 1
    assert text_space.get_classification_instances()[0].classification_hash == "text-classification"
    assert len(list(text_space.get_classification_instance_annotations())) == 1

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
