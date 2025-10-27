from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from deepdiff import DeepDiff

from encord.exceptions import LabelRowError
from encord.objects import Classification, LabelRowV2, Object
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
audio_obj_ontology_item = all_types_structure.get_child_by_hash("KVfzNkFy", Object)
text_classification = all_types_structure.get_child_by_hash("jPOcEsbw", Classification)


@pytest.fixture
def ontology():
    ontology_structure = Mock()
    ontology_structure.get_child_by_hash = all_types_structure.get_child_by_hash
    ontology = Mock(structure=ontology_structure)
    yield ontology


def test_video_space_can_add_object_instances(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)

    frame_0_box_coordinates = BoundingBoxCoordinates(
        height=0.1,
        width=0.2,
        top_left_x=0.3,
        top_left_y=0.4,
    )

    video_space = label_row.get_space_by_id("video-1-uuid", type_=VideoSpace)
    # Check that no objects exist on space
    objects_on_video_space = video_space.get_object_instances()
    assert len(objects_on_video_space) == 0

    # After adding, check that object exists, and has correct properties
    created_by = "new_user"
    created_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
    added_object_instance = video_space.add_object_instance(
        obj=box_ontology_item,
        frames=[0, 1],
        coordinates=frame_0_box_coordinates,
        created_by=created_by,
        created_at=created_at,
        manual_annotation=False,
    )

    objects_on_video_space = video_space.get_object_instances()
    assert len(objects_on_video_space) == 1

    first_object_instance = objects_on_video_space[0]
    annotations_on_first_object_instance = first_object_instance.get_annotations()
    assert first_object_instance.object_hash == added_object_instance.object_hash
    assert len(annotations_on_first_object_instance) == 2

    frames_on_annotations = first_object_instance.get_annotation_frames()
    assert frames_on_annotations == [0, 1]
    for annotation in annotations_on_first_object_instance:
        assert annotation.coordinates == frame_0_box_coordinates
        assert annotation.created_by == created_by
        assert annotation.created_at == created_at
        assert annotation.manual_annotation is False

    # Check that spaces has correct properties
    assert len(video_space._frames_to_hashes[0]) == 1
    assert len(video_space._frames_to_hashes[1]) == 1
    assert added_object_instance.object_hash in video_space._objects_map


def test_video_space_can_remove_object_instances(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)

    frame_0_box_coordinates = BoundingBoxCoordinates(
        height=0.1,
        width=0.2,
        top_left_x=0.3,
        top_left_y=0.4,
    )

    video_space = label_row.get_space_by_id("video-1-uuid", type_=VideoSpace)

    assert video_space is not None
    added_object_instance = video_space.add_object_instance(
        obj=box_ontology_item, frames=[0, 1], coordinates=frame_0_box_coordinates
    )
    objects_on_video_space = video_space.get_object_instances()

    # Check properties after adding object
    assert len(objects_on_video_space) == 1
    assert len(video_space._frames_to_hashes[0]) == 1
    assert len(video_space._frames_to_hashes[1]) == 1
    assert added_object_instance.object_hash in video_space._objects_map

    # Check properties after removing object
    video_space.remove_object_instance(added_object_instance.object_hash)
    objects_on_video_space = video_space.get_object_instances()
    assert len(objects_on_video_space) == 0
    assert len(video_space._frames_to_hashes[0]) == 0
    assert len(video_space._frames_to_hashes[1]) == 0


def test_video_space_move_object_instances(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)

    frame_0_box_coordinates = BoundingBoxCoordinates(
        height=0.1,
        width=0.2,
        top_left_x=0.3,
        top_left_y=0.4,
    )

    video_space_1 = label_row.get_space_by_id("video-1-uuid", type_=VideoSpace)
    object_on_video_space_1 = video_space_1.add_object_instance(
        obj=box_ontology_item, frames=[0, 1], coordinates=frame_0_box_coordinates
    )
    objects_on_video_space_1 = video_space_1.get_object_instances()

    # Check properties of video space 1 before moving object
    assert len(objects_on_video_space_1) == 1
    assert len(video_space_1._frames_to_hashes[0]) == 1
    assert len(video_space_1._frames_to_hashes[1]) == 1
    assert object_on_video_space_1.object_hash in video_space_1._objects_map

    # Check properties of video space 2 before moving object
    video_space_2 = label_row.get_space_by_id("video-2-uuid", type_=VideoSpace)
    objects_on_video_space_2 = video_space_2.get_object_instances()
    assert len(objects_on_video_space_2) == 0
    assert len(video_space_2._frames_to_hashes.keys()) == 0
    assert len(video_space_2._frames_to_hashes.keys()) == 0

    # Move object from space 1 to space 2
    video_space_2.move_object_instance_from_space(object_on_video_space_1)

    # Check properties of video space 1 after moving object
    objects_on_video_space_1 = video_space_1.get_object_instances()
    assert len(objects_on_video_space_1) == 0
    assert len(video_space_1._frames_to_hashes[0]) == 0
    assert len(video_space_1._frames_to_hashes[1]) == 0

    # Check properties of video space 2 after moving object
    objects_on_video_space_2 = video_space_2.get_object_instances()
    assert len(objects_on_video_space_2) == 1
    assert len(video_space_2._frames_to_hashes[0]) == 1
    assert len(video_space_2._frames_to_hashes[1]) == 1


