from unittest.mock import Mock

from encord.objects import Classification, LabelRowV2
from tests.objects.data.all_types_ontology_structure import GLOBAL_CLASSIFICATION, all_types_structure
from tests.objects.data.data_group.all_modalities import (
    DATA_GROUP_METADATA,
    DATA_GROUP_NO_LABELS,
)

global_classification = all_types_structure.get_child_by_hash(GLOBAL_CLASSIFICATION.feature_node_hash, Classification)


def test_global_classifications_on_data_group(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_NO_LABELS)

    classifications_on_label_row = label_row.get_classification_instances()
    assert len(classifications_on_label_row) == 0

    # Act
    global_classification_on_label_row = global_classification.create_instance()
    label_row.add_classification_instance(global_classification_on_label_row)
    assert len(label_row.get_classification_instances()) == 1

    # Add global classification to each space
    total_spaces = len(label_row._get_spaces())
    for space in label_row._space_map.values():
        global_classification_on_space = global_classification.create_instance()
        space.put_classification_instance(classification_instance=global_classification_on_space)
        assert list(space._global_classification_hash_to_annotation_data.keys()) == [
            global_classification_on_space.classification_hash
        ]

        classification_instances = space.get_classification_instances()
        assert len(classification_instances) == 1

    # Assert
    assert len(label_row._get_classification_instances(include_spaces=True)) == total_spaces + 1
    video_space = label_row._get_space(id="video-uuid", type_="video")
    annotations = list(video_space.get_classification_instance_annotations())
    assert len(annotations) == 1
