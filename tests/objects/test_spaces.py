from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from deepdiff import DeepDiff

from encord.objects import Classification, LabelRowV2, Object
from encord.objects.coordinates import BoundingBoxCoordinates
from encord.objects.space import VisionSpace
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group import DATA_GROUP_METADATA, EMPTY_DATA_GROUP_LABELS, EXPECTED_DATA_GROUP_WITH_LABELS

segmentation_ontology_item = all_types_structure.get_child_by_hash("segmentationFeatureNodeHash", Object)
box_ontology_item = all_types_structure.get_child_by_hash("MjI2NzEy", Object)
audio_obj_ontology_item = all_types_structure.get_child_by_hash("KVfzNkFy", Object)
text_classification = all_types_structure.get_child_by_hash("jPOcEsbw", Classification)


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
    assert len(objects_on_vision_space) == 0

    # After adding, check that object exists, and has correct properties
    created_by = "new_user"
    created_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
    added_object_instance = vision_space.add_object_instance(
        obj=box_ontology_item,
        frames=[0, 1],
        coordinates=frame_0_box_coordinates,
        created_by=created_by,
        created_at=created_at,
        manual_annotation=False,
    )
    objects_on_vision_space = vision_space.get_object_instances()
    assert len(objects_on_vision_space) == 1

    first_object_instance = objects_on_vision_space[0]
    annotations_on_first_object_instance = first_object_instance.get_annotations()
    assert first_object_instance.object_hash == added_object_instance.object_hash
    assert len(annotations_on_first_object_instance) == 2

    frames_on_annotations = [annotation.frame for annotation in annotations_on_first_object_instance]
    assert frames_on_annotations == [0, 1]
    for annotation in annotations_on_first_object_instance:
        assert annotation.coordinates == frame_0_box_coordinates
        assert annotation.created_by == created_by
        assert annotation.created_at == created_at
        assert annotation.manual_annotation is False

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
    added_object_instance = vision_space.add_object_instance(
        obj=box_ontology_item, frames=[0, 1], coordinates=frame_0_box_coordinates
    )
    objects_on_vision_space = vision_space.get_object_instances()

    # Check properties after adding object
    assert len(objects_on_vision_space) == 1
    assert len(vision_space._frames_to_hashes[0]) == 1
    assert len(vision_space._frames_to_hashes[1]) == 1
    assert added_object_instance.object_hash in vision_space._objects_map

    # Check properties after removing object
    vision_space.remove_object_instance(added_object_instance.object_hash)
    objects_on_vision_space = vision_space.get_object_instances()
    assert len(objects_on_vision_space) == 0
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
    object_on_vision_space_1 = vision_space_1.add_object_instance(
        obj=box_ontology_item, frames=[0, 1], coordinates=frame_0_box_coordinates
    )
    objects_on_vision_space_1 = vision_space_1.get_object_instances()

    # Check properties of vision space 1 before moving object
    assert len(objects_on_vision_space_1) == 1
    assert len(vision_space_1._frames_to_hashes[0]) == 1
    assert len(vision_space_1._frames_to_hashes[1]) == 1
    assert object_on_vision_space_1.object_hash in vision_space_1._objects_map

    # Check properties of vision space 2 before moving object
    vision_space_2 = label_row.get_space_by_id("video-2-uuid", type_=VisionSpace)
    objects_on_vision_space_2 = vision_space_2.get_object_instances()
    assert len(objects_on_vision_space_2) == 0
    assert len(vision_space_2._frames_to_hashes.keys()) == 0
    assert len(vision_space_2._frames_to_hashes.keys()) == 0

    # Move object from space 1 to space 2
    vision_space_2.move_object_instance_from_space(object_on_vision_space_1)

    # Check properties of vision space 1 after moving object
    objects_on_vision_space_1 = vision_space_1.get_object_instances()
    assert len(objects_on_vision_space_1) == 0
    assert len(vision_space_1._frames_to_hashes[0]) == 0
    assert len(vision_space_1._frames_to_hashes[1]) == 0

    # Check properties of vision space 2 after moving object
    objects_on_vision_space_2 = vision_space_2.get_object_instances()
    assert len(objects_on_vision_space_2) == 1
    assert len(vision_space_2._frames_to_hashes[0]) == 1
    assert len(vision_space_2._frames_to_hashes[1]) == 1


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
    assert len(objects_on_vision_space) == 0

    # After adding, check that object exists, and has correct properties
    created_by = "new_user"
    created_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
    added_object_instance = vision_space.add_object_instance(
        obj=box_ontology_item,
        frames=[0, 1],
        coordinates=frame_0_box_coordinates,
        created_by=created_by,
        created_at=created_at,
        manual_annotation=False,
    )
    objects_on_vision_space = vision_space.get_object_instances()
    assert len(objects_on_vision_space) == 1

    first_object_instance = objects_on_vision_space[0]
    annotations_on_first_object_instance = first_object_instance.get_annotations()
    assert first_object_instance.object_hash == added_object_instance.object_hash
    assert len(annotations_on_first_object_instance) == 2

    frames_on_annotations = [annotation.frame for annotation in annotations_on_first_object_instance]
    assert frames_on_annotations == [0, 1]
    for annotation in annotations_on_first_object_instance:
        assert annotation.coordinates == frame_0_box_coordinates
        assert annotation.created_by == created_by
        assert annotation.created_at == created_at
        assert annotation.manual_annotation is False

    # Check that spaces has correct properties
    assert len(vision_space._frames_to_hashes[0]) == 1
    assert len(vision_space._frames_to_hashes[1]) == 1
    assert added_object_instance.object_hash in vision_space._objects_map