def test_video_space_can_update_annotations_on_object_instance(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)

    frame_0_box_coordinates = BoundingBoxCoordinates(
        height=0.1,
        width=0.2,
        top_left_x=0.3,
        top_left_y=0.4,
    )

    video_space_1 = label_row.get_space_by_id("video-1-uuid", type_=VideoSpace)
    added_object = video_space_1.add_object_instance(
        obj=box_ontology_item, frames=[0, 1], coordinates=frame_0_box_coordinates
    )

    annotation_on_frame_1 = added_object.get_annotation(frame=1)

    # Change annotation values
    annotation_on_frame_1.last_edited_by = "arthur@encord.com"
    annotation_on_frame_1.created_by = "clinton@encord.com"
    annotation_on_frame_1.coordinates = BoundingBoxCoordinates(
        height=0.5,
        width=0.6,
        top_left_x=0.7,
        top_left_y=0.8,
    )

    # Check output dict
    actual_frame_labels = video_space_1._to_space_dict()["labels"]
    EXPECTED_FRAME_LABELS = {
        "0": {
            "objects": [
                {
                    "name": "Box",
                    "color": "#D33115",
                    "shape": "bounding_box",
                    "value": "box",
                    "createdBy": None,
                    "confidence": 1.0,
                    "objectHash": added_object.object_hash,
                    "featureHash": "MjI2NzEy",
                    "manualAnnotation": DEFAULT_MANUAL_ANNOTATION,
                    "boundingBox": {"h": 0.1, "w": 0.2, "x": 0.3, "y": 0.4},
                }
            ],
            "classifications": [],
        },
        "1": {
            "objects": [
                {
                    "name": "Box",
                    "color": "#D33115",
                    "shape": "bounding_box",
                    "value": "box",
                    "createdBy": "clinton@encord.com",
                    "confidence": 1.0,
                    "objectHash": added_object.object_hash,
                    "featureHash": "MjI2NzEy",
                    "manualAnnotation": DEFAULT_MANUAL_ANNOTATION,
                    "lastEditedBy": "arthur@encord.com",
                    "boundingBox": {"h": 0.5, "w": 0.6, "x": 0.7, "y": 0.8},
                }
            ],
            "classifications": [],
        },
    }

    assert not DeepDiff(
        EXPECTED_FRAME_LABELS, actual_frame_labels, exclude_regex_paths=[r".*\['lastEditedAt'\]|.*\['createdAt'\]"]
    )


def test_video_space_can_add_classification_instances(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)

    video_space = label_row.get_space_by_id("video-1-uuid", type_=VideoSpace)
    # Check that no objects exist on space
    classifications_on_video_space = video_space.get_classification_instances()
    assert len(classifications_on_video_space) == 0

    # After adding, check that object exists, and has correct properties
    created_by = "new_user"
    created_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
    added_classification_instance = video_space.add_classification_instance(
        classification=text_classification,
        frames=[0, 1],
        created_by=created_by,
        created_at=created_at,
        manual_annotation=False,
    )
    classifications_on_video_space = video_space.get_classification_instances()
    assert len(classifications_on_video_space) == 1

    first_classification_instance = classifications_on_video_space[0]
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
    assert len(video_space._frames_to_hashes[0]) == 1
    assert len(video_space._frames_to_hashes[1]) == 1
    assert added_classification_instance.classification_hash in video_space._classifications_map


def test_video_space_can_remove_classification_instances(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)

    video_space = label_row.get_space_by_id("video-1-uuid", type_=VideoSpace)

    assert video_space is not None
    added_classification_instance = video_space.add_classification_instance(
        classification=text_classification, frames=[0, 1]
    )
    classifications_on_video_space = video_space.get_classification_instances()

    # Check properties after adding classification
    assert len(classifications_on_video_space) == 1
    assert len(video_space._frames_to_hashes[0]) == 1
    assert len(video_space._frames_to_hashes[1]) == 1
    assert added_classification_instance.classification_hash in video_space._classifications_map

    # Check properties after removing classification
    video_space.remove_classification_instance(added_classification_instance.classification_hash)
    classifications_on_video_space = video_space.get_classification_instances()
    assert len(classifications_on_video_space) == 0
    assert len(video_space._frames_to_hashes[0]) == 0
    assert len(video_space._frames_to_hashes[1]) == 0


