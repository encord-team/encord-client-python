import json
from unittest.mock import Mock

import pytest
from deepdiff import DeepDiff

from encord.objects import LabelRowV2, Object
from encord.objects.coordinates import BoundingBoxCoordinates
from encord.objects.space import VisionSpace
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group import DATA_GROUP_METADATA, EMPTY_DATA_GROUP_LABELS, EXPECTED_DATA_GROUP_WITH_LABELS

segmentation_ontology_item = all_types_structure.get_child_by_hash("segmentationFeatureNodeHash", Object)
box_ontology_item = all_types_structure.get_child_by_hash("MjI2NzEy", Object)
audio_obj_ontology_item = all_types_structure.get_child_by_hash("KVfzNkFy", Object)

@pytest.fixture
def ontology():
    ontology_structure = Mock()
    ontology_structure.get_child_by_hash = all_types_structure.get_child_by_hash
    ontology = Mock(structure=ontology_structure)
    yield ontology

def test_vision_space_can_add_object_instances(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(EMPTY_DATA_GROUP_LABELS)

    frame_0_box_coordinates = BoundingBoxCoordinates(
        height=0.1,
        width=0.2,
        top_left_x=0.3,
        top_left_y=0.4,
    )

    vision_space = label_row.get_space_by_id("video-1-uuid", type_=VisionSpace)
    # Check that no objects exist on space
    objects_on_vision_space = vision_space.get_object_instances()
    assert(len(objects_on_vision_space) == 0)

    # After adding, check that object exists, and has correct properties
    added_object_instance = vision_space.add_object_instance(obj=box_ontology_item, frames=[0, 1], coordinates=frame_0_box_coordinates)
    objects_on_vision_space = vision_space.get_object_instances()
    assert(len(objects_on_vision_space) == 1)

    first_object_instance = objects_on_vision_space[0]
    annotations_on_first_object_instance = first_object_instance.get_annotations()
    assert first_object_instance.object_hash == added_object_instance.object_hash
    assert(len(annotations_on_first_object_instance) == 2)

    frames_on_annotations = [annotation.frame for annotation in annotations_on_first_object_instance]
    assert frames_on_annotations == [0, 1]
    for annotation in annotations_on_first_object_instance:
        assert annotation.coordinates == frame_0_box_coordinates

    # Check that spaces has correct properties
    assert len(vision_space._frames_to_hashes[0]) == 1
    assert len(vision_space._frames_to_hashes[1]) == 1
    assert added_object_instance.object_hash in vision_space._objects_map


def test_vision_space_can_remove_object_instances(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(EMPTY_DATA_GROUP_LABELS)

    frame_0_box_coordinates = BoundingBoxCoordinates(
        height=0.1,
        width=0.2,
        top_left_x=0.3,
        top_left_y=0.4,
    )

    vision_space = label_row.get_space_by_id("video-1-uuid", type_=VisionSpace)

    assert vision_space is not None
    added_object_instance = vision_space.add_object_instance(obj=box_ontology_item, frames=[0, 1], coordinates=frame_0_box_coordinates)
    objects_on_vision_space = vision_space.get_object_instances()

    # Check properties after adding object
    assert(len(objects_on_vision_space) == 1)
    assert len(vision_space._frames_to_hashes[0]) == 1
    assert len(vision_space._frames_to_hashes[1]) == 1
    assert added_object_instance.object_hash in vision_space._objects_map

    # Check properties after removing object
    vision_space.remove_object_instance(added_object_instance.object_hash)
    objects_on_vision_space = vision_space.get_object_instances()
    assert(len(objects_on_vision_space) == 0)
    assert len(vision_space._frames_to_hashes[0]) == 0
    assert len(vision_space._frames_to_hashes[1]) == 0


def test_vision_space_move_object_instances(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(EMPTY_DATA_GROUP_LABELS)

    frame_0_box_coordinates = BoundingBoxCoordinates(
        height=0.1,
        width=0.2,
        top_left_x=0.3,
        top_left_y=0.4,
    )

    vision_space_1 = label_row.get_space_by_id("video-1-uuid", type_=VisionSpace)
    object_on_vision_space_1 = vision_space_1.add_object_instance(obj=box_ontology_item, frames=[0, 1], coordinates=frame_0_box_coordinates)
    objects_on_vision_space_1 = vision_space_1.get_object_instances()

    # Check properties of vision space 1 before moving object
    assert(len(objects_on_vision_space_1) == 1)
    assert len(vision_space_1._frames_to_hashes[0]) == 1
    assert len(vision_space_1._frames_to_hashes[1]) == 1
    assert object_on_vision_space_1.object_hash in vision_space_1._objects_map

    # Check properties of vision space 2 before moving object
    vision_space_2 = label_row.get_space_by_id("video-2-uuid", type_=VisionSpace)
    objects_on_vision_space_2 = vision_space_2.get_object_instances()
    assert(len(objects_on_vision_space_2) == 0)
    assert len(vision_space_2._frames_to_hashes.keys()) == 0
    assert len(vision_space_2._frames_to_hashes.keys()) == 0

    # Move object from space 1 to space 2
    vision_space_2.move_object_instance_from_space(object_on_vision_space_1)

    # Check properties of vision space 1 after moving object
    objects_on_vision_space_1 = vision_space_1.get_object_instances()
    assert(len(objects_on_vision_space_1) == 0)
    assert len(vision_space_1._frames_to_hashes[0]) == 0
    assert len(vision_space_1._frames_to_hashes[1]) == 0

    # Check properties of vision space 2 after moving object
    objects_on_vision_space_2 = vision_space_2.get_object_instances()
    assert(len(objects_on_vision_space_2) == 1)
    assert len(vision_space_2._frames_to_hashes[0]) == 1
    assert len(vision_space_2._frames_to_hashes[1]) == 1

def test_read_and_export_labels(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(EXPECTED_DATA_GROUP_WITH_LABELS)

    vision_space_1 = label_row.get_space_by_id("video-1-uuid", type_=VisionSpace)
    objects_on_vision_space_1 = vision_space_1.get_object_instances()
    assert(len(objects_on_vision_space_1) == 1)

    object1 = objects_on_vision_space_1[0]
    assert(object1.object_hash == "object1")
    assert(object1.get_annotation_frames() == {0, 1})

    final_res = label_row.to_encord_dict()
    print(json.dumps(final_res, indent=2))

    assert not DeepDiff(EXPECTED_DATA_GROUP_WITH_LABELS, label_row.to_encord_dict())
# def test_spaces(ontology):
# #     label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
# #     label_row.from_labels_dict(EMPTY_DATA_GROUP_LABELS)
# #
# #     frame_0_box_coordinates = BoundingBoxCoordinates(
# #         height=0.1,
# #         width=0.2,
# #         top_left_x=0.3,
# #         top_left_y=0.4,
# #     )
# #
# #     frames_5_to_10_box_coordinates = BoundingBoxCoordinates(
# #         height=0.3,
# #         width=0.4,
# #         top_left_x=0.5,
# #         top_left_y=0.6,
# #     )
# #
# #     # LIST ALL SPACES
# #     spaces = label_row.list_spaces()
# #     for space in spaces:
# #         print(f"ID: {space.id}")
# #         print(f"title: {space.title}")
# #         print(f"space type: {space.space_type}")
# #
# #     # ADD OBJECTS FROM SPACE
# #     video_space_1 = label_row.get_space_by_title(title="Video 1", type_=VisionSpace)
# #     # OR could get the space by its layout key
# #     video_space_1 = label_row.get_space_by_layout_key(layout_key="video-left", type_=VisionSpace)
# #
# #     bb_instance = video_space_1.add_object_instance(
# #         obj=box_ontology_item,
# #         coordinates=frame_0_box_coordinates,
# #         frames=0,
# #         # Also could add the other args for set_for_frames (e.g. last_edited_at etc..)
# #     )
# #
# #     # Can continue to use old API for object_instances
# #     bb_instance.set_for_frames(coordinates=frames_5_to_10_box_coordinates, frames=Range(start=5, end=10))
# #
# #     audio_space = label_row.get_space_by_title(title="Audio 1", type_=AudioSpace)
# #     audio_instance = audio_space.add_object_instance(obj=audio_obj_ontology_item, ranges=Range(start=500, end=2000))
# #
# #     # NOTE: Point clouds have no frames, so any object instance is applied to the entire thing
# #     point_cloud_space = label_row.get_space_by_title(title="url-to-point-cloud.pcd", type_=SceneStreamSpace)
#     point_cloud_space.add_object_instance(obj=box_ontology_item, coordinates=frame_0_box_coordinates)
#
#     # REMOVE OBJECTS FROM SPACE
#     video_space_1.remove_object_instance(object_hash=bb_instance.object_hash)
#
#     # UPDATE SPACE
#     video_space_2 = label_row.get_space_by_title(title="Video 2", type_=VisionSpace)
#     video_space_1.move_object_instance_to_space(object_hash=bb_instance.object_hash, target_space_id=video_space_2.id)
#
#     # List object instances in space
#     objects_on_video_space = video_space_1.get_object_instances(
#         filter_ontology_object=box_ontology_item, filter_frames=[0, 1, 2]
#     )
#     objects_on_audio_space = audio_space.get_object_instances(
#         filter_ontology_object=audio_obj_ontology_item, filter_ranges=Range(start=5, end=200)
#     )
#     objects_to_point_cloud_space = point_cloud_space.get_object_instances(
#         filter_ontology_object=segmentation_ontology_item
#     )
#
#     # Object Instances also know which space they are on
#     print(f"BB Object is on space: {bb_instance._space}")