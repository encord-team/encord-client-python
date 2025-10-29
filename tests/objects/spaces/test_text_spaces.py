import json
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from deepdiff import DeepDiff

from encord.exceptions import LabelRowError
from encord.objects import Classification, LabelRowV2, Object
from encord.objects.attributes import Attribute
from encord.objects.frames import Range
from encord.objects.spaces.range_space import TextSpace
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.two_text import DATA_GROUP_TWO_TEXT_NO_LABELS, DATA_GROUP_WITH_TWO_TEXT_LABELS
from tests.objects.data.data_group.two_videos import (
    DATA_GROUP_METADATA,
)

text_obj_ontology_item = all_types_structure.get_child_by_hash("textFeatureNodeHash", Object)
text_obj_definition_attribute_ontology_item = text_obj_ontology_item.get_child_by_hash(
    "definitionFeatureHash", Attribute
)
text_classification = all_types_structure.get_child_by_hash("jPOcEsbw", Classification)


@pytest.fixture
def ontology():
    ontology_structure = Mock()
    ontology_structure.get_child_by_hash = all_types_structure.get_child_by_hash
    ontology = Mock(structure=ontology_structure)
    yield ontology


def test_add_object_to_text_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_TEXT_NO_LABELS)
    text_space_1 = label_row.get_space_by_id("text-1-uuid", type_=TextSpace)

    # Act
    new_object = label_row.create_space_object(ontology_class=text_obj_ontology_item)
    text_space_1.place_object(
        object=new_object,
        ranges=[Range(start=0, end=500)],
    )

    text_space_1.place_object(object=new_object, ranges=[Range(start=400, end=1000)])

    # Assert
    entities = text_space_1.get_objects()
    assert len(entities) == 1

    annotations = text_space_1.get_object_annotations()
    assert len(annotations) == 1

    first_annotation = annotations[0]

    assert first_annotation.ranges == [Range(start=0, end=1000)]
    assert first_annotation.object_hash == new_object.object_hash


def test_remove_object_from_text_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_TEXT_NO_LABELS)
    text_space_1 = label_row.get_space_by_id("text-1-uuid", type_=TextSpace)
    new_object = label_row.create_space_object(ontology_class=text_obj_ontology_item)
    text_space_1.place_object(
        object=new_object,
        ranges=[Range(start=0, end=500)],
    )

    entities = text_space_1.get_objects()
    assert len(entities) == 1

    annotations = text_space_1.get_object_annotations()
    assert len(annotations) == 1

    first_annotation = annotations[0]

    # Act
    text_space_1.remove_space_object(new_object.object_hash)

    # Assert
    annotations = text_space_1.get_object_annotations()
    assert len(annotations) == 0
    with pytest.raises(LabelRowError):
        assert first_annotation.ranges


def test_add_object_to_two_text(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_TEXT_NO_LABELS)
    text_space_1 = label_row.get_space_by_id("text-1-uuid", type_=TextSpace)
    text_space_2 = label_row.get_space_by_id("text-2-uuid", type_=TextSpace)

    new_object = label_row.create_space_object(ontology_class=text_obj_ontology_item)
    range_1 = Range(start=0, end=500)
    range_2 = Range(start=700, end=1000)

    # Act
    text_space_1.place_object(
        object=new_object,
        ranges=range_1,
    )
    text_space_2.place_object(object=new_object, ranges=range_2)

    # Assert
    entities = text_space_1.get_objects()
    assert len(entities) == 1

    annotations_on_text_space_1 = text_space_1.get_object_annotations()
    first_annotation_on_text_space_1 = annotations_on_text_space_1[0]
    assert len(annotations_on_text_space_1) == 1
    assert first_annotation_on_text_space_1.ranges == [range_1]

    annotations_on_text_space_2 = text_space_2.get_object_annotations()
    first_annotation_on_text_space_2 = annotations_on_text_space_2[0]
    assert len(annotations_on_text_space_2) == 1
    assert first_annotation_on_text_space_2.ranges == [range_2]


def test_update_attribute_for_object_which_exist_on_two_spaces(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_TEXT_NO_LABELS)
    text_space_1 = label_row.get_space_by_id("text-1-uuid", type_=TextSpace)
    text_space_2 = label_row.get_space_by_id("text-2-uuid", type_=TextSpace)

    new_object = label_row.create_space_object(ontology_class=text_obj_ontology_item)
    ranges = Range(start=0, end=500)

    text_space_1.place_object(
        object=new_object,
        ranges=ranges,
    )

    text_space_2.place_object(
        object=new_object,
        ranges=ranges,
    )

    object_answer = new_object.get_answer(attribute=text_obj_definition_attribute_ontology_item)
    assert object_answer is None

    # Act
    new_answer = "A work of art"
    new_object.set_answer(attribute=text_obj_definition_attribute_ontology_item, answer=new_answer)

    # Assert
    object_answer = new_object.get_answer(attribute=text_obj_definition_attribute_ontology_item)
    assert object_answer == new_answer

    object_on_text_space_1 = text_space_1.get_objects()[0]
    assert object_on_text_space_1.get_answer(text_obj_definition_attribute_ontology_item) == new_answer

    object_on_text_space_2 = text_space_2.get_objects()[0]
    assert object_on_text_space_2.get_answer(text_obj_definition_attribute_ontology_item) == new_answer

    object_answer_dict = label_row.to_encord_dict()["object_answers"]
    EXPECTED_DICT = {
        new_object.object_hash: {
            "classifications": [
                {
                    "name": "Definition",
                    "value": "definition",
                    "answers": new_answer,
                    "featureHash": "definitionFeatureHash",
                    "manualAnnotation": True,
                }
            ],
            "objectHash": new_object.object_hash,
            "range": [[0, 500]],
            "createdBy": None,
            "createdAt": "Wed, 29 Oct 2025 20:11:16 UTC",
            "lastEditedBy": None,
            "lastEditedAt": "Wed, 29 Oct 2025 20:11:16 UTC",
            "manualAnnotation": True,
            "featureHash": "textFeatureNodeHash",
            "name": "text object",
            "color": "#A4FF00",
            "shape": "text",
            "value": "text_object",
        }
    }

    assert not DeepDiff(
        object_answer_dict,
        EXPECTED_DICT,
        exclude_regex_paths=[r".*\['trackHash'\]", r".*\['createdAt'\]", r".*\['lastEditedAt'\]"],
    )


def test_read_and_export_labels(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_WITH_TWO_TEXT_LABELS)

    text_space_1 = label_row.get_space_by_id("text-1-uuid", type_=TextSpace)
    objects_on_text_space_1 = text_space_1.get_objects()
    assert len(objects_on_text_space_1) == 1

    # TODO: Need to somehow know which space an annotation is on
    text_object_instance = objects_on_text_space_1[0]
    assert text_object_instance.object_hash == "text1"

    annotations_on_text_space_1 = text_space_1.get_object_annotations()
    first_annotation_on_text_space_1 = annotations_on_text_space_1[0]
    assert first_annotation_on_text_space_1.ranges == [Range(start=10, end=50)]

    classifications_on_text_space_1 = text_space_1.get_classifications()
    assert len(classifications_on_text_space_1) == 1

    classification_instance = classifications_on_text_space_1[0]
    assert classification_instance.classification_hash == "classification1"

    output_dict = label_row.to_encord_dict()

    assert not DeepDiff(
        DATA_GROUP_WITH_TWO_TEXT_LABELS,
        output_dict,
        exclude_regex_paths=[r".*\['trackHash'\]"],
        ignore_order_func=lambda x: x.path().endswith("['objects']"),
    )
