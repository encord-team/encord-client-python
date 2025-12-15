from datetime import datetime
from unittest.mock import Mock

import pytest
from deepdiff import DeepDiff

from encord.common.time_parser import format_datetime_to_long_string
from encord.exceptions import LabelRowError
from encord.objects import Classification, LabelRowV2, Object
from encord.objects.attributes import Attribute
from encord.objects.coordinates import BoundingBoxCoordinates
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.two_images import (
    DATA_GROUP_METADATA,
    DATA_GROUP_TWO_IMAGES_NO_LABELS,
)

box_ontology_item = all_types_structure.get_child_by_hash("MjI2NzEy", Object)
box_with_attributes_ontology_item = all_types_structure.get_child_by_hash("MTA2MjAx", Object)
box_text_attribute_ontology_item = box_with_attributes_ontology_item.get_child_by_hash("OTkxMjU1", type_=Attribute)
text_classification = all_types_structure.get_child_by_hash("jPOcEsbw", Classification)


def test_put_classification_on_image_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_IMAGES_NO_LABELS)
    image_space_1 = label_row.get_space(id="image-1-uuid", type_="image")
    coordinates_1 = BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0)
    coordinates_2 = BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.5, top_left_y=0.5)

    # Act
    object_instance_1 = box_ontology_item.create_instance()
    object_instance_2 = box_ontology_item.create_instance()
    image_space_1.put_object_instance(
        object_instance=object_instance_1,
        coordinates=coordinates_1,
    )
    image_space_1.put_object_instance(
        object_instance=object_instance_2,
        coordinates=coordinates_2,
    )

    # Assert
    object_instances = label_row.get_object_instances()
    assert len(object_instances) == 2

    objects_on_space = image_space_1.get_object_instances()
    object_on_space = objects_on_space[0]
    assert len(objects_on_space) == 2
    assert object_on_space._spaces == {image_space_1.space_id: image_space_1}

    annotations = image_space_1.get_object_instance_annotations()
    assert len(annotations) == 2

    first_annotation = annotations[0]
    assert first_annotation.frame == 0
    assert first_annotation.coordinates == coordinates_1
    assert first_annotation.object_hash == object_instance_1.object_hash

    second_annotation = annotations[1]
    assert second_annotation.frame == 0
    assert second_annotation.coordinates == coordinates_2
    assert second_annotation.object_hash == object_instance_2.object_hash


def test_put_classification_that_already_exists_image_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_IMAGES_NO_LABELS)
    image_space_1 = label_row.get_space(id="image-1-uuid", type_="image")
    new_object_instance = box_ontology_item.create_instance()
    image_space_1.put_object_instance(
        object_instance=new_object_instance,
        coordinates=BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0),
    )

    # Act
    with pytest.raises(LabelRowError) as e:
        image_space_1.put_object_instance(
            object_instance=new_object_instance,
            coordinates=BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.5, top_left_y=0.5),
        )

    # Assert
    assert (
        e.value.message
        == f"Annotation for object instance {new_object_instance.object_hash} already exists. Set 'on_overlap' to 'replace' to overwrite existing annotations."
    )


def test_put_classification_on_frames_with_overwrite_on_image_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_IMAGES_NO_LABELS)
    image_space_1 = label_row.get_space(id="image-1-uuid", type_="image")
    new_object_instance = box_ontology_item.create_instance()

    coordinates_1 = BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0)
    coordinates_2 = BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.5, top_left_y=0.5)
    image_space_1.put_object_instance(
        object_instance=new_object_instance,
        coordinates=coordinates_1,
    )

    # Act
    image_space_1.put_object_instance(
        object_instance=new_object_instance,
        coordinates=coordinates_2,
        on_overlap="replace",
    )

    # Assert
    object_annotations = image_space_1.get_object_instance_annotations()
    annotation_on_frame_1 = object_annotations[0]
    assert annotation_on_frame_1.frame == 0
    assert annotation_on_frame_1.coordinates == coordinates_2


