from unittest.mock import Mock

import pytest
from encord.exceptions import LabelRowError
from encord.objects import Classification, LabelRowV2, Object, OntologyStructure
from encord.objects.attributes import Attribute
from encord.objects.coordinates import BoundingBoxCoordinates
from encord.objects.spaces.video_space import VideoSpace
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.two_videos import (
    DATA_GROUP_METADATA,
)
from tests.objects.data.empty_video import labels as EMPTY_VIDEO_LABELS

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


def test_add_object_with_frame_data_to_root_video_space(ontology: OntologyStructure):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(EMPTY_VIDEO_LABELS)
    box_coordinates = BoundingBoxCoordinates(
        height=0.5,
        width=0.5,
        top_left_x=0.5,
        top_left_y=0.5,
    )
    root_space = label_row.get_space_by_id("root", type_=VideoSpace)

    new_object_instance = box_ontology_item.create_instance()
    new_object_instance.set_for_frames(coordinates=box_coordinates, frames=[0, 1, 2])

    # Act
    with pytest.raises(LabelRowError) as e:
        root_space.place_object(new_object_instance, frames=[0, 1, 2], coordinates=box_coordinates)

    # Assert
    assert e.value.message == (
        "Object instance contains frames data. "
        "Ensure ObjectInstance.set_for_frames was not used before calling this method. "
    )


def test_add_object_without_frame_data_to_root_video_space(ontology: OntologyStructure):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(EMPTY_VIDEO_LABELS)
    box_coordinates = BoundingBoxCoordinates(
        height=0.5,
        width=0.5,
        top_left_x=0.5,
        top_left_y=0.5,
    )
    root_space = label_row.get_space_by_id("root", type_=VideoSpace)

    new_object_instance = box_ontology_item.create_instance()

    root_space.place_object(new_object_instance, frames=[0, 1, 2], coordinates=box_coordinates)
    objects = root_space.get_objects()
    assert len(objects) == 1


def test_add_object_with_frame_data_to_label_row(ontology: OntologyStructure):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(EMPTY_VIDEO_LABELS)
    box_coordinates = BoundingBoxCoordinates(
        height=0.5,
        width=0.5,
        top_left_x=0.5,
        top_left_y=0.5,
    )

    new_object_instance = box_ontology_item.create_instance()
    new_object_instance.set_for_frames(coordinates=box_coordinates, frames=[0, 1, 2])
    root_space = label_row.get_space_by_id("root", type_=VideoSpace)
    assert len(new_object_instance.get_annotations()) == 3

    # Act
    label_row.add_object_instance(new_object_instance)

    # Assert
    assert len(label_row.get_object_instances()) == 1
    assert len(root_space.get_objects()) == 1

    annotation_on_root_space = root_space.get_object_annotations()
    assert len(annotation_on_root_space) == 3
    assert annotation_on_root_space[0].coordinates == box_coordinates

    annotations_on_object_instance = new_object_instance.get_annotations()
    assert len(annotations_on_object_instance) == 3
    assert annotations_on_object_instance[0].coordinates == box_coordinates

def test_update_frame_data_on_object_instance_attached_to_label_row(ontology: OntologyStructure):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(EMPTY_VIDEO_LABELS)
    box_coordinates = BoundingBoxCoordinates(
        height=0.5,
        width=0.5,
        top_left_x=0.5,
        top_left_y=0.5,
    )

    new_object_instance = box_ontology_item.create_instance()
    new_object_instance.set_for_frames(coordinates=box_coordinates, frames=[0, 1, 2])
    root_space = label_row.get_space_by_id("root", type_=VideoSpace)
    assert len(new_object_instance.get_annotations()) == 3
    label_row.add_object_instance(new_object_instance)

    # Act
    new_box_coordinates = BoundingBoxCoordinates(
        height=0.7,
        width=0.7,
        top_left_x=0.7,
        top_left_y=0.7,
    )

    new_object_instance.set_for_frames(frames=[5], coordinates=new_box_coordinates)

    # Assert
    annotation_on_root_space = root_space.get_object_annotations()
    assert len(annotation_on_root_space) == 4
    assert annotation_on_root_space[0].coordinates == box_coordinates

    annotations_on_object_instance = new_object_instance.get_annotations()
    assert len(annotations_on_object_instance) == 4
    assert annotations_on_object_instance[0].coordinates == box_coordinates

def test_add_object_without_frame_data_to_label_row(ontology: OntologyStructure):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(EMPTY_VIDEO_LABELS)
    new_object_instance = box_ontology_item.create_instance()

    # Act
    with pytest.raises(LabelRowError) as e:
        label_row.add_object_instance(new_object_instance)

    # Assert
    assert e.value.message == "ObjectInstance is not on any frames. Please add it to at least one frame."


def test_add_object_to_root_video_space(ontology: OntologyStructure):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(EMPTY_VIDEO_LABELS)
    box_coordinates = BoundingBoxCoordinates(
        height=0.5,
        width=0.5,
        top_left_x=0.5,
        top_left_y=0.5,
    )
    root_space = label_row.get_space_by_id("root", type_=VideoSpace)

    new_object_instance = box_ontology_item.create_instance()
    new_object_instance.set_for_frames(coordinates=box_coordinates, frames=[0, 1, 2])

    with pytest.raises(LabelRowError) as e:
        root_space.place_object(new_object_instance, frames=[0, 1, 2], coordinates=box_coordinates)

    assert e.value.message == (
        "Object instance contains frames data. "
        "Ensure ObjectInstance.set_for_frames was not used before calling this method. "
    )
