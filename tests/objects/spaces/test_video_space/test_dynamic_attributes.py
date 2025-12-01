from unittest.mock import Mock

import pytest

from encord.exceptions import LabelRowError
from encord.objects import LabelRowV2, Object
from encord.objects.attributes import Attribute
from encord.objects.coordinates import PointCoordinate
from encord.objects.frames import Range
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.two_videos import (
    DATA_GROUP_METADATA,
    DATA_GROUP_TWO_VIDEOS_NO_LABELS,
)

keypoint_with_dynamic_attributes_ontology_item = all_types_structure.get_child_by_hash("MTY2MTQx", Object)
key_point_dynamic_text_attribute = keypoint_with_dynamic_attributes_ontology_item.get_child_by_hash(
    "OTkxMjU1", type_=Attribute
)


@pytest.fixture
def ontology():
    ontology_structure = Mock()
    ontology_structure.get_child_by_hash = all_types_structure.get_child_by_hash
    ontology = Mock(structure=ontology_structure)
    yield ontology


def test_add_dynamic_attributes_to_frames_on_object_on_video_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")

    new_object_instance = keypoint_with_dynamic_attributes_ontology_item.create_instance()
    point_coordinates = PointCoordinate(x=0.5, y=0.5)
    video_space_1.place_object(
        object_instance=new_object_instance,
        frames=[0, 1, 2],
        coordinates=point_coordinates,
    )

    answer_on_frame_0 = "Frame 0"
    answer_on_frame_1_and_2 = "Frame 1 and 2"

    # Act
    video_space_1.set_answer_on_frames(
        object_instance=new_object_instance,
        frames=[0],
        attribute=key_point_dynamic_text_attribute,
        answer=answer_on_frame_0,
    )
    video_space_1.set_answer_on_frames(
        object_instance=new_object_instance,
        frames=[1, 2],
        attribute=key_point_dynamic_text_attribute,
        answer=answer_on_frame_1_and_2,
    )

    # Assert
    actual_answers = video_space_1.get_answer_on_frames(
        object_instance=new_object_instance,
        frames=[0, 1, 2],
        attribute=key_point_dynamic_text_attribute,
    )

    assert len(actual_answers) == 2
    first_answer = actual_answers[0]
    second_answer = actual_answers[1]

    assert first_answer.ranges == [Range(start=0, end=0)]
    assert first_answer.answer == answer_on_frame_0

    assert second_answer.ranges == [Range(start=1, end=2)]
    assert second_answer.answer == answer_on_frame_1_and_2


def test_remove_dynamic_attributes_from_frame_on_video_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")

    new_object_instance = keypoint_with_dynamic_attributes_ontology_item.create_instance()
    point_coordinates = PointCoordinate(x=0.5, y=0.5)
    video_space_1.place_object(
        object_instance=new_object_instance,
        frames=[0, 1, 2],
        coordinates=point_coordinates,
    )

    answer = "Answers"

    video_space_1.set_answer_on_frames(
        object_instance=new_object_instance, frames=[0, 1, 2], attribute=key_point_dynamic_text_attribute, answer=answer
    )

    # Act
    video_space_1.remove_answer_from_frame(
        object_instance=new_object_instance,
        attribute=key_point_dynamic_text_attribute,
        frame=1,  # Remove from frame 1, should left with frame 1 and 2
    )

    # Assert
    actual_answers = video_space_1.get_answer_on_frames(
        object_instance=new_object_instance,
        frames=[0, 1, 2],
        attribute=key_point_dynamic_text_attribute,
    )

    assert len(actual_answers) == 1
    first_answer = actual_answers[0]

    assert first_answer.ranges == [Range(start=0, end=0), Range(start=2, end=2)]
    assert first_answer.answer == answer


def test_unplace_object_removes_dynamic_attributes_from_those_frames(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")

    new_object_instance = keypoint_with_dynamic_attributes_ontology_item.create_instance()
    point_coordinates = PointCoordinate(x=0.5, y=0.5)
    video_space_1.place_object(
        object_instance=new_object_instance,
        frames=[0, 1, 2],
        coordinates=point_coordinates,
    )
    answer = "Answers"
    video_space_1.set_answer_on_frames(
        object_instance=new_object_instance, frames=[0, 1, 2], attribute=key_point_dynamic_text_attribute, answer=answer
    )

    # Act
    video_space_1.remove_object_from_frames(object_instance=new_object_instance, frames=[1])

    # Assert
    actual_answers = video_space_1.get_answer_on_frames(
        object_instance=new_object_instance,
        frames=[0, 1, 2],
        attribute=key_point_dynamic_text_attribute,
    )

    assert len(actual_answers) == 1
    first_answer = actual_answers[0]

    assert first_answer.ranges == [Range(start=0, end=0), Range(start=2, end=2)]
    assert first_answer.answer == answer


def test_remove_object_removes_dynamic_attributes_for_that_object(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")

    new_object_instance = keypoint_with_dynamic_attributes_ontology_item.create_instance()
    point_coordinates = PointCoordinate(x=0.5, y=0.5)
    video_space_1.place_object(
        object_instance=new_object_instance,
        frames=[0, 1, 2],
        coordinates=point_coordinates,
    )
    answer = "Answers"
    video_space_1.set_answer_on_frames(
        object_instance=new_object_instance, frames=[0, 1, 2], attribute=key_point_dynamic_text_attribute, answer=answer
    )

    # Act
    video_space_1.remove_object(object_hash=new_object_instance.object_hash)

    # Assert
    with pytest.raises(LabelRowError) as e:
        video_space_1.get_answer_on_frames(
            object_instance=new_object_instance,
            frames=[0, 1, 2],
            attribute=key_point_dynamic_text_attribute,
        )
    assert e.value.message == "This object does not exist on this space."


def test_add_dynamic_attributes_to_frames_where_object_does_not_exist_on_video_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")

    new_object_instance = keypoint_with_dynamic_attributes_ontology_item.create_instance()
    point_coordinates = PointCoordinate(x=0.5, y=0.5)

    video_space_1.place_object(
        object_instance=new_object_instance,
        frames=[0],
        coordinates=point_coordinates,
    )

    answer_on_frame_1 = "Frame 1"

    # Act
    video_space_1.set_answer_on_frames(
        object_instance=new_object_instance,
        frames=[1],  # Setting answer on frame 1, but object only exists on frame 0
        attribute=key_point_dynamic_text_attribute,
        answer=answer_on_frame_1,
    )

    # Assert
    actual_answers = video_space_1.get_answer_on_frames(
        object_instance=new_object_instance,
        frames=[0, 1],
        attribute=key_point_dynamic_text_attribute,
    )

    assert len(actual_answers) == 0  # No answer is set


def test_add_dynamic_attributes_object_which_does_not_exist_on_video_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")

    new_object_instance = keypoint_with_dynamic_attributes_ontology_item.create_instance()

    answer_on_frame_1 = "Frame 1"

    # Act
    with pytest.raises(LabelRowError) as e:
        video_space_1.set_answer_on_frames(
            object_instance=new_object_instance,  # Object does not yet exist on this space
            frames=[0],
            attribute=key_point_dynamic_text_attribute,
            answer=answer_on_frame_1,
        )

    # Assert
    assert (
        e.value.message
        == "Object does not yet exist on this space. Place the object on this space with `Space.place_object`."
    )