def test_remove_object_from_image_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_IMAGES_NO_LABELS)
    image_space_1 = label_row.get_space(id="image-1-uuid", type_="image")
    new_object_instance = box_ontology_item.create_instance()
    box_coordinates = BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0)
    image_space_1.put_object_instance(
        object_instance=new_object_instance,
        coordinates=box_coordinates,
    )

    # Act
    image_space_1.remove_object_instance(
        object_hash=new_object_instance.object_hash,
    )

    # Assert
    object_instances = label_row.get_object_instances()
    assert len(object_instances) == 0

    objects_on_space = image_space_1.get_object_instances()
    assert len(objects_on_space) == 0

    annotations_on_space = image_space_1.get_object_instance_annotations()
    assert len(annotations_on_space) == 0

    annotations_on_object = new_object_instance.get_annotations()
    assert len(annotations_on_object) == 0


def test_add_object_to_two_spaces(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_IMAGES_NO_LABELS)
    image_space_1 = label_row.get_space(id="image-1-uuid", type_="image")
    image_space_2 = label_row.get_space(id="image-2-uuid", type_="image")

    new_object_instance = box_ontology_item.create_instance()
    box_coordinates_1 = BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.5, top_left_y=0.5)
    box_coordinates_2 = BoundingBoxCoordinates(height=0.8, width=0.8, top_left_x=0.8, top_left_y=0.8)

    # Act
    image_space_1.put_object_instance(
        object_instance=new_object_instance,
        coordinates=box_coordinates_1,
    )
    image_space_2.put_object_instance(
        object_instance=new_object_instance,
        coordinates=box_coordinates_2,
    )

    # Assert
    entities = image_space_1.get_object_instances()
    assert len(entities) == 1

    annotations_on_image_space_1 = image_space_1.get_object_instance_annotations()
    first_annotation_on_image_space_1 = annotations_on_image_space_1[0]
    assert len(annotations_on_image_space_1) == 1
    assert first_annotation_on_image_space_1.coordinates == box_coordinates_1

    annotations_on_image_space_2 = image_space_2.get_object_instance_annotations()
    first_annotation_on_image_space_2 = annotations_on_image_space_2[0]
    assert len(annotations_on_image_space_2) == 1
    assert first_annotation_on_image_space_2.coordinates == box_coordinates_2


def test_update_attribute_for_object_which_exist_on_two_spaces(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_IMAGES_NO_LABELS)
    image_space_1 = label_row.get_space(id="image-1-uuid", type_="image")
    image_space_2 = label_row.get_space(id="image-2-uuid", type_="image")

    new_object_instance = box_with_attributes_ontology_item.create_instance()
    box_coordinates_1 = BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.5, top_left_y=0.5)

    image_space_1.put_object_instance(
        object_instance=new_object_instance,
        coordinates=box_coordinates_1,
    )

    image_space_2.put_object_instance(
        object_instance=new_object_instance,
        coordinates=box_coordinates_1,
    )

    object_answer = new_object_instance.get_answer(attribute=box_text_attribute_ontology_item)
    assert object_answer is None

    # Act
    new_answer = "Hello!"
    new_object_instance.set_answer(attribute=box_text_attribute_ontology_item, answer=new_answer)

    # Assert
    object_answer = new_object_instance.get_answer(attribute=box_text_attribute_ontology_item)
    assert object_answer == new_answer

    object_on_image_space_1 = image_space_1.get_object_instances()[0]
    assert object_on_image_space_1.get_answer(box_text_attribute_ontology_item) == new_answer

    object_on_image_space_2 = image_space_2.get_object_instances()[0]
    assert object_on_image_space_2.get_answer(box_text_attribute_ontology_item) == new_answer

    object_answer_dict = label_row.to_encord_dict()["object_answers"]
    EXPECTED_DICT = {
        new_object_instance.object_hash: {
            "classifications": [
                {
                    "name": "First name",
                    "value": "first_name",
                    "answers": "Hello!",
                    "featureHash": "OTkxMjU1",
                    "manualAnnotation": True,
                }
            ],
            "objectHash": new_object_instance.object_hash,
        }
    }

    assert not DeepDiff(object_answer_dict, EXPECTED_DICT)


