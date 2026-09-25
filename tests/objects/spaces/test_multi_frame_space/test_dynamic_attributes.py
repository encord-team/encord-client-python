import sys
from copy import deepcopy
from dataclasses import asdict
from random import Random
from typing import cast
from unittest.mock import Mock

import pytest

from encord.exceptions import LabelRowError
from encord.objects import AnswerForFrames, LabelRowV2, Object
from encord.objects.attributes import Attribute, ChecklistAttribute, NumericAttribute
from encord.objects.coordinates import PointCoordinate
from encord.objects.frames import Range
from encord.objects.ontology_object_instance import AnswersForFrames
from encord.orm.label_row import LabelRowMetadata
from tests.objects.common import BASE_LABEL_ROW_METADATA
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.scene import SCENE_METADATA, SCENE_NO_LABELS
from tests.objects.data.data_group.two_videos import (
    DATA_GROUP_TWO_VIDEOS_NO_LABELS,
    DATA_GROUP_WITH_TWO_VIDEOS_METADATA,
)
from tests.objects.data.empty_video import labels as empty_video_labels

keypoint_with_dynamic_attributes_ontology_item = all_types_structure.get_child_by_hash("MTY2MTQx", Object)
key_point_dynamic_text_attribute = keypoint_with_dynamic_attributes_ontology_item.get_child_by_hash(
    "OTkxMjU1", type_=Attribute
)


def test_distinct_dynamic_answer_writes_do_not_scale_quadratically():
    def write_call_count(count):
        obj = keypoint_with_dynamic_attributes_ontology_item.create_instance()
        calls = 0

        def count_calls(frame, event, arg):
            nonlocal calls
            if event == "call":
                calls += 1

        previous_profile = sys.getprofile()
        try:
            sys.setprofile(count_calls)
            for frame in range(count):
                obj.set_answer(str(frame), attribute=key_point_dynamic_text_attribute, frames=frame)
            for frame in range(count):
                obj.set_answer(f"edited-{frame}", attribute=key_point_dynamic_text_attribute, frames=frame)
        finally:
            sys.setprofile(previous_profile)
        answers = cast(AnswersForFrames, obj.get_answer(key_point_dynamic_text_attribute))
        assert len(answers) == count
        assert obj.get_answer(key_point_dynamic_text_attribute, filter_frame=count - 1) == [
            AnswerForFrames(answer=f"edited-{count - 1}", ranges=[Range(count - 1, count - 1)])
        ]
        return calls

    # Count Python calls instead of elapsed time so slow CI workers do not affect the assertion.
    small = write_call_count(100)
    large = write_call_count(200)
    assert large < small * 3, (small, large)


def test_explicit_empty_dynamic_answer_frames_still_validate_the_answer():
    obj = keypoint_with_dynamic_attributes_ontology_item.create_instance()
    with pytest.raises(ValueError, match="TextAnswer can only be set to a string"):
        obj.set_answer(1.0, attribute=key_point_dynamic_text_attribute, frames=[])
    assert obj.get_answer(key_point_dynamic_text_attribute) == []


@pytest.mark.parametrize("scene", [False, True])
def test_dense_dynamic_answers_round_trip_and_remain_editable(all_types_ontology, scene):
    count = 200
    if scene:
        metadata = deepcopy(SCENE_METADATA)
        labels = deepcopy(SCENE_NO_LABELS)
    else:
        metadata_dict = asdict(BASE_LABEL_ROW_METADATA)
        metadata_dict["number_of_frames"] = count
        metadata = LabelRowMetadata(**metadata_dict)
        labels = deepcopy(empty_video_labels)
    row = LabelRowV2(metadata, Mock(), all_types_ontology)
    row.from_labels_dict(labels)
    obj = keypoint_with_dynamic_attributes_ontology_item.create_instance()
    obj.set_for_frames(PointCoordinate(0.1, 0.2), frames=Range(0, count - 1))
    row.add_object_instance(obj)
    for frame in range(count):
        obj.set_answer(str(frame), attribute=key_point_dynamic_text_attribute, frames=frame)
    row.from_labels_dict(row.to_encord_dict())
    [obj] = row.get_object_instances()
    answers = cast(AnswersForFrames, obj.get_answer(key_point_dynamic_text_attribute))
    assert len(answers) == count
    obj.set_answer("edited", attribute=key_point_dynamic_text_attribute, frames=Range(10, 19))
    obj.delete_answer(key_point_dynamic_text_attribute, filter_frame=15)
    assert obj.get_answer(key_point_dynamic_text_attribute, filter_frame=15) == []
    assert obj.get_answer(key_point_dynamic_text_attribute, filter_frame=12) == [
        AnswerForFrames(answer="edited", ranges=[Range(10, 14), Range(16, 19)])
    ]
    obj.are_dynamic_answers_valid()
    row.from_labels_dict(row.to_encord_dict())
    restored_answers = cast(
        AnswersForFrames, row.get_object_instances()[0].get_answer(key_point_dynamic_text_attribute)
    )
    expected_answers = cast(AnswersForFrames, obj.get_answer(key_point_dynamic_text_attribute))
    assert sorted(restored_answers, key=lambda a: cast(str, a.answer)) == sorted(
        expected_answers, key=lambda a: cast(str, a.answer)
    )


