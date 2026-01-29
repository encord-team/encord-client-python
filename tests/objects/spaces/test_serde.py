from unittest.mock import Mock

from deepdiff import DeepDiff

from encord.objects import LabelRowV2
from tests.objects.data.data_group.all_modalities import (
    DATA_GROUP_WITH_LABELS,
)
from tests.objects.data.data_group.multilayer_image import (
    DATA_GROUP_MULTILAYER_IMAGE_LABELS,
    DATA_GROUP_MULTILAYER_IMAGE_METADATA,
)


def test_read_and_export_all_space_labels(ontology):
    label_row = LabelRowV2(DATA_GROUP_MULTILAYER_IMAGE_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_MULTILAYER_IMAGE_LABELS)

    assert len(label_row.get_classification_instances()) == 1

    multilayer_image_space = label_row.get_space(id="root", type_="multilayer")
    assert len(multilayer_image_space.get_object_instances()) == 1
    assert multilayer_image_space.get_object_instances()[0].object_hash == "video-box-object"
    assert len(list(multilayer_image_space.get_annotations(type_="object"))) == 1
    classification_instances = multilayer_image_space.get_classification_instances()
    assert len(classification_instances) == 2
    assert classification_instances[0].classification_hash == "video-classification"
    assert classification_instances[1].classification_hash == "global-classification-on-video"
    assert len(list(multilayer_image_space.get_annotations(type_="classification"))) == 2

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


def test_read_and_export_multilayer_image_labels(ontology):
    label_row = LabelRowV2(DATA_GROUP_MULTILAYER_IMAGE_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_MULTILAYER_IMAGE_LABELS)

    video_space = label_row.get_space(id="root", type_="multilayer_image")
    assert len(video_space.get_object_instances()) == 2
    assert video_space.get_object_instances()[0].object_hash == "object1"
    assert len(list(video_space.get_annotations(type_="object"))) == 2
    classification_instances = video_space.get_classification_instances()
    assert len(classification_instances) == 1
    assert classification_instances[0].classification_hash == "classification1"
    assert len(list(video_space.get_annotations(type_="classification"))) == 1

    # Verify round-trip serialization
    output_dict = label_row.to_encord_dict()
    assert not DeepDiff(
        DATA_GROUP_MULTILAYER_IMAGE_LABELS,
        output_dict,
        exclude_regex_paths=[
            r".*\['trackHash'\]",
            r".*\['child_info'\]",
        ],
        ignore_order_func=lambda x: x.path().endswith("['objects']"),
    )
