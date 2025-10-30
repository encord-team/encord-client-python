from unittest.mock import Mock

import pytest
from deepdiff import DeepDiff

from encord.exceptions import LabelRowError
from encord.objects import Classification, LabelRowV2, Object
from encord.objects.attributes import Attribute
from encord.objects.coordinates import BoundingBoxCoordinates
from encord.objects.spaces.image_space import ImageSpace
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.two_images import DATA_GROUP_TWO_IMAGES_NO_LABELS, DATA_GROUP_WITH_TWO_IMAGES_LABELS
from tests.objects.data.data_group.two_videos import (
    DATA_GROUP_METADATA,
)

segmentation_ontology_item = all_types_structure.get_child_by_hash("segmentationFeatureNodeHash", Object)
box_ontology_item = all_types_structure.get_child_by_hash("MjI2NzEy", Object)
box_with_attributes_ontology_item = all_types_structure.get_child_by_hash("MTA2MjAx", Object)
box_text_attribute_ontology_item = box_with_attributes_ontology_item.get_child_by_hash("OTkxMjU1", type_=Attribute)

audio_obj_ontology_item = all_types_structure.get_child_by_hash("KVfzNkFy", Object)
text_classification = all_types_structure.get_child_by_hash("jPOcEsbw", Classification)


@pytest.fixture
def ontology():
    ontology_structure = Mock()
    ontology_structure.get_child_by_hash = all_types_structure.get_child_by_hash
    ontology = Mock(structure=ontology_structure)
    yield ontology


def test_add_object_to_image_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_IMAGES_NO_LABELS)
    image_space_1 = label_row.get_space_by_id("image-1-uuid", type_=ImageSpace)

    # Act
    new_object = label_row.create_space_object(ontology_class=box_ontology_item)
    coordinates = BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0)
    image_space_1.place_object(
        object=new_object,
        coordinates=coordinates,
    )

    # Assert
    space_objects_on_label_row = label_row.list_space_objects()
    assert len(space_objects_on_label_row) == 1

    space_objects = image_space_1.get_objects()
    space_object = space_objects[0]
    assert len(space_objects) == 1
    assert space_object.spaces == {image_space_1.space_id: image_space_1}

    annotations = image_space_1.get_object_annotations()
    assert len(annotations) == 1

    first_annotation = annotations[0]
    assert first_annotation.coordinates == coordinates
    assert first_annotation.object_hash == new_object.object_hash


def test_remove_object_from_image_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_IMAGES_NO_LABELS)
    image_space_1 = label_row.get_space_by_id("image-1-uuid", type_=ImageSpace)
    new_object = label_row.create_space_object(ontology_class=box_ontology_item)
    image_space_1.place_object(
        object=new_object,
        coordinates=BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.5, top_left_y=0.5),
    )

    space_objects = image_space_1.get_objects()
    assert len(space_objects) == 1

    annotations = image_space_1.get_object_annotations()
    assert len(annotations) == 1

    first_annotation = annotations[0]

    # Act
    image_space_1.remove_space_object(new_object.object_hash)

    # Assert
    space_objects_on_label_row = label_row.list_space_objects()
    space_object_on_label_row = space_objects_on_label_row[0]

    assert len(space_objects_on_label_row) == 1
    assert space_object_on_label_row.spaces == {}

    space_objects = image_space_1.get_objects()
    assert len(space_objects) == 0

    annotations = image_space_1.get_object_annotations()
    assert len(annotations) == 0
    with pytest.raises(LabelRowError):
        assert first_annotation.coordinates


def test_add_object_to_two_spaces(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_IMAGES_NO_LABELS)
    image_space_1 = label_row.get_space_by_id("image-1-uuid", type_=ImageSpace)
    image_space_2 = label_row.get_space_by_id("image-2-uuid", type_=ImageSpace)

    new_object = label_row.create_space_object(ontology_class=box_ontology_item)
    box_coordinates_1 = BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.5, top_left_y=0.5)
    box_coordinates_2 = BoundingBoxCoordinates(height=0.8, width=0.8, top_left_x=0.8, top_left_y=0.8)

    # Act
    image_space_1.place_object(
        object=new_object,
        coordinates=box_coordinates_1,
    )
    image_space_2.place_object(object=new_object, coordinates=box_coordinates_2)

    # Assert
    entities = image_space_1.get_objects()
    assert len(entities) == 1

    annotations_on_video_space_1 = image_space_1.get_object_annotations()
    first_annotation_on_video_space_1 = annotations_on_video_space_1[0]
    assert len(annotations_on_video_space_1) == 1
    assert first_annotation_on_video_space_1.coordinates == box_coordinates_1

    annotations_on_video_space_2 = image_space_2.get_object_annotations()
    first_annotation_on_video_space_2 = annotations_on_video_space_2[0]
    assert len(annotations_on_video_space_2) == 1
    assert first_annotation_on_video_space_2.coordinates == box_coordinates_2