def test_copy_dynamic_answers_can_be_edited_independently():
    obj = keypoint_with_dynamic_attributes_ontology_item.create_instance()
    obj.set_answer("original", attribute=key_point_dynamic_text_attribute, frames=Range(0, 10))
    obj.set_answer("middle", attribute=key_point_dynamic_text_attribute, frames=Range(4, 6))
    copied = obj.copy()
    copied.set_answer("copy", attribute=key_point_dynamic_text_attribute, frames=Range(2, 8))
    copied.delete_answer(key_point_dynamic_text_attribute, filter_frame=5)
    obj.delete_answer(key_point_dynamic_text_attribute, filter_answer="middle")
    assert obj.get_answer(key_point_dynamic_text_attribute) == [
        AnswerForFrames(answer="original", ranges=[Range(0, 3), Range(7, 10)])
    ]
    assert copied.get_answer(key_point_dynamic_text_attribute) == [
        AnswerForFrames(answer="original", ranges=[Range(0, 1), Range(9, 10)]),
        AnswerForFrames(answer="copy", ranges=[Range(2, 4), Range(6, 8)]),
    ]


@pytest.mark.parametrize("scene", [False, True])
def test_default_dynamic_answer_update_preserves_serialized_answer_order(all_types_ontology, scene):
    metadata = SCENE_METADATA if scene else BASE_LABEL_ROW_METADATA
    labels = SCENE_NO_LABELS if scene else empty_video_labels
    row = LabelRowV2(deepcopy(metadata), Mock(), all_types_ontology)
    row.from_labels_dict(deepcopy(labels))
    obj = keypoint_with_dynamic_attributes_ontology_item.create_instance()
    obj.set_for_frames(PointCoordinate(0.1, 0.2), frames=[0, 1])
    row.add_object_instance(obj)
    checklist = keypoint_with_dynamic_attributes_ontology_item.get_child_by_hash("ODcxMDAy", ChecklistAttribute)
    obj.set_answer("text", attribute=key_point_dynamic_text_attribute, frames=[0, 1])
    obj.set_answer([checklist.options[0]], attribute=checklist, frames=0)
    expected = row.to_encord_dict()

    obj.set_answer("text", attribute=key_point_dynamic_text_attribute)

    assert row.to_encord_dict() == expected


def test_editing_numeric_answers_preserves_other_attributes():
    keypoint = deepcopy(keypoint_with_dynamic_attributes_ontology_item)
    numeric = keypoint.add_attribute(NumericAttribute, "Score", dynamic=True)
    checklist = keypoint.get_child_by_hash("ODcxMDAy", ChecklistAttribute)
    option = checklist.options[0]
    obj = keypoint.create_instance()
    obj.set_answer("text", attribute=key_point_dynamic_text_attribute, frames=Range(0, 9))
    obj.set_answer([option], attribute=checklist, frames=Range(0, 9))
    for frame in range(10):
        obj.set_answer(frame / 10, attribute=numeric, frames=frame)
    obj.set_answer(0.5, attribute=numeric, frames=Range(3, 7))
    obj.delete_answer(numeric, filter_frame=5)
    assert obj.get_answer(numeric, filter_frame=4) == [AnswerForFrames(answer=0.5, ranges=[Range(3, 4), Range(6, 7)])]
    obj.delete_answer(numeric)
    assert obj.get_answer(numeric) == []
    obj.set_answer(1.0, attribute=numeric, frames=Range(0, 9))
    assert obj.get_answer(numeric) == [AnswerForFrames(answer=1.0, ranges=[Range(0, 9)])]
    assert obj.get_answer(key_point_dynamic_text_attribute) == [AnswerForFrames(answer="text", ranges=[Range(0, 9)])]
    assert obj.get_answer(checklist) == [AnswerForFrames(answer=[option], ranges=[Range(0, 9)])]


