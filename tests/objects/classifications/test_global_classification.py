from dataclasses import asdict
from unittest.mock import Mock

import pytest

from encord.exceptions import LabelRowError
from encord.objects import Classification, ClassificationInstance, FlatOption, LabelRowV2
from encord.orm.label_row import LabelRowMetadata
from tests.objects.common import FAKE_LABEL_ROW_METADATA
from tests.objects.data.all_ontology_types import global_classification_dict
from tests.objects.data.all_types_ontology_structure import GLOBAL_CLASSIFICATION, all_types_structure
from tests.objects.data.empty_image_group import empty_image_group_labels
from tests.objects.data.empty_video import labels

global_classification = all_types_structure.get_child_by_hash(GLOBAL_CLASSIFICATION.feature_node_hash, Classification)


def test_global_ontology_serde() -> None:
    assert GLOBAL_CLASSIFICATION.to_dict() == global_classification_dict
    assert Classification.from_dict(global_classification_dict) == GLOBAL_CLASSIFICATION


def test_global_classification_image_group(all_types_ontology) -> None:
    label_row_metadata_dict = asdict(FAKE_LABEL_ROW_METADATA)
    label_row_metadata_dict["frames_per_second"] = None  # not a thing in image groups
    label_row_metadata_dict["duration"] = None  # not a thing in image groups
    label_row_metadata = LabelRowMetadata(**label_row_metadata_dict)

    label_row = LabelRowV2(label_row_metadata, Mock(), all_types_ontology)
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

    # Assert on serialised data
    encord_dict_with_classification = label_row.to_encord_dict()
    for _, data_unit in encord_dict_with_classification["data_units"].items():
        assert data_unit["labels"]["classifications"] == [], f"{data_unit=} frame classifications are empty"

    serialised_answers = encord_dict_with_classification["classification_answers"]
    assert len(serialised_answers) == 1, "We have the answer we expect"

    label_row.remove_classification(classification_instance)

    assert len(label_row.get_classification_instances()) == 0, "A global classification can be removed"
    assert label_row.to_encord_dict() == empty_image_group_labels, (
        "The serialised dict should be the same as the original"
    )


def test_global_classification_override(all_types_ontology) -> None:
    label_row_metadata_dict = asdict(FAKE_LABEL_ROW_METADATA)
    label_row_metadata = LabelRowMetadata(**label_row_metadata_dict)

    label_row = LabelRowV2(label_row_metadata, Mock(), all_types_ontology)
    label_row.from_labels_dict(labels)  # initialise the empty video labels.

    answer_1 = global_classification.get_child_by_title("Global Answer 1", FlatOption)
    classification_instance_1 = ClassificationInstance(global_classification)
    classification_instance_1.set_answer(answer=[answer_1])

    answer_2 = global_classification.get_child_by_title("Global Answer 2", FlatOption)
    classification_instance_2 = ClassificationInstance(global_classification)
    classification_instance_2.set_answer(answer=[answer_2])

    assert classification_instance_1.range_list == [], "A global classification has an empty range list"
    assert classification_instance_2.range_list == [], "A global classification has an empty range list"

    # Test label_row interactions
    label_row.add_classification_instance(classification_instance_1)
    assert len(label_row.get_classification_instances()) == 1, "We can add a global classification"
    assert label_row.get_classification_instances()[0] == classification_instance_1, "And it's the one we expect"

    # We should be raising an error when trying to add the same classification
    with pytest.raises(LabelRowError):
        label_row.add_classification_instance(classification_instance_2)
    assert len(label_row.get_classification_instances()) == 1, "We've got the same number of classifications"
    assert label_row.get_classification_instances()[0] == classification_instance_1, "And it's the same one"

    label_row.add_classification_instance(classification_instance_2, force=True)
    assert len(label_row.get_classification_instances()) == 1, "After force overwriting, we should be left with one"
    assert label_row.get_classification_instances()[0] == classification_instance_2, "It should be the second"