def test_update_attribute_for_object_which_exist_on_two_spaces(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_IMAGES_NO_LABELS)
    image_space_1 = label_row.get_space_by_id("image-1-uuid", type_=ImageSpace)
    image_space_2 = label_row.get_space_by_id("image-2-uuid", type_=ImageSpace)

    new_object = label_row.create_space_object(ontology_class=box_with_attributes_ontology_item)
    box_coordinates_1 = BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.5, top_left_y=0.5)

    image_space_1.place_object(
        object=new_object,
        coordinates=box_coordinates_1,
    )
    image_space_2.place_object(object=new_object, coordinates=box_coordinates_1)

    object_answer = new_object.get_answer(attribute=box_text_attribute_ontology_item)
    assert object_answer is None

    # Act
    new_answer = "Hello!"
    new_object.set_answer(attribute=box_text_attribute_ontology_item, answer=new_answer)

    # Assert
    object_answer = new_object.get_answer(attribute=box_text_attribute_ontology_item)
    assert object_answer == new_answer

    object_on_video_space_1 = image_space_1.get_objects()[0]
    assert object_on_video_space_1.get_answer(box_text_attribute_ontology_item) == new_answer

    object_on_video_space_2 = image_space_2.get_objects()[0]
    assert object_on_video_space_2.get_answer(box_text_attribute_ontology_item) == new_answer

    object_answer_dict = label_row.to_encord_dict()["object_answers"]
    EXPECTED_DICT = {
        new_object.object_hash: {
            "classifications": [
                {
                    "name": "First name",
                    "value": "first_name",
                    "answers": "Hello!",
                    "featureHash": "OTkxMjU1",
                    "manualAnnotation": True,
                }
            ],
            "objectHash": new_object.object_hash,
        }
    }
    assert not DeepDiff(object_answer_dict, EXPECTED_DICT)


def test_add_classification_to_image_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_IMAGES_NO_LABELS)
    image_space_1 = label_row.get_space_by_id("image-1-uuid", type_=ImageSpace)

    # Act
    created_by = "arthur@encord.com"
    new_classification = label_row.create_space_classification(ontology_class=text_classification)
    image_space_1.place_classification(classification=new_classification, created_by=created_by)
    image_space_1.place_classification(classification=new_classification)

    text_answer = "Some answer"
    new_classification.set_answer(answer=text_answer)

    # Assert
    entities = image_space_1.get_classifications()
    assert len(entities) == 1

    annotations = image_space_1.get_classification_annotations()
    assert len(annotations) == 1

    first_annotation = annotations[0]
    assert first_annotation.created_by == created_by
    assert first_annotation.classification_hash == new_classification.classification_hash

    classification_answers_dict = label_row.to_encord_dict()["classification_answers"]
    expected_dict = {
        new_classification.classification_hash: {
            "classifications": [
                {
                    "name": "Text classification",
                    "value": "text_classification",
                    "answers": text_answer,
                    "featureHash": "OxrtEM+v",
                    "manualAnnotation": True,
                }
            ],
            "classificationHash": new_classification.classification_hash,
            "featureHash": "jPOcEsbw",
        }
    }

    assert not DeepDiff(classification_answers_dict, expected_dict)


def test_remove_classification_from_image_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_IMAGES_NO_LABELS)
    image_space_1 = label_row.get_space_by_id("image-1-uuid", type_=ImageSpace)

    new_classification = label_row.create_space_classification(ontology_class=text_classification)
    image_space_1.place_classification(classification=new_classification)
    entities = image_space_1.get_classifications()
    assert len(entities) == 1
    annotations = image_space_1.get_classification_annotations()
    assert len(annotations) == 1

    # Act
    image_space_1.remove_space_classification(new_classification.classification_hash)

    # Assert
    entities = image_space_1.get_classifications()
    assert len(entities) == 0
    annotations = image_space_1.get_classification_annotations()
    assert len(annotations) == 0


def test_read_and_export_labels(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_WITH_TWO_IMAGES_LABELS)

    image_space_1 = label_row.get_space_by_id("image-1-uuid", type_=ImageSpace)
    image_space_1_object_annotations = image_space_1.get_object_annotations()
    assert len(image_space_1_object_annotations) == 1

    image_space_1_objects = image_space_1.get_objects()
    assert len(image_space_1_objects) == 1

    image_space_1_classification_annotations = image_space_1.get_classification_annotations()
    assert len(image_space_1_classification_annotations) == 1
    classification_entities = image_space_1.get_classifications()
    assert len(classification_entities) == 1

    output_dict = label_row.to_encord_dict()

    assert not DeepDiff(
        DATA_GROUP_WITH_TWO_IMAGES_LABELS,
        output_dict,
        exclude_regex_paths=[r".*\['trackHash'\]"],
        ignore_order_func=lambda x: x.path().endswith("['objects']"),
    )