def test_vision_space_can_add_classification_instances(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(EMPTY_DATA_GROUP_LABELS)

    vision_space = label_row.get_space_by_id("video-1-uuid", type_=VisionSpace)
    # Check that no objects exist on space
    classifications_on_vision_space = vision_space.get_classification_instances()
    assert len(classifications_on_vision_space) == 0

    # After adding, check that object exists, and has correct properties
    created_by = "new_user"
    created_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
    added_classification_instance = vision_space.add_classification_instance(
        classification=text_classification,
        frames=[0, 1],
        created_by=created_by,
        created_at=created_at,
        manual_annotation=False,
    )
    classifications_on_vision_space = vision_space.get_classification_instances()
    assert len(classifications_on_vision_space) == 1

    first_classification_instance = classifications_on_vision_space[0]
    annotations_on_first_classification_instance = first_classification_instance.get_annotations()
    assert first_classification_instance.classification_hash == added_classification_instance.classification_hash
    assert len(annotations_on_first_classification_instance) == 2

    frames_on_annotations = [annotation.frame for annotation in annotations_on_first_classification_instance]
    assert frames_on_annotations == [0, 1]
    for annotation in annotations_on_first_classification_instance:
        assert annotation.created_by == created_by
        assert annotation.created_at == created_at
        assert annotation.manual_annotation is False

    # Check that spaces has correct properties
    assert len(vision_space._frames_to_hashes[0]) == 1
    assert len(vision_space._frames_to_hashes[1]) == 1
    assert added_classification_instance.classification_hash in vision_space._classifications_map


def test_vision_space_can_remove_classification_instances(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(EMPTY_DATA_GROUP_LABELS)

    vision_space = label_row.get_space_by_id("video-1-uuid", type_=VisionSpace)

    assert vision_space is not None
    added_classification_instance = vision_space.add_classification_instance(
        classification=text_classification, frames=[0, 1]
    )
    classifications_on_vision_space = vision_space.get_classification_instances()

    # Check properties after adding classification
    assert len(classifications_on_vision_space) == 1
    assert len(vision_space._frames_to_hashes[0]) == 1
    assert len(vision_space._frames_to_hashes[1]) == 1
    assert added_classification_instance.classification_hash in vision_space._classifications_map

    # Check properties after removing classification
    vision_space.remove_classification_instance(added_classification_instance.classification_hash)
    classifications_on_vision_space = vision_space.get_classification_instances()
    assert len(classifications_on_vision_space) == 0
    assert len(vision_space._frames_to_hashes[0]) == 0
    assert len(vision_space._frames_to_hashes[1]) == 0


def test_vision_space_move_classification_instances(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(EMPTY_DATA_GROUP_LABELS)

    vision_space_1 = label_row.get_space_by_id("video-1-uuid", type_=VisionSpace)
    classification_on_vision_space_1 = vision_space_1.add_classification_instance(
        classification=text_classification, frames=[0, 1]
    )
    classifications_on_vision_space_1 = vision_space_1.get_classification_instances()

    # Check properties of vision space 1 before moving classification
    assert len(classifications_on_vision_space_1) == 1
    assert len(vision_space_1._frames_to_hashes[0]) == 1
    assert len(vision_space_1._frames_to_hashes[1]) == 1
    assert classification_on_vision_space_1.classification_hash in vision_space_1._classifications_map

    # Check properties of vision space 2 before moving classification
    vision_space_2 = label_row.get_space_by_id("video-2-uuid", type_=VisionSpace)
    classifications_on_vision_space_2 = vision_space_2.get_classification_instances()
    assert len(classifications_on_vision_space_2) == 0
    assert len(vision_space_2._frames_to_hashes.keys()) == 0
    assert len(vision_space_2._frames_to_hashes.keys()) == 0

    # Move classification from space 1 to space 2
    vision_space_2.move_classification_instance_from_space(classification_on_vision_space_1)

    # Check properties of vision space 1 after moving classification
    classifications_on_vision_space_1 = vision_space_1.get_classification_instances()
    assert len(classifications_on_vision_space_1) == 0
    assert len(vision_space_1._frames_to_hashes[0]) == 0
    assert len(vision_space_1._frames_to_hashes[1]) == 0

    # Check properties of vision space 2 after moving classification
    classifications_on_vision_space_2 = vision_space_2.get_classification_instances()
    assert len(classifications_on_vision_space_2) == 1
    assert len(vision_space_2._frames_to_hashes[0]) == 1
    assert len(vision_space_2._frames_to_hashes[1]) == 1


def test_read_and_export_labels(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(EXPECTED_DATA_GROUP_WITH_LABELS)

    vision_space_1 = label_row.get_space_by_id("video-1-uuid", type_=VisionSpace)
    objects_on_vision_space_1 = vision_space_1.get_object_instances()
    assert len(objects_on_vision_space_1) == 2

    box_object_instance = objects_on_vision_space_1[0]
    assert box_object_instance.object_hash == "object1"
    assert box_object_instance.get_annotation_frames() == {0, 1}

    dynamic_point_instance = objects_on_vision_space_1[1]
    assert dynamic_point_instance.object_hash == "dynamicPoint1"
    assert dynamic_point_instance.get_annotation_frames() == {0, 1}

    classifications_on_vision_space_1 = vision_space_1.get_classification_instances()
    classification_instance = classifications_on_vision_space_1[0]
    assert classification_instance.classification_hash == "classification1"
    assert classification_instance.get_annotation_frames() == {0}

    output_dict = label_row.to_encord_dict()

    assert not DeepDiff(
        EXPECTED_DATA_GROUP_WITH_LABELS,
        output_dict,
        exclude_regex_paths=[r".*\['trackHash'\]"],
        ignore_order_func=lambda x: x.path().endswith("['objects']"),
    )