@pytest.mark.parametrize("seed", range(3))
def test_dynamic_answer_range_edits_match_a_frame_model(seed):
    obj = keypoint_with_dynamic_attributes_ontology_item.create_instance()
    obj.set_for_frames(PointCoordinate(0.1, 0.2), frames=Range(0, 29))
    expected = {}
    rng = Random(seed)
    for _ in range(100):
        if rng.randrange(3):
            ranges = [Range(*sorted([rng.randrange(30), rng.randrange(30)])) for _ in range(2)]
            value = rng.choice(["a", "b", "c"])
            obj.set_answer(value, attribute=key_point_dynamic_text_attribute, frames=ranges)
            for r in ranges:
                expected.update({frame: value for frame in range(r.start, r.end + 1)})
        else:
            frame = rng.choice([None, rng.randrange(30)])
            value = rng.choice([None, "a", "b", "c"])
            obj.delete_answer(key_point_dynamic_text_attribute, filter_frame=frame, filter_answer=value)
            expected = {
                f: v
                for f, v in expected.items()
                if not ((frame is None or f == frame) and (value is None or v == value))
            }
        actual = {}
        answers = cast(AnswersForFrames, obj.get_answer(key_point_dynamic_text_attribute))
        for answer in answers:
            for r in answer.ranges:
                for frame in range(r.start, r.end + 1):
                    assert frame not in actual
                    actual[frame] = answer.answer
        assert actual == expected


