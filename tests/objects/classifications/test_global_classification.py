from dataclasses import asdict
from unittest.mock import Mock

import pytest

from encord.exceptions import LabelRowError
from encord.objects import Classification, ClassificationInstance, LabelRowV2
from encord.orm.label_row import LabelRowMetadata
from tests.objects.common import FAKE_LABEL_ROW_METADATA
from tests.objects.data.all_ontology_types import global_classification_dict
from tests.objects.data.all_types_ontology_structure import GLOBAL_CLASSIFICATION, all_types_structure
from tests.objects.data.empty_image_group import empty_image_group_labels

global_classification = all_types_structure.get_child_by_hash(GLOBAL_CLASSIFICATION.feature_node_hash, Classification)


def test_global_ontology_serde() -> None:
    assert GLOBAL_CLASSIFICATION.to_dict() == global_classification_dict
    assert Classification.from_dict(global_classification_dict) == GLOBAL_CLASSIFICATION


def test_global_classification_can_be_added_edited_and_removed(ontology) -> None:
    label_row_metadata_dict = asdict(FAKE_LABEL_ROW_METADATA)
    label_row_metadata_dict["number_of_frames"] = 100
    label_row_metadata = LabelRowMetadata(**label_row_metadata_dict)

    label_row = LabelRowV2(label_row_metadata, Mock(), ontology)
    label_row.from_labels_dict(empty_image_group_labels)  # initialise the labels.

    classification_instance = ClassificationInstance(global_classification)

    classification_instance.confidence = 0.5

    assert classification_instance.range_list == [], "A global classification has an empty range list"
    assert classification_instance.confidence == 0.5

    # You cannot get an annotation for a global classification
    with pytest.raises(LabelRowError):
        classification_instance.get_annotation(0)

    # Test label_row interactions
    label_row.add_classification_instance(classification_instance)
    assert len(label_row.get_classification_instances()) == 1, "A global classification can be added without frames"

    label_row.remove_classification(classification_instance)
    assert len(label_row.get_classification_instances()) == 0, "A global classification can be removed"
