from unittest.mock import Mock

from deepdiff import DeepDiff

from encord.objects import LabelRowV2
from tests.objects.data.data_group.two_audio import (
    DATA_GROUP_METADATA,
    DATA_GROUP_WITH_TWO_AUDIO_LABELS,
)


def test_read_and_export_audio_space_labels(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_WITH_TWO_AUDIO_LABELS)

    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")
    audio_space_1_object_annotations = audio_space_1.get_object_instance_annotations()
    assert len(audio_space_1_object_annotations) == 1

    audio_space_1_object_instances = audio_space_1.get_object_instances()
    assert len(audio_space_1_object_instances) == 1

    audio_space_1_classification_annotations = audio_space_1.get_classification_instance_annotations()
    assert len(audio_space_1_classification_annotations) == 1
    classification_entities = audio_space_1.get_classification_instances()
    assert len(classification_entities) == 1

    output_dict = label_row.to_encord_dict()
    assert not DeepDiff(
        DATA_GROUP_WITH_TWO_AUDIO_LABELS,
        output_dict,
        exclude_regex_paths=[r".*\['trackHash'\]", r".*\['child_info'\]"],
        ignore_order_func=lambda x: x.path().endswith("['objects']"),
    )