@pytest.mark.parametrize("multiple_spaces", [False, True])
def test_default_dynamic_answer_frames_on_video_spaces_round_trip(all_types_ontology, multiple_spaces):
    label_row = LabelRowV2(DATA_GROUP_WITH_TWO_VIDEOS_METADATA, Mock(), all_types_ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space = label_row.get_space(id="video-1-uuid", type_="video")
    obj = keypoint_with_dynamic_attributes_ontology_item.create_instance()
    coordinates = PointCoordinate(x=0.5, y=0.5)
    video_space.put_object_instance(obj, frames=[0, 2], coordinates=coordinates)
    expected_ranges = [Range(0, 0), Range(2, 2)]
    if multiple_spaces:
        other_space = label_row.get_space(id="video-2-uuid", type_="video")
        other_space.put_object_instance(obj, frames=[2, 3], coordinates=coordinates)
        expected_ranges = [Range(0, 0), Range(2, 3)]

    obj.set_answer("old", attribute=key_point_dynamic_text_attribute, frames=2)
    obj.set_answer("visible", attribute=key_point_dynamic_text_attribute)
    expected = [AnswerForFrames(answer="visible", ranges=expected_ranges)]
    assert obj.get_answer(key_point_dynamic_text_attribute) == expected

    assert obj.get_answer(key_point_dynamic_text_attribute, filter_frame=1) == []
    exported = label_row.to_encord_dict()
    assert exported["object_actions"][obj.object_hash]["actions"][0]["range"] == [
        [r.start, r.end] for r in expected_ranges
    ]
    restored = LabelRowV2(DATA_GROUP_WITH_TWO_VIDEOS_METADATA, Mock(), all_types_ontology)
    restored.from_labels_dict(exported)
    restored_obj = restored.get_space(id="video-1-uuid", type_="video").get_object_instances()[0]
    assert restored_obj.get_answer(key_point_dynamic_text_attribute) == expected


def test_add_dynamic_attributes_to_frames_on_object_on_video_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_WITH_TWO_VIDEOS_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")

    new_object_instance = keypoint_with_dynamic_attributes_ontology_item.create_instance()
    point_coordinates = PointCoordinate(x=0.5, y=0.5)
    video_space_1.put_object_instance(
        object_instance=new_object_instance,
        frames=[0, 1, 2],
        coordinates=point_coordinates,
    )

    answer_on_frame_0 = "Frame 0"
    answer_on_frame_1_and_2 = "Frame 1 and 2"

    new_object_instance.set_answer(frames=[0], attribute=key_point_dynamic_text_attribute, answer=answer_on_frame_0)

    # # Act
    video_space_1.set_dynamic_answer(
        object_instance=new_object_instance,
        frames=[0],
        attribute=key_point_dynamic_text_attribute,
        answer=answer_on_frame_0,
    )
    video_space_1.set_dynamic_answer(
        object_instance=new_object_instance,
        frames=[1, 2],
        attribute=key_point_dynamic_text_attribute,
        answer=answer_on_frame_1_and_2,
    )
    #
    # # Assert
    actual_answers = video_space_1.get_dynamic_answer(
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
    label_row = LabelRowV2(DATA_GROUP_WITH_TWO_VIDEOS_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")

    new_object_instance = keypoint_with_dynamic_attributes_ontology_item.create_instance()
    point_coordinates = PointCoordinate(x=0.5, y=0.5)
    video_space_1.put_object_instance(
        object_instance=new_object_instance,
        frames=[0, 1, 2],
        coordinates=point_coordinates,
    )

    answer = "Answers"

    video_space_1.set_dynamic_answer(
        object_instance=new_object_instance, frames=[0, 1, 2], attribute=key_point_dynamic_text_attribute, answer=answer
    )

    # Act
    video_space_1.remove_dynamic_answer(
        object_instance=new_object_instance,
        attribute=key_point_dynamic_text_attribute,
        frame=1,  # Remove from frame 1, should left with frame 1 and 2
    )

    # Assert
    actual_answers = video_space_1.get_dynamic_answer(
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
    label_row = LabelRowV2(DATA_GROUP_WITH_TWO_VIDEOS_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")

    new_object_instance = keypoint_with_dynamic_attributes_ontology_item.create_instance()
    point_coordinates = PointCoordinate(x=0.5, y=0.5)
    video_space_1.put_object_instance(
        object_instance=new_object_instance,
        frames=[0, 1, 2],
        coordinates=point_coordinates,
    )
    answer = "Answers"
    video_space_1.set_dynamic_answer(
        object_instance=new_object_instance, frames=[0, 1, 2], attribute=key_point_dynamic_text_attribute, answer=answer
    )

    # Act
    video_space_1.remove_object_instance(object_hash=new_object_instance.object_hash)

    # Assert
    with pytest.raises(LabelRowError) as e:
        video_space_1.get_dynamic_answer(
            object_instance=new_object_instance,
            frames=[0, 1, 2],
            attribute=key_point_dynamic_text_attribute,
        )
    assert (
        e.value.message
        == "Object does not yet exist on this space. Place the object on this space with `Space.place_object`."
    )


def test_add_dynamic_attributes_to_frames_where_object_does_not_exist_on_video_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_WITH_TWO_VIDEOS_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")

    new_object_instance = keypoint_with_dynamic_attributes_ontology_item.create_instance()
    point_coordinates = PointCoordinate(x=0.5, y=0.5)

    video_space_1.put_object_instance(
        object_instance=new_object_instance,
        frames=[0],
        coordinates=point_coordinates,
    )

    answer_on_frame_1 = "Frame 1"

    # Act
    video_space_1.set_dynamic_answer(
        object_instance=new_object_instance,
        frames=[1],  # Setting answer on frame 1, but object only exists on frame 0
        attribute=key_point_dynamic_text_attribute,
        answer=answer_on_frame_1,
    )

    # Assert
    actual_answers = video_space_1.get_dynamic_answer(
        object_instance=new_object_instance,
        frames=[0, 1],
        attribute=key_point_dynamic_text_attribute,
    )

    assert len(actual_answers) == 0  # No answer is set


def test_add_dynamic_attributes_object_which_does_not_exist_on_video_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_WITH_TWO_VIDEOS_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")

    new_object_instance = keypoint_with_dynamic_attributes_ontology_item.create_instance()

    answer_on_frame_1 = "Frame 1"

    # Act
    with pytest.raises(LabelRowError) as e:
        video_space_1.set_dynamic_answer(
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