def test_get_object_annotations(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_IMAGES_NO_LABELS)
    image_space_1 = label_row.get_space(id="image-1-uuid", type_="image")
    object_instance_1 = box_ontology_item.create_instance()
    object_instance_2 = box_ontology_item.create_instance()

    coordinates_1 = BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0)
    coordinates_2 = BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.5, top_left_y=0.5)

    name_1 = "james"
    name_2 = "timmy"

    date1 = datetime(2020, 1, 1)
    date2 = datetime(2020, 5, 5)

    image_space_1.put_object_instance(
        object_instance=object_instance_1,
        coordinates=coordinates_1,
        last_edited_by=name_1,
        last_edited_at=date1,
    )

    image_space_1.put_object_instance(
        object_instance=object_instance_2,
        coordinates=coordinates_2,
        last_edited_by=name_2,
        last_edited_at=date2,
    )

    # Act
    object_annotations = image_space_1.get_object_instance_annotations()
    first_annotation = object_annotations[0]
    second_annotation = object_annotations[1]

    # Assert
    assert len(object_annotations) == 2

    assert first_annotation.space.space_id == "image-1-uuid"
    assert first_annotation.frame == 0
    assert first_annotation.object_hash == object_instance_1.object_hash
    assert first_annotation.coordinates == coordinates_1
    assert first_annotation.last_edited_by == name_1
    assert first_annotation.last_edited_at == date1

    assert second_annotation.space.space_id == "image-1-uuid"
    assert second_annotation.frame == 0
    assert second_annotation.object_hash == object_instance_2.object_hash
    assert second_annotation.coordinates == coordinates_2
    assert second_annotation.last_edited_by == name_2
    assert second_annotation.last_edited_at == date2


def test_get_object_annotations_with_filter_objects(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_IMAGES_NO_LABELS)
    image_space_1 = label_row.get_space(id="image-1-uuid", type_="image")
    object_instance_1 = box_ontology_item.create_instance()
    object_instance_2 = box_ontology_item.create_instance()

    coordinates_1 = BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0)
    coordinates_2 = BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.5, top_left_y=0.5)

    name_1 = "james"
    name_2 = "timmy"

    date1 = datetime(2020, 1, 1)
    date2 = datetime(2020, 5, 5)

    image_space_1.put_object_instance(
        object_instance=object_instance_1,
        coordinates=coordinates_1,
        last_edited_by=name_1,
        last_edited_at=date1,
    )

    image_space_1.put_object_instance(
        object_instance=object_instance_2,
        coordinates=coordinates_2,
        last_edited_by=name_2,
        last_edited_at=date2,
    )

    # Act
    object_annotations_for_object_1 = image_space_1.get_object_instance_annotations(
        filter_object_instances=[object_instance_1.object_hash]
    )
    first_annotation_for_object_1 = object_annotations_for_object_1[0]

    object_annotations_for_object_2 = image_space_1.get_object_instance_annotations(
        filter_object_instances=[object_instance_2.object_hash]
    )
    first_annotation_for_object_2 = object_annotations_for_object_2[0]

    # Assert
    assert len(object_annotations_for_object_1) == 1
    assert first_annotation_for_object_1.space.space_id == "image-1-uuid"
    assert first_annotation_for_object_1.frame == 0
    assert first_annotation_for_object_1.object_hash == object_instance_1.object_hash
    assert first_annotation_for_object_1.coordinates == coordinates_1
    assert first_annotation_for_object_1.last_edited_by == name_1
    assert first_annotation_for_object_1.last_edited_at == date1

    assert len(object_annotations_for_object_2) == 1
    assert first_annotation_for_object_2.space.space_id == "image-1-uuid"
    assert first_annotation_for_object_2.frame == 0
    assert first_annotation_for_object_2.object_hash == object_instance_2.object_hash
    assert first_annotation_for_object_2.coordinates == coordinates_2
    assert first_annotation_for_object_2.last_edited_by == name_2
    assert first_annotation_for_object_2.last_edited_at == date2


