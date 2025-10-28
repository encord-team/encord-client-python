import json
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from deepdiff import DeepDiff

from encord.exceptions import LabelRowError
from encord.objects import Classification, LabelRowV2, Object
from encord.objects.attributes import Attribute
from encord.objects.constants import DEFAULT_MANUAL_ANNOTATION
from encord.objects.coordinates import BoundingBoxCoordinates
from encord.objects.spaces.annotation_instance.base_instance import BaseObjectInstance
from encord.objects.spaces.annotation_instance.image_instance import ImageObjectInstance
from encord.objects.spaces.annotation_instance.video_instance import VideoObjectInstance
from encord.objects.spaces.video_space import VideoSpace
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.two_videos import (
    DATA_GROUP_METADATA,
    DATA_GROUP_TWO_VIDEOS_NO_LABELS,
    DATA_GROUP_WITH_TWO_VIDEOS_LABELS,
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

def test_add_object_entity_to_video_space(ontology):

    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space_by_id("video-1-uuid", type_=VideoSpace)

    # Act
    new_entity = label_row.create_entity(ontology_class=box_ontology_item)
    video_space_1.place_object_entity(entity=new_entity, frames=[1], coordinates=BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0))
    video_space_1.place_object_entity(entity=new_entity, frames=[0, 2, 3], coordinates=BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.5, top_left_y=0.5))

    # Assert
    entities = video_space_1.get_object_entities()
    assert len(entities) == 1

    annotations = video_space_1.get_object_annotations()
    assert len(annotations) == 4

    first_annotation = annotations[0]
    assert first_annotation.frame == 0
    assert first_annotation.coordinates == BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.5, top_left_y=0.5)


def test_remove_object_entity_from_video_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space_by_id("video-1-uuid", type_=VideoSpace)
    new_entity = label_row.create_entity(ontology_class=box_ontology_item)
    video_space_1.place_object_entity(
        entity=new_entity,
        frames=[0, 1, 2],
        coordinates=BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.5, top_left_y=0.5),
    )

    entities = video_space_1.get_object_entities()
    assert len(entities) == 1

    annotations = video_space_1.get_object_annotations()
    assert len(annotations) == 3

    first_annotation = annotations[0]

    # Act
    video_space_1.remove_entity(new_entity.entity_hash)

    # Assert
    annotations = video_space_1.get_object_annotations()
    assert len(annotations) == 0
    with pytest.raises(LabelRowError):
        assert first_annotation.coordinates

def test_add_object_entity_to_two_spaces(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space_by_id("video-1-uuid", type_=VideoSpace)
    video_space_2 = label_row.get_space_by_id("video-2-uuid", type_=VideoSpace)

    new_entity = label_row.create_entity(ontology_class=box_ontology_item)
    box_coordinates_1 = BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.5, top_left_y=0.5)
    box_coordinates_2 = BoundingBoxCoordinates(height=0.8, width=0.8, top_left_x=0.8, top_left_y=0.8)

    # Act
    video_space_1.place_object_entity(
        entity=new_entity,
        frames=[0, 1, 2],
        coordinates=box_coordinates_1,
    )
    video_space_2.place_object_entity(
        entity=new_entity,
        frames=[4, 5],
        coordinates=box_coordinates_2
    )

    # Assert
    entities = video_space_1.get_object_entities()
    assert len(entities) == 1

    annotations_on_video_space_1 = video_space_1.get_object_annotations()
    first_annotation_on_video_space_1 = annotations_on_video_space_1[0]
    assert len(annotations_on_video_space_1) == 3
    assert first_annotation_on_video_space_1.coordinates == box_coordinates_1

    annotations_on_video_space_2 = video_space_2.get_object_annotations()
    first_annotation_on_video_space_2 = annotations_on_video_space_2[0]
    assert len(annotations_on_video_space_2) == 2
    assert first_annotation_on_video_space_2.coordinates == box_coordinates_2

def test_update_attribute_for_object_entity_which_exist_on_two_spaces(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space_by_id("video-1-uuid", type_=VideoSpace)
    video_space_2 = label_row.get_space_by_id("video-2-uuid", type_=VideoSpace)

    new_entity = label_row.create_entity(ontology_class=box_with_attributes_ontology_item)
    box_coordinates_1 = BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.5, top_left_y=0.5)

    video_space_1.place_object_entity(
        entity=new_entity,
        frames=[0, 1, 2],
        coordinates=box_coordinates_1,
    )
    video_space_2.place_object_entity(
        entity=new_entity,
        frames=[4, 5],
        coordinates=box_coordinates_1
    )

    entity_answer = new_entity.get_answer(attribute=box_text_attribute_ontology_item)
    assert entity_answer is None

    # Act
    new_answer = "Hello!"
    new_entity.set_answer(attribute=box_text_attribute_ontology_item, answer=new_answer)

    # Assert
    entity_answer = new_entity.get_answer(attribute=box_text_attribute_ontology_item)
    assert entity_answer == new_answer

    entity_on_video_space_1 = video_space_1.get_object_entities()[0]
    assert entity_on_video_space_1.get_answer(box_text_attribute_ontology_item) == new_answer

    entity_on_video_space_2 = video_space_2.get_object_entities()[0]
    assert entity_on_video_space_2.get_answer(box_text_attribute_ontology_item) == new_answer

def test_add_classification_entity_to_video_space(ontology):

    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space_by_id("video-1-uuid", type_=VideoSpace)

    # Act
    new_entity = label_row.create_entity(ontology_class=text_classification)
    video_space_1.place_classification_entity(entity=new_entity, frames=[1])
    video_space_1.place_classification_entity(entity=new_entity, frames=[0, 2, 3])

    # Assert
    entities = video_space_1.get_classification_entities()
    assert len(entities) == 1

    annotations = video_space_1.get_classification_annotations()
    assert len(annotations) == 4

    first_annotation = annotations[0]
    assert first_annotation.frame == 0


def test_read_and_export_video_space_labels(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_WITH_TWO_VIDEOS_LABELS)

    video_space_1 = label_row.get_space_by_id("video-1-uuid", type_=VideoSpace)
    video_space_1_object_annotations = video_space_1.get_object_annotations()
    assert len(video_space_1_object_annotations) == 4

    video_space_1_object_entities = video_space_1.get_object_entities()
    assert len(video_space_1_object_entities) == 2

    video_space_1_classification_annotations = video_space_1.get_classification_annotations()
    assert len(video_space_1_classification_annotations) == 1
    classification_entities = video_space_1.get_classification_entities()
    assert len(classification_entities) == 1

    output_dict = label_row.to_encord_dict()

    assert not DeepDiff(
        DATA_GROUP_WITH_TWO_VIDEOS_LABELS,
        output_dict,
        exclude_regex_paths=[r".*\['trackHash'\]"],
        ignore_order_func=lambda x: x.path().endswith("['objects']"),
    )
