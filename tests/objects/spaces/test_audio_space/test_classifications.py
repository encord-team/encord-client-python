from datetime import datetime
from unittest.mock import Mock

import pytest
from deepdiff import DeepDiff

from encord.common.time_parser import format_datetime_to_long_string
from encord.exceptions import LabelRowError
from encord.objects import Classification, LabelRowV2
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.two_audio import (
    DATA_GROUP_METADATA,
    DATA_GROUP_TWO_AUDIO_NO_LABELS,
)

text_classification = all_types_structure.get_child_by_hash("jPOcEsbw", Classification)
checklist_classification = all_types_structure.get_child_by_hash("3DuQbFxo", Classification)


@pytest.fixture
def ontology():
    ontology_structure = Mock()
    ontology_structure.get_child_by_hash = all_types_structure.get_child_by_hash
    ontology = Mock(structure=ontology_structure)
    yield ontology


def test_label_row_get_classification_instances_on_audio_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)

    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")
    audio_space_2 = label_row.get_space(id="audio-2-uuid", type_="audio")

    # Act
    classification_instance_1 = text_classification.create_instance()
    classification_instance_2 = checklist_classification.create_instance()

    # Place classification on space 1
    audio_space_1.place_classification(classification=classification_instance_1)
    audio_space_1.place_classification(classification=classification_instance_2)

    # Place classification on space 2
    audio_space_2.place_classification(classification=classification_instance_1)

    # Assert
    all_classification_instances = label_row.get_classification_instances()
    assert len(all_classification_instances) == 2

    # For backwards compatibility, all audio classifications are on frame=0
    classification_instances_on_frame_0 = label_row.get_classification_instances(filter_frames=0)
    assert len(classification_instances_on_frame_0) == 2

    classification_instances_on_frame_1 = label_row.get_classification_instances(filter_frames=1)
    assert len(classification_instances_on_frame_1) == 0


def test_place_classification_on_audio_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)

    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")

    # Act
    new_classification_instance = text_classification.create_instance()
    audio_space_1.place_classification(classification=new_classification_instance)

    text_answer = "Some answer"
    new_classification_instance.set_answer(answer=text_answer)

    # Assert
    classifications_on_label_row = label_row.get_classification_instances()
    assert len(classifications_on_label_row) == 1

    classifications_on_space = audio_space_1.get_classifications()
    classification_on_space = classifications_on_space[0]
    assert len(classifications_on_space) == 1
    assert classification_on_space._spaces == {audio_space_1.space_id: audio_space_1}

    annotations = audio_space_1.get_classification_annotations()
    assert len(annotations) == 1

    first_annotation = annotations[0]
    assert first_annotation.frame == 0
    assert first_annotation.classification_hash == new_classification_instance.classification_hash

    classification_answers_dict = label_row.to_encord_dict()["classification_answers"]

    expected_dict = {
        new_classification_instance.classification_hash: {
            "classifications": [
                {
                    "name": "Text classification",
                    "value": "text_classification",
                    "answers": text_answer,
                    "featureHash": "OxrtEM+v",
                    "manualAnnotation": True,
                }
            ],
            "classificationHash": new_classification_instance.classification_hash,
            "featureHash": "jPOcEsbw",
            "range": [],
            "createdBy": None,
            "lastEditedBy": None,
            "manualAnnotation": True,
        }
    }

    assert not DeepDiff(
        classification_answers_dict, expected_dict, exclude_regex_paths=[r".*\['lastEditedAt'\]", r".*\['createdAt'\]"]
    )