def test_video_space_move_classification_instances(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)

    video_space_1 = label_row.get_space_by_id("video-1-uuid", type_=VideoSpace)
    classification_on_video_space_1 = video_space_1.add_classification_instance(
        classification=text_classification, frames=[0, 1]
    )
    classifications_on_video_space_1 = video_space_1.get_classification_instances()

    # Check properties of video space 1 before moving classification
    assert len(classifications_on_video_space_1) == 1
    assert len(video_space_1._frames_to_hashes[0]) == 1
    assert len(video_space_1._frames_to_hashes[1]) == 1
    assert classification_on_video_space_1.classification_hash in video_space_1._classifications_map

    # Check properties of video space 2 before moving classification
    video_space_2 = label_row.get_space_by_id("video-2-uuid", type_=VideoSpace)
    classifications_on_video_space_2 = video_space_2.get_classification_instances()
    assert len(classifications_on_video_space_2) == 0
    assert len(video_space_2._frames_to_hashes.keys()) == 0
    assert len(video_space_2._frames_to_hashes.keys()) == 0

    # Move classification from space 1 to space 2
    video_space_2.move_classification_instance_from_space(classification_on_video_space_1)

    # Check properties of video space 1 after moving classification
    classifications_on_video_space_1 = video_space_1.get_classification_instances()
    assert len(classifications_on_video_space_1) == 0
    assert len(video_space_1._frames_to_hashes[0]) == 0
    assert len(video_space_1._frames_to_hashes[1]) == 0

    # Check properties of video space 2 after moving classification
    classifications_on_video_space_2 = video_space_2.get_classification_instances()
    assert len(classifications_on_video_space_2) == 1
    assert len(video_space_2._frames_to_hashes[0]) == 1
    assert len(video_space_2._frames_to_hashes[1]) == 1


def test_read_and_export_labels(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_WITH_TWO_VIDEOS_LABELS)

    video_space_1 = label_row.get_space_by_id("video-1-uuid", type_=VideoSpace)
    objects_on_video_space_1 = video_space_1.get_object_instances()
    assert len(objects_on_video_space_1) == 2

    box_object_instance = objects_on_video_space_1[0]
    assert box_object_instance.object_hash == "object1"
    assert box_object_instance.get_annotation_frames() == [0, 1]
    assert video_space_1._frames_to_hashes[1] == {"object1", "dynamicPoint1"}

    dynamic_point_instance = objects_on_video_space_1[1]
    assert dynamic_point_instance.object_hash == "dynamicPoint1"
    assert dynamic_point_instance.get_annotation_frames() == [0, 1]

    classifications_on_video_space_1 = video_space_1.get_classification_instances()
    classification_instance = classifications_on_video_space_1[0]
    assert classification_instance.classification_hash == "classification1"
    assert classification_instance.get_annotation_frames() == {0}

    output_dict = label_row.to_encord_dict()

    assert not DeepDiff(
        DATA_GROUP_WITH_TWO_VIDEOS_LABELS,
        output_dict,
        exclude_regex_paths=[r".*\['trackHash'\]"],
        ignore_order_func=lambda x: x.path().endswith("['objects']"),
    )


def test_add_entity_to_video_space(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)

    video_space_1 = label_row.get_space_by_id("video-1-uuid", type_=VideoSpace)
    new_entity = label_row.create_entity(ontology_class=box_ontology_item)
    video_space_1.place_object_entity(entity=new_entity, frames=[1], coordinates=BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0))
    video_space_1.place_object_entity(entity=new_entity, frames=[0, 2, 3], coordinates=BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.5, top_left_y=0.5))

    entities = video_space_1.get_entities()
    annotations = video_space_1.get_annotations()
    assert len(annotations) == 4
    first_annotation = annotations[0]
    assert first_annotation.frame == 0
    assert first_annotation.coordinates == BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.5, top_left_y=0.5)

    assert len(entities) == 1

    video_space_2 = label_row.get_space_by_id("video-2-uuid", type_=VideoSpace)
    video_space_2.place_object_entity(entity=new_entity, frames=[0], coordinates=BoundingBoxCoordinates(height=0.7, width=0.7, top_left_x=0.7, top_left_y=0.7))
    annotations = video_space_2.get_annotations()
    assert len(annotations) == 1

    # Remove entity
    video_space_1.remove_entity(new_entity.entity_hash)
    annotations = video_space_1.get_annotations()
    assert len(annotations) == 0
    with pytest.raises(LabelRowError):
        assert first_annotation.coordinates


def test_read_and_export_video_space_labels(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_WITH_TWO_VIDEOS_LABELS)

    video_space_1 = label_row.get_space_by_id("video-1-uuid", type_=VideoSpace)
    video_space_1_annotations = video_space_1.get_annotations()
    assert len(video_space_1_annotations) == 4

    entities = video_space_1.get_entities()
    assert len(entities) == 2