def test_get_object_annotations_from_object_instance(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_IMAGES_NO_LABELS)
    image_space_1 = label_row.get_space(id="image-1-uuid", type_="image")
    object_instance_1 = box_ontology_item.create_instance()
    object_instance_2 = box_ontology_item.create_instance()

    coordinates_1 = BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0)
    coordinates_2 = BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.5, top_left_y=0.5)

    name_1 = "james"
    name_2 = "timmy"

    date1 = datetime(2020, 1, 1)
    date2 = datetime(2020, 5, 5)

    image_space_1.put_object_instance(
        object_instance=object_instance_1,
        coordinates=coordinates_1,
        last_edited_by=name_1,
        last_edited_at=date1,
    )

    image_space_1.put_object_instance(
        object_instance=object_instance_2,
        coordinates=coordinates_2,
        last_edited_by=name_2,
        last_edited_at=date2,
    )

    # Act
    object_annotations_for_object_1 = object_instance_1.get_annotations()
    first_annotation_for_object_1 = object_annotations_for_object_1[0]

    object_annotations_for_object_2 = object_instance_2.get_annotations()
    first_annotation_for_object_2 = object_annotations_for_object_2[0]

    # Assert
    assert len(object_annotations_for_object_1) == 1
    assert first_annotation_for_object_1.space.space_id == "image-1-uuid"
    assert first_annotation_for_object_1.frame == 0
    assert first_annotation_for_object_1.object_hash == object_instance_1.object_hash
    assert first_annotation_for_object_1.coordinates == coordinates_1
    assert first_annotation_for_object_1.last_edited_by == name_1
    assert first_annotation_for_object_1.last_edited_at == date1

    assert len(object_annotations_for_object_2) == 1
    assert first_annotation_for_object_2.space.space_id == "image-1-uuid"
    assert first_annotation_for_object_2.frame == 0
    assert first_annotation_for_object_2.object_hash == object_instance_2.object_hash
    assert first_annotation_for_object_2.coordinates == coordinates_2
    assert first_annotation_for_object_2.last_edited_by == name_2
    assert first_annotation_for_object_2.last_edited_at == date2


def test_update_annotation_from_object_annotation(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_IMAGES_NO_LABELS)
    image_space_1 = label_row.get_space(id="image-1-uuid", type_="image")
    object_instance = box_ontology_item.create_instance()

    coordinates = BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0)
    new_coordinates = BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.5, top_left_y=0.5)

    name = "james@encord.com"
    new_name = "timmy@encord.com"

    date = datetime(2020, 1, 1)
    new_date = datetime(2020, 5, 5)

    image_space_1.put_object_instance(
        object_instance=object_instance,
        coordinates=coordinates,
        last_edited_by=name,
        last_edited_at=date,
        created_at=date,
    )

    current_label_row_dict = label_row.to_encord_dict()
    current_frame_dict = current_label_row_dict["spaces"]["image-1-uuid"]["labels"]

    EXPECTED_CURRENT_LABELS_DICT = {
        "0": {
            "objects": [
                {
                    "objectHash": object_instance.object_hash,
                    "featureHash": "MjI2NzEy",
                    "name": "Box",
                    "color": "#D33115",
                    "value": "box",
                    "createdAt": format_datetime_to_long_string(date),
                    "manualAnnotation": True,
                    "confidence": 1.0,
                    "lastEditedAt": format_datetime_to_long_string(date),
                    "lastEditedBy": name,
                    "boundingBox": coordinates.to_dict(),
                    "shape": "bounding_box",
                }
            ],
            "classifications": [],
        }
    }
    assert not DeepDiff(current_frame_dict, EXPECTED_CURRENT_LABELS_DICT)

    # Act
    object_annotations = image_space_1.get_object_instance_annotations()
    object_annotation = object_annotations[0]

    object_annotation.created_by = new_name
    object_annotation.created_at = new_date
    object_annotation.last_edited_by = new_name
    object_annotation.last_edited_at = new_date
    object_annotation.coordinates = new_coordinates

    # Assert
    new_label_row_dict = label_row.to_encord_dict()
    new_frame_label_dict = new_label_row_dict["spaces"]["image-1-uuid"]["labels"]

    EXPECTED_CURRENT_LABELS_DICT = {
        "0": {
            "objects": [
                {
                    "objectHash": object_instance.object_hash,
                    "featureHash": "MjI2NzEy",
                    "name": "Box",
                    "color": "#D33115",
                    "value": "box",
                    "createdAt": format_datetime_to_long_string(new_date),
                    "manualAnnotation": True,
                    "confidence": 1.0,
                    "createdBy": new_name,
                    "lastEditedAt": format_datetime_to_long_string(new_date),
                    "lastEditedBy": new_name,
                    "boundingBox": new_coordinates.to_dict(),
                    "shape": "bounding_box",
                }
            ],
            "classifications": [],
        }
    }
    assert not DeepDiff(new_frame_label_dict, EXPECTED_CURRENT_LABELS_DICT)