def test_place_classification_where_classification_already_exists(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")

    classification_instance_1 = text_classification.create_instance()

    audio_space_1.place_classification(classification=classification_instance_1)

    # Act
    with pytest.raises(LabelRowError) as e:
        audio_space_1.place_classification(classification=classification_instance_1)

    # Assert
    assert e.value.message == f"The classification '{classification_instance_1.classification_hash}' already exists."


def test_place_classification_on_where_classification_of_same_class_already_exists(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")

    classification_instance_1 = text_classification.create_instance()
    classification_instance_2 = text_classification.create_instance()
    text_answer_1 = "Answer 1"
    text_answer_2 = "Answer 2"

    classification_instance_1.set_answer(answer=text_answer_1)
    classification_instance_2.set_answer(answer=text_answer_2)

    audio_space_1.place_classification(classification=classification_instance_1)

    # Act
    with pytest.raises(LabelRowError) as e:
        audio_space_1.place_classification(classification=classification_instance_2)

    # Assert
    assert (
        e.value.message
        == f"A classification instance for the classification with feature hash '{text_classification.feature_node_hash}' already exists."
    )


def test_remove_classification_from_audio_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")

    new_classification_instance = text_classification.create_instance()
    audio_space_1.place_classification(classification=new_classification_instance)
    classifications_on_space = audio_space_1.get_classifications()
    assert len(classifications_on_space) == 1
    annotations = audio_space_1.get_classification_annotations()
    assert len(annotations) == 1

    # Act
    audio_space_1.remove_classification(new_classification_instance.classification_hash)

    # Assert
    classifications_on_label_row = label_row.get_classification_instances()
    assert len(classifications_on_label_row) == 0

    classifications_on_space = audio_space_1.get_classifications()
    assert len(classifications_on_space) == 0

    annotations = audio_space_1.get_classification_annotations()
    assert len(annotations) == 0


def test_get_classification_annotations(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")

    text_classification_instance = text_classification.create_instance()
    checklist_classification_instance = checklist_classification.create_instance()

    name_1 = "james"
    name_2 = "timmy"

    date1 = datetime(2020, 1, 1)
    date2 = datetime(2020, 5, 5)

    audio_space_1.place_classification(
        classification=text_classification_instance,
        last_edited_by=name_1,
        last_edited_at=date1,
    )

    audio_space_1.place_classification(
        classification=checklist_classification_instance,
        last_edited_by=name_2,
        last_edited_at=date2,
    )

    # Act
    classification_annotations = audio_space_1.get_classification_annotations()
    first_annotation = classification_annotations[0]
    second_annotation = classification_annotations[1]

    # Assert
    assert len(classification_annotations) == 2

    assert first_annotation.space.space_id == "audio-1-uuid"
    assert first_annotation.frame == 0
    assert first_annotation.classification_hash == text_classification_instance.classification_hash
    assert first_annotation.last_edited_by == name_1
    assert first_annotation.last_edited_at == date1

    assert second_annotation.space.space_id == "audio-1-uuid"
    assert second_annotation.frame == 0
    assert second_annotation.classification_hash == checklist_classification_instance.classification_hash
    assert second_annotation.last_edited_by == name_2
    assert second_annotation.last_edited_at == date2


def test_get_classification_annotations_with_filter_classifications(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")
    text_classification_instance = text_classification.create_instance()
    checklist_classification_instance = checklist_classification.create_instance()

    name_1 = "james"
    name_2 = "timmy"

    date1 = datetime(2020, 1, 1)
    date2 = datetime(2020, 5, 5)

    audio_space_1.place_classification(
        classification=text_classification_instance,
        last_edited_by=name_1,
        last_edited_at=date1,
    )

    audio_space_1.place_classification(
        classification=checklist_classification_instance,
        last_edited_by=name_2,
        last_edited_at=date2,
    )

    # Act
    annotations_for_classification_1 = audio_space_1.get_classification_annotations(
        filter_classifications=[text_classification_instance.classification_hash]
    )
    first_annotation_for_classification_1 = annotations_for_classification_1[0]

    annotations_for_classification_2 = audio_space_1.get_classification_annotations(
        filter_classifications=[checklist_classification_instance.classification_hash]
    )
    first_annotation_for_classification_2 = annotations_for_classification_2[0]

    # Assert
    assert len(annotations_for_classification_1) == 1
    assert first_annotation_for_classification_2.space.space_id == "audio-1-uuid"
    assert first_annotation_for_classification_1.frame == 0
    assert first_annotation_for_classification_1.classification_hash == text_classification_instance.classification_hash
    assert first_annotation_for_classification_1.last_edited_by == name_1
    assert first_annotation_for_classification_1.last_edited_at == date1

    assert len(annotations_for_classification_2) == 1
    assert first_annotation_for_classification_2.space.space_id == "audio-1-uuid"
    assert first_annotation_for_classification_2.frame == 0
    assert (
        first_annotation_for_classification_2.classification_hash
        == checklist_classification_instance.classification_hash
    )
    assert first_annotation_for_classification_2.last_edited_by == name_2
    assert first_annotation_for_classification_2.last_edited_at == date2


def test_get_classification_annotations_from_classification_instance(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")
    text_classification_instance = text_classification.create_instance()
    checklist_classification_instance = checklist_classification.create_instance()

    name_1 = "james"
    name_2 = "timmy"

    date1 = datetime(2020, 1, 1)
    date2 = datetime(2020, 5, 5)

    audio_space_1.place_classification(
        classification=text_classification_instance,
        last_edited_by=name_1,
        last_edited_at=date1,
    )

    audio_space_1.place_classification(
        classification=checklist_classification_instance,
        last_edited_by=name_2,
        last_edited_at=date2,
    )

    # Act
    annotations_for_classification_1 = text_classification_instance.get_annotations()
    first_annotation_for_classification_1 = annotations_for_classification_1[0]

    annotations_for_classification_2 = checklist_classification_instance.get_annotations()
    first_annotation_for_classification_2 = annotations_for_classification_2[0]

    # Assert
    assert len(annotations_for_classification_1) == 1
    assert first_annotation_for_classification_2.space.space_id == "audio-1-uuid"
    assert first_annotation_for_classification_1.frame == 0
    assert first_annotation_for_classification_1.classification_hash == text_classification_instance.classification_hash
    assert first_annotation_for_classification_1.last_edited_by == name_1
    assert first_annotation_for_classification_1.last_edited_at == date1

    assert len(annotations_for_classification_2) == 1
    assert first_annotation_for_classification_2.space.space_id == "audio-1-uuid"
    assert first_annotation_for_classification_2.frame == 0
    assert (
        first_annotation_for_classification_2.classification_hash
        == checklist_classification_instance.classification_hash
    )
    assert first_annotation_for_classification_2.last_edited_by == name_2
    assert first_annotation_for_classification_2.last_edited_at == date2


def test_update_annotation_from_object_annotation(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")
    classification_instance_1 = text_classification.create_instance()
    classification_instance_1.set_answer("Hi there")

    name = "james@encord.com"
    new_name = "timmy@encord.com"

    date = datetime(2020, 1, 1)
    new_date = datetime(2020, 5, 5)

    audio_space_1.place_classification(
        classification=classification_instance_1,
        created_at=date,
        last_edited_by=name,
        last_edited_at=date,
    )

    current_label_row_dict = label_row.to_encord_dict()
    current_classification_answers_dict = current_label_row_dict["classification_answers"]

    EXPECTED_CURRENT_CLASSIFICATION_ANSWERS_DICT = {
        classification_instance_1.classification_hash: {
            "classificationHash": classification_instance_1.classification_hash,
            "featureHash": text_classification.feature_node_hash,
            "range": [],
            "createdBy": None,
            "createdAt": format_datetime_to_long_string(date),
            "lastEditedBy": name,
            "lastEditedAt": format_datetime_to_long_string(date),
            "manualAnnotation": True,
            "classifications": [
                {
                    "name": "Text classification",
                    "value": "text_classification",
                    "answers": "Hi there",
                    "featureHash": "OxrtEM+v",
                    "manualAnnotation": True,
                }
            ],
        }
    }
    assert not DeepDiff(current_classification_answers_dict, EXPECTED_CURRENT_CLASSIFICATION_ANSWERS_DICT)

    # Act
    classification_annotations = audio_space_1.get_classification_annotations()
    classification_annotation = classification_annotations[0]

    classification_annotation.created_by = new_name
    classification_annotation.created_at = new_date
    classification_annotation.last_edited_by = new_name
    classification_annotation.last_edited_at = new_date

    # Assert
    new_label_row_dict = label_row.to_encord_dict()
    new_frame_dict = new_label_row_dict["classification_answers"]

    EXPECTED_NEW_CLASSIFICATION_ANSWERS_DICT = {
        classification_instance_1.classification_hash: {
            "classificationHash": classification_instance_1.classification_hash,
            "featureHash": text_classification.feature_node_hash,
            "range": [],
            "createdBy": new_name,
            "createdAt": format_datetime_to_long_string(new_date),
            "lastEditedBy": new_name,
            "lastEditedAt": format_datetime_to_long_string(new_date),
            "manualAnnotation": True,
            "classifications": [
                {
                    "name": "Text classification",
                    "value": "text_classification",
                    "answers": "Hi there",
                    "featureHash": "OxrtEM+v",
                    "manualAnnotation": True,
                }
            ],
        }
    }
    assert not DeepDiff(new_frame_dict, EXPECTED_NEW_CLASSIFICATION_ANSWERS_DICT)
