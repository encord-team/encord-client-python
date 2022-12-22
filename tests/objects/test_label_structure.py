from dataclasses import dataclass
from typing import List, Union

import pytest

from encord.objects.common import Option
from encord.objects.label_structure import (
    BoundingBoxCoordinates,
    ChecklistAnswer,
    LabelClassification,
    LabelObject,
    LabelRow,
    LabelRowReadOnlyData,
    ObjectFrameInstanceInfo,
    PointCoordinate,
    PolygonCoordinates,
    RadioAnswer,
    TextAnswer,
    get_item_by_hash,
)
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.empty_image_group import empty_image_group_labels

box_ontology_item = get_item_by_hash("MjI2NzEy", all_types_structure)
polygon_ontology_item = get_item_by_hash("ODkxMzAx", all_types_structure)
polyline_ontology_item = get_item_by_hash("OTcxMzIy", all_types_structure)

nested_box_ontology_item = get_item_by_hash("MTA2MjAx", all_types_structure)
text_attribute_1 = get_item_by_hash("OTkxMjU1", all_types_structure)
checklist_attribute_1 = get_item_by_hash("ODcxMDAy", all_types_structure)
checklist_attribute_1_option_1 = get_item_by_hash("MTE5MjQ3", all_types_structure)
checklist_attribute_1_option_2 = get_item_by_hash("Nzg3MDE3", all_types_structure)

deeply_nested_polygon_item = get_item_by_hash("MTM1MTQy", all_types_structure)
radio_attribute_level_1 = get_item_by_hash("MTExMjI3", all_types_structure)
radio_nested_option_1 = get_item_by_hash("MTExNDQ5", all_types_structure)
radio_nested_option_2 = get_item_by_hash("MTcxMjAy", all_types_structure)

radio_attribute_level_2 = get_item_by_hash("NDYyMjQx", all_types_structure)
radio_attribute_2_option_1 = get_item_by_hash("MTY0MzU2", all_types_structure)
radio_attribute_2_option_2 = get_item_by_hash("MTI4MjQy", all_types_structure)

keypoint_dynamic = get_item_by_hash("MTY2MTQx", all_types_structure)
dynamic_text = get_item_by_hash("OTkxMjU1", all_types_structure)
dynamic_checklist = get_item_by_hash("ODcxMDAy", all_types_structure)
dynamic_checklist_option_1 = get_item_by_hash("MTE5MjQ3", all_types_structure)
dynamic_checklist_option_2 = get_item_by_hash("Nzg3MDE3", all_types_structure)
dynamic_radio = get_item_by_hash("MTExM9I3", all_types_structure)
dynamic_radio_option_1 = get_item_by_hash("MT9xNDQ5", all_types_structure)  # This is dynamic and deeply nested.
dynamic_radio_option_2 = get_item_by_hash("9TcxMjAy", all_types_structure)  # This is dynamic and deeply nested.

text_classification = get_item_by_hash("jPOcEsbw", all_types_structure)
radio_classification = get_item_by_hash("NzIxNTU1", all_types_structure)
radio_classification_option_1 = get_item_by_hash("MTcwMjM5", all_types_structure)
radio_classification_option_2 = get_item_by_hash("MjUzMTg1", all_types_structure)
radio_classification_option_2_text = get_item_by_hash("MTg0MjIw", all_types_structure)
checklist_classification = get_item_by_hash("3DuQbFxo", all_types_structure)
checklist_classification_option_1 = get_item_by_hash("fvLjF0qZ", all_types_structure)
checklist_classification_option_2 = get_item_by_hash("a4r7nK9i", all_types_structure)

BOX_COORDINATES = BoundingBoxCoordinates(
    height=0.1,
    width=0.2,
    top_left_x=0.3,
    top_left_y=0.4,
)

POLYGON_COORDINATES = PolygonCoordinates(
    values=[
        PointCoordinate(x=0.2, y=0.1),
        PointCoordinate(x=0.3, y=0.2),
        PointCoordinate(x=0.5, y=0.3),
        PointCoordinate(x=0.6, y=0.5),
    ]
)

KEYPOINT_COORDINATES = PointCoordinate(x=0.2, y=0.1)


# =======================================================
# =========== demonstrative tests below here ============
# =======================================================


@pytest.mark.skip("The functionality is not fully implemented")
def test_upload_simple_data():
    project = "code that generates a project ..."
    label_hash = "1234"

    label_row = project.get_label_row_class(label_hash)  # can either take label_hash or data_hash

    # Now create an object and add it to the label row
    label_object = LabelObject(box_ontology_item)
    coordinates = BoundingBoxCoordinates(
        height=0.1,
        width=0.2,
        top_left_x=0.3,
        top_left_y=0.4,
    )
    label_object.set_coordinates(coordinates=coordinates, frames={1})

    label_row.add_object(label_object)

    # Create a classification and add it to the label row
    label_classification = LabelClassification(text_classification)
    answer = label_classification.get_static_answer()
    answer.set("Text answer to the classification attribute")

    label_classification.add_to_frames([2, 3])

    label_row.add_classification(label_classification)

    label_row.save()  # The data will be uploaded to our BE.


# =======================================================
# =========== demonstrative tests above here ============
# =======================================================


def test_create_label_object_one_coordinate():
    label_object = LabelObject(box_ontology_item)

    coordinates = BoundingBoxCoordinates(
        height=0.1,
        width=0.2,
        top_left_x=0.3,
        top_left_y=0.4,
    )

    label_object.set_coordinates(coordinates=coordinates, frames={1})
    assert label_object.is_valid()


def test_create_a_label_row_from_empty_image_group_label_row_dict():
    label_row = LabelRow(empty_image_group_labels, all_types_structure)

    assert label_row.get_classifications() == []
    assert label_row.get_objects() == []
    read_only_data = label_row.label_row_read_only_data
    assert isinstance(read_only_data, LabelRowReadOnlyData)
    # TODO: do more assertions


def test_add_label_object_to_label_row():
    label_row = LabelRow(empty_image_group_labels, all_types_structure)
    label_object = LabelObject(box_ontology_item)

    coordinates = BoundingBoxCoordinates(
        height=0.1,
        width=0.2,
        top_left_x=0.3,
        top_left_y=0.4,
    )

    label_object.set_coordinates(coordinates=coordinates, frames={1})
    label_row.add_object(label_object)
    assert label_row.get_objects()[0].object_hash == label_object.object_hash


def test_add_remove_access_label_objects_in_label_row():
    label_row = LabelRow(empty_image_group_labels, all_types_structure)

    label_object_1 = LabelObject(box_ontology_item)
    label_object_2 = LabelObject(box_ontology_item)

    coordinates_1 = BoundingBoxCoordinates(
        height=0.1,
        width=0.2,
        top_left_x=0.3,
        top_left_y=0.4,
    )
    coordinates_2 = BoundingBoxCoordinates(
        height=0.2,
        width=0.1,
        top_left_x=0.5,
        top_left_y=0.4,
    )

    label_object_1.set_coordinates(coordinates=coordinates_1, frames={1})
    label_object_2.set_coordinates(coordinates=coordinates_2, frames={2, 3})

    label_row.add_object(label_object_1)
    label_row.add_object(label_object_2)

    objects = label_row.get_objects()
    assert objects[0].object_hash == label_object_1.object_hash
    assert objects[1].object_hash == label_object_2.object_hash
    # The FE may sometimes rely on the order of these.

    label_row.remove_object(label_object_1)
    objects = label_row.get_objects()
    assert len(objects) == 1
    assert objects[0].object_hash == label_object_2.object_hash


def discussion_with_eloy():
    x = {
        "label_1": {
            1: BOX_COORDINATES,
            2: BOX_COORDINATES,
            3: BOX_COORDINATES,
            4: BOX_COORDINATES,
        },
        "label_2": {
            1: BOX_COORDINATES,
            2: BOX_COORDINATES,
            3: BOX_COORDINATES,
            4: BOX_COORDINATES,
        },
    }
    y = {
        "frame_1": {
            "label_1": BOX_COORDINATES,
            "label_2": BOX_COORDINATES,
        },
        "frame_2": {
            "label_1": BOX_COORDINATES,
            "label_2": BOX_COORDINATES,
        },
        "frame_3": {
            "label_1": BOX_COORDINATES,
            "label_2": BOX_COORDINATES,
        },
    }

    label_row = LabelRow(empty_image_group_labels, all_types_structure)

    # DENIS: think about such a read layer, to be able to iterate over each
    # individual frame and then get all the objects and read them.
    frame_unit: FrameUnit = label_row.get_frame(1)

    label_object_1 = LabelObject(BOX_COORDINATES)
    label_object_2 = LabelObject(BOX_COORDINATES)

    # ======
    objects_for_frame: List[LabelObject] = LabelRow.objects_by_frame(1)

    x = LabelRow.label_row_read_only_data

    # ===
    frame_unit: FrameUnit = LabelRow.frame_unit(1)
    objects_for_frame: List[LabelObject] = frame_unit.get_all_objects()

    # ======

    frame_unit.add_object(
        coordinates=BOX_COORDINATES,
        object_=label_object_1,
    )
    frame_unit.add_object(
        coordinates=BOX_COORDINATES,
        object_=label_object_2,
    )

    # ########## #
    label_row = LabelRow(empty_image_group_labels, all_types_structure)
    label_object_1 = BOX_COORDINATES.get_object(label_row)
    label_object_2 = BOX_COORDINATES.get_object(label_row)

    label_object_1.set_coordinates(coordinates=BOX_COORDINATES, frames={1})
    label_object_2.set_coordinates(coordinates=BOX_COORDINATES, frames={2})


def test_filter_for_objects():
    label_row = LabelRow(empty_image_group_labels, all_types_structure)
    label_box = LabelObject(box_ontology_item)
    label_polygon = LabelObject(polygon_ontology_item)

    box_coordinates = BoundingBoxCoordinates(
        height=0.1,
        width=0.2,
        top_left_x=0.3,
        top_left_y=0.4,
    )
    polygon_coordinates = PolygonCoordinates(
        values=[
            PointCoordinate(x=0.2, y=0.1),
            PointCoordinate(x=0.3, y=0.2),
            PointCoordinate(x=0.5, y=0.3),
            PointCoordinate(x=0.6, y=0.5),
        ]
    )

    label_box.set_coordinates(box_coordinates, {1, 2})
    label_polygon.set_coordinates(polygon_coordinates, {2, 3})

    label_row.add_object(label_box)
    label_row.add_object(label_polygon)

    objects = label_row.get_objects()
    assert len(objects) == 2

    objects = label_row.get_objects(ontology_object=polygon_ontology_item)
    assert len(objects) == 1
    assert objects[0].object_hash == label_polygon.object_hash

    objects = label_row.get_objects(ontology_object=box_ontology_item)
    assert len(objects) == 1
    assert objects[0].object_hash == label_box.object_hash

    objects = label_row.get_objects(ontology_object=polyline_ontology_item)
    assert len(objects) == 0


def test_add_wrong_coordinates():
    label_box = LabelObject(box_ontology_item)
    with pytest.raises(ValueError):
        label_box.set_coordinates(POLYGON_COORDINATES, frames={1})


def test_get_label_objects_by_frames():
    label_row = LabelRow(empty_image_group_labels, all_types_structure)
    label_box = LabelObject(box_ontology_item)
    label_polygon = LabelObject(polygon_ontology_item)

    label_box.set_coordinates(BOX_COORDINATES, {1, 2})
    label_polygon.set_coordinates(POLYGON_COORDINATES, {2, 3})

    label_row.add_object(label_box)
    label_row.add_object(label_polygon)

    objects = label_row.get_objects_by_frame({2})
    assert len(objects) == 2

    objects = label_row.get_objects_by_frame({4})
    assert len(objects) == 0

    objects = list(label_row.get_objects_by_frame({1}))
    assert len(objects) == 1
    assert objects[0].object_hash == label_box.object_hash

    objects = list(label_row.get_objects_by_frame({3}))
    assert len(objects) == 1
    assert objects[0].object_hash == label_polygon.object_hash

    label_box.set_coordinates(BOX_COORDINATES, {3})
    objects = list(label_row.get_objects_by_frame({3}))
    assert len(objects) == 2

    label_row.remove_object(label_box)
    objects = list(label_row.get_objects_by_frame({3}))
    assert len(objects) == 1
    assert objects[0].object_hash == label_polygon.object_hash


def test_adding_label_object_to_multiple_frames_fails():
    label_row_1 = LabelRow(empty_image_group_labels)
    label_row_2 = LabelRow(empty_image_group_labels)
    label_box = LabelObject(box_ontology_item)

    label_box.set_coordinates(BOX_COORDINATES, {1})

    label_row_1.add_object(label_box)
    with pytest.raises(RuntimeError):
        label_row_2.add_object(label_box)

    label_row_1.remove_object(label_box)
    label_row_2.add_object(label_box)

    with pytest.raises(RuntimeError):
        label_row_1.add_object(label_box)

    label_box_copy = label_box.copy()
    label_row_1.add_object(label_box_copy)
    assert label_box.object_hash != label_box_copy.object_hash


def test_update_remove_label_object_coordinates():
    label_box = LabelObject(box_ontology_item)

    # Add initial coordinates
    label_box.set_coordinates(BOX_COORDINATES, {1})
    frames = label_box.frames()
    instance_data = label_box.get_instance_data([1])
    assert sorted(frames) == [1]
    assert instance_data[0].coordinates == BOX_COORDINATES
    assert instance_data[0].object_frame_instance_info == ObjectFrameInstanceInfo()

    box_coordinates_2 = BoundingBoxCoordinates(
        height=0.1,
        width=0.3,
        top_left_x=0.4,
        top_left_y=0.5,
    )

    # Add new coordinates
    object_frame_instance_info_2 = ObjectFrameInstanceInfo(confidence=0.5, manual_annotation=False)
    label_box.set_coordinates(box_coordinates_2, [2, 3, 4], object_frame_instance_info=object_frame_instance_info_2)
    frames = label_box.frames()
    instance_data = label_box.get_instance_data(frames)
    assert sorted(frames) == [1, 2, 3, 4]
    assert instance_data[0].coordinates == BOX_COORDINATES
    assert instance_data[0].object_frame_instance_info == ObjectFrameInstanceInfo()
    assert instance_data[1].coordinates == box_coordinates_2
    assert instance_data[1].object_frame_instance_info == object_frame_instance_info_2
    assert instance_data[1] == instance_data[2]
    assert instance_data[2] == instance_data[3]

    # Remove coordinates
    label_box.remove_from_frames([2, 3])
    frames = label_box.frames()
    instance_data = label_box.get_instance_data(frames)
    assert sorted(frames) == [1, 4]
    assert instance_data[0].coordinates == BOX_COORDINATES
    assert instance_data[0].object_frame_instance_info == ObjectFrameInstanceInfo()
    assert instance_data[1].coordinates == box_coordinates_2
    assert instance_data[1].object_frame_instance_info == object_frame_instance_info_2

    # Reset coordinates
    box_coordinates_3 = BoundingBoxCoordinates(
        height=0.1,
        width=0.3,
        top_left_x=0.6,
        top_left_y=0.5,
    )
    object_frame_instance_info_3 = ObjectFrameInstanceInfo(confidence=0.7, manual_annotation=False)

    label_box.set_coordinates(box_coordinates_3, [4, 5], object_frame_instance_info=object_frame_instance_info_3)
    frames = label_box.frames()
    instance_data = label_box.get_instance_data(frames)
    assert sorted(frames) == [1, 4, 5]
    assert instance_data[0].coordinates == BOX_COORDINATES
    assert instance_data[0].object_frame_instance_info == ObjectFrameInstanceInfo()
    assert instance_data[1].coordinates == box_coordinates_3
    assert instance_data[1].object_frame_instance_info == object_frame_instance_info_3
    assert instance_data[1] == instance_data[2]


def test_removing_coordinates_from_object_removes_it_from_parent():
    label_row = LabelRow(empty_image_group_labels, all_types_structure)
    label_box = LabelObject(box_ontology_item)
    label_box.set_coordinates(BOX_COORDINATES, [1, 2, 3])

    label_row.add_object(label_box)

    objects = label_row.get_objects_by_frame([1, 2, 3])
    assert len(objects) == 1
    objects = label_row.get_objects_by_frame([3])
    assert len(objects) == 1

    label_box.remove_from_frames([3])

    objects = label_row.get_objects_by_frame([1, 2, 3])
    assert len(objects) == 1
    objects = label_row.get_objects_by_frame([3])
    assert len(objects) == 0


def test_getting_static_answers_from_label_object():
    label_box = LabelObject(nested_box_ontology_item)

    """
    DENIS: probably I want some flow where I can get all the empty answers from the label, and then set them.
    I can also get a specific answer by ontology object and set it. So essentially I'd like to initiate all the answers
    already, and then be able to add them. 
    What about having multiple label_boxes and setting the same answers? Can do some sort of copy_all_answers for example,
    but really it only saves an additional for loop. or copy_answers_for_ontology_objects. 
    
    Maybe I want a context manager something like
    with label_box.modify_answers() as answers:
        for answer in answers:
            ...
        # Throw in exit handler if the answers list was changed.
        
    Can also get a read only view which copies the answers out?
    Or I can make the collection itself something more intelligent that protects itself from people deleting stuff.
    
    Or I can just never return the whole reference to the internal list, but always only  specific answers or a new list
    of references! 
    """

    static_answers = label_box.get_all_static_answers()
    assert len(static_answers) == 2

    expected_ontology_hashes = {checklist_attribute_1.feature_node_hash, text_attribute_1.feature_node_hash}
    actual_ontology_hashes = {
        static_answers[0].ontology_attribute.feature_node_hash,
        static_answers[1].ontology_attribute.feature_node_hash,
    }
    assert expected_ontology_hashes == actual_ontology_hashes
    assert not static_answers[0].is_answered()
    assert not static_answers[1].is_answered()


def test_setting_static_text_answers():
    label_object_1 = LabelObject(nested_box_ontology_item)
    label_object_2 = LabelObject(nested_box_ontology_item)

    text_answer: TextAnswer = label_object_1.get_static_answer(text_attribute_1)
    assert not text_answer.is_answered()
    assert text_answer.get_value() is None
    # DENIS: `value.get()` `value.set()`

    text_answer.set("Zeus")
    assert text_answer.is_answered()
    assert text_answer.get_value() == "Zeus"

    refetched_text_answer: TextAnswer = label_object_1.get_static_answer(text_attribute_1)
    assert refetched_text_answer.is_answered()
    assert refetched_text_answer.get_value() == "Zeus"

    other_text_answer = label_object_2.get_static_answer(text_attribute_1)
    assert not other_text_answer.is_answered()
    assert other_text_answer.get_value() is None

    other_text_answer.copy_from(text_answer)
    assert refetched_text_answer.is_answered()
    assert refetched_text_answer.get_value() == "Zeus"


def test_setting_static_checklist_answers():
    label_object_1 = LabelObject(nested_box_ontology_item)
    label_object_2 = LabelObject(nested_box_ontology_item)

    checklist_answer: ChecklistAnswer = label_object_1.get_static_answer(checklist_attribute_1)
    assert not checklist_answer.is_answered()
    assert not checklist_answer.get_value(checklist_attribute_1_option_1)
    assert not checklist_answer.get_value(checklist_attribute_1_option_2)

    checklist_answer.check_options([checklist_attribute_1_option_1, checklist_attribute_1_option_2])
    assert checklist_answer.is_answered()
    assert checklist_answer.get_value(checklist_attribute_1_option_1)
    assert checklist_answer.get_value(checklist_attribute_1_option_2)

    checklist_answer.uncheck_options([checklist_attribute_1_option_1])
    assert checklist_answer.is_answered()
    assert not checklist_answer.get_value(checklist_attribute_1_option_1)
    assert checklist_answer.get_value(checklist_attribute_1_option_2)

    refetched_checklist_answer: ChecklistAnswer = label_object_1.get_static_answer(checklist_attribute_1)
    assert refetched_checklist_answer.is_answered()
    assert not refetched_checklist_answer.get_value(checklist_attribute_1_option_1)
    assert refetched_checklist_answer.get_value(checklist_attribute_1_option_2)

    other_checklist_answer: ChecklistAnswer = label_object_2.get_static_answer(checklist_attribute_1)
    assert not other_checklist_answer.is_answered()
    assert not other_checklist_answer.get_value(checklist_attribute_1_option_1)
    assert not other_checklist_answer.get_value(checklist_attribute_1_option_2)

    other_checklist_answer.copy_from(checklist_answer)
    assert other_checklist_answer.is_answered()
    assert not other_checklist_answer.get_value(checklist_attribute_1_option_1)
    assert other_checklist_answer.get_value(checklist_attribute_1_option_2)


def test_setting_static_radio_answers():
    label_object_1 = LabelObject(deeply_nested_polygon_item)
    label_object_2 = LabelObject(deeply_nested_polygon_item)

    radio_answer_1: RadioAnswer = label_object_1.get_static_answer(radio_attribute_level_1)
    radio_answer_2: RadioAnswer = label_object_1.get_static_answer(radio_attribute_level_2)
    # DENIS: This answer only makes sense if the top level option was actually selected!!
    # DENIS: need to think about an interface where this is cleaner.
    # Maybe the get_static_answer only return from top level, and that answer object itself returns the next
    # selectable options and nested stuff.

    assert not radio_answer_1.is_answered()
    assert not radio_answer_2.is_answered()
    assert radio_answer_1.get_value() is None
    assert radio_answer_2.get_value() is None

    radio_answer_1.set(radio_nested_option_1)
    with pytest.raises(ValueError):
        radio_answer_2.set(radio_nested_option_1)
    assert radio_answer_1.is_answered()
    assert not radio_answer_2.is_answered()
    assert radio_answer_1.get_value().feature_node_hash == radio_nested_option_1.feature_node_hash
    assert radio_answer_2.get_value() is None

    radio_answer_2.set(radio_attribute_2_option_1)
    assert radio_answer_2.is_answered()
    assert radio_answer_2.get_value().feature_node_hash == radio_attribute_2_option_1.feature_node_hash

    refetched_radio_answer: RadioAnswer = label_object_1.get_static_answer(radio_attribute_level_1)
    assert refetched_radio_answer.is_answered()
    assert refetched_radio_answer.get_value().feature_node_hash == radio_nested_option_1.feature_node_hash

    other_radio_answer: RadioAnswer = label_object_2.get_static_answer(radio_attribute_level_1)
    assert not other_radio_answer.is_answered()
    assert other_radio_answer.get_value() is None

    other_radio_answer.copy_from(radio_answer_1)
    assert other_radio_answer.is_answered()
    assert other_radio_answer.get_value().feature_node_hash == radio_nested_option_1.feature_node_hash
    x = {other_radio_answer: 5}


@dataclass
class Range:
    start: int
    end: int


@dataclass
class AnswerForFrames:
    answer: Union[str, List[Option]]
    range: List[Range]  # either [1, 3, 4, 5] or [[1], [3,5]]


# def dynamic_vs_static_answer():
# DENIS: implement these simplifications!
#     answer: Answer = ...
#     answer.in_frames()  # for static answers, this equals the entire range.
#
#     object_instance = LabelObject(box_ontology_item)
#     object_instance.set_coordinates(BOX_COORDINATES, frames=[0, 1, 2, 3])
#     dynamic_answer: TextAnswer = object_instance.get_static_answer(text_attribute_1)
#     dynamic_answer.set("Zeus", frames=[0, 1])  # frames empty => defaults to all
#     object_instance.get_static_answer(text_attribute_1).set("Zeus", frames=[0, 1])  # frames empty => defaults to all
#     # if frames is specified for static answer, throw error
#
#     dynamic_answer.get(frames=[0, 1])  # returns "Zeus"
#     # DENIS: this way I cannot use a `get_all_answers` thingie, I'll not get a set of answers
#     object_instance.set_answer(text_attribute_1, "Zeus", frames=None)
#     object_instance.set_answer(text_attribute_1, "Zeus", frames=Range(0, 1))
#     object_instance.set_answer(text_attribute_1, "Zeus", frames=List[Range(0, 1), Range(3, 5)])
#     object_instance.set_answer(text_attribute_1, "Zeus", frames=Range(0, None))
#     # ^ means from 0 to end of video, even if the object instance comes to new frames. => becomes tricky.
#     object_instance.set_ansser(text_attribute_1, "Poseidon", frames=Range(2, 3))
#     answers = object_instance.get_answer(text_attribute_1)
#     assert answers[0] == AnswerForFrames("Zeus", [Range(0, 1)])
#     assert answers[1] == AnswerForFrames("Poseidon", [Range(2, 3)])
#
#     object_instance.delete_answer(text_attribute_1, frames=Range(0, 1))  # Unsets values to default (i.e. unanswered)
#
#     object_instance.set_answer(text_attribute_1, "Poseidon", frames=[2, 3])
#     object_instance.set_answer(checklist_attribute_1, {checklist_attribute_1}, frames=[0, 1])
#     # DENIS: maybe I don't need the answer object at all, and just have the object instance handle the answer.
#     # object_instance.check_option(checklist_attribute_1, checklist_attribute_1, frames=[0,1])
#
#     answers: List[AnswerForFrames] = object_instance.get_answer(text_attribute_1, frames=[1, 2], filter_value=None)
#     assert object_instance.is_answer_dynamic(text_attribute_1)  # true
#
#     object_instance.set_answer(radio_attribute_level_2, {radio_attribute_2_option_1})
#     # ^ throws if the radio level 1 is not selected.
#
#     # typing:
#     object_instance.set_text_answer(text_attribute_1, "Zeus", frames=[0, 1])
#     object_instance.get_text_answer(text_attribute_1)
#
#     # iterating over frames
#     for frame in object_instance.frames():
#         assert isinstance(frame, int)
#         assert object_instance.set_answer(text_attribute_1, "Zeus", frames=frame)
#         assert object_instance.get_answer(text_attribute_1, frames=[frame]) == "Zeus"
#


def test_adding_dynamic_text_answers():
    label_object = LabelObject(keypoint_dynamic)
    label_object.set_coordinates(KEYPOINT_COORDINATES, frames=[1, 2, 3])

    dynamic_answer = label_object.get_dynamic_answer(frame=1, attribute=dynamic_text)
    assert dynamic_answer.frame == 1
    dynamic_answer.set("Hermes")
    dynamic_answer.copy_to_frames(frames=[2])
    dynamic_answer.propagate_to_last_frame()  # DENIS: implement this?

    assert dynamic_answer.get_value() == "Hermes"
    assert dynamic_answer.in_frames() == {1, 2}

    dynamic_answer_2 = label_object.get_dynamic_answer(frame=3, attribute=dynamic_text)
    dynamic_answer_2.set("Aphrodite")
    dynamic_answer.copy_to_frames(frames=[1])

    assert dynamic_answer.get_value() == "Hermes"
    assert dynamic_answer_2.get_value() == "Aphrodite"

    dynamic_answer_2.copy_to_frames(frames=[1])
    assert dynamic_answer_2.get_value() == "Aphrodite"
    assert dynamic_answer.get_value() == "Aphrodite"
    assert dynamic_answer.in_frames() == dynamic_answer_2.in_frames()

    with pytest.raises(RuntimeError):
        dynamic_answer_2.copy_to_frames([100])
    """
    Essentially I need some sort of map from frame to real answers. Where these dynamic answers, are just a view
    of the frame to the real answers. 
    Additionally, to get the `in_ranges()` thing right, I might need to define a map from the same answers to
    the frames. However, that means I need to define some sort of comparison operator of a given value
    to another given value, even for checklists.
    views:
        * DONE get dynamic answer for specific frame and attribute
        * get all dynamic answers for specific frame
        * DONE get all other frames for which this dynamic answer is set
        * get all dynamic answers that are unset (either by frame or attribute) (in future)
    """
    # DENIS: up I want to have all the views of the Dynamic data and implement the DynamicChecklistAnswer,
    #  and DynamicRadioAnswer


def test_adding_dynamic_checklist_answers():
    label_object = LabelObject(keypoint_dynamic)
    label_object.set_coordinates(KEYPOINT_COORDINATES, frames=[1, 2, 3])

    dynamic_answer = label_object.get_dynamic_answer(frame=1, attribute=dynamic_checklist)
    assert dynamic_answer.frame == 1
    assert not dynamic_answer.is_answered_for_current_frame()
    assert not dynamic_answer.get_value(dynamic_checklist_option_1)
    assert not dynamic_answer.get_value(dynamic_checklist_option_2)

    dynamic_answer.check_options([dynamic_checklist_option_1])
    assert dynamic_answer.get_value(dynamic_checklist_option_1)
    assert not dynamic_answer.get_value(dynamic_checklist_option_2)

    dynamic_answer.copy_to_frames([1, 2])
    assert dynamic_answer.in_frames() == {1, 2}

    dynamic_answer_2 = label_object.get_dynamic_answer(frame=3, attribute=dynamic_checklist)
    dynamic_answer_2.check_options([dynamic_checklist_option_1, dynamic_checklist_option_2])
    dynamic_answer_2.copy_to_frames(frames=[1])

    assert dynamic_answer.get_value(dynamic_checklist_option_1)
    assert dynamic_answer.get_value(dynamic_checklist_option_1)
    assert dynamic_answer_2.get_value(dynamic_checklist_option_1)
    assert dynamic_answer_2.get_value(dynamic_checklist_option_2)
    assert dynamic_answer.in_frames() == {1, 3}
    assert dynamic_answer_2.in_frames() == {1, 3}

    # Frame 2 is still answered from before and unchanged.
    dynamic_answer_3 = label_object.get_dynamic_answer(frame=2, attribute=dynamic_checklist)
    assert dynamic_answer_3.is_answered_for_current_frame()
    assert dynamic_answer_3.get_value(dynamic_checklist_option_1)
    assert not dynamic_answer_3.get_value(dynamic_checklist_option_2)

    with pytest.raises(RuntimeError):
        dynamic_answer_2.copy_to_frames([100])


def test_adding_radio_checklist_answers():
    """DENIS: think about what to do with non-dynamic nested stuff. What does the UI do?"""
    label_object = LabelObject(keypoint_dynamic)
    label_object.set_coordinates(KEYPOINT_COORDINATES, frames=[1, 2, 3])

    dynamic_answer = label_object.get_dynamic_answer(frame=1, attribute=dynamic_radio)
    assert dynamic_answer.frame == 1
    dynamic_answer.set(dynamic_radio_option_1)
    dynamic_answer.copy_to_frames(frames=[2])

    assert dynamic_answer.get_value() == dynamic_radio_option_1
    # DENIS: do I need to have equality comparison of dynamic radios, if they are not the same instance...
    assert dynamic_answer.in_frames() == {1, 2}

    dynamic_answer_2 = label_object.get_dynamic_answer(frame=3, attribute=dynamic_radio)
    dynamic_answer_2.set(dynamic_radio_option_2)
    dynamic_answer.copy_to_frames(frames=[1])

    assert dynamic_answer.get_value() == dynamic_radio_option_1
    assert dynamic_answer_2.get_value() == dynamic_radio_option_2

    dynamic_answer_2.copy_to_frames(frames=[1])
    assert dynamic_answer_2.get_value() == dynamic_radio_option_2
    assert dynamic_answer.get_value() == dynamic_radio_option_2
    assert dynamic_answer.in_frames() == dynamic_answer_2.in_frames()

    with pytest.raises(RuntimeError):
        dynamic_answer_2.copy_to_frames([100])


def test_label_classifications():
    label_classification_1 = LabelClassification(text_classification)
    label_classification_2 = LabelClassification(text_classification)
    assert not label_classification_1.is_valid()

    label_classification_1.add_to_frames([1, 2, 3])
    assert label_classification_1.is_valid()

    answer_1 = label_classification_1.get_static_answer()

    answer_1.set("Dionysus")
    assert answer_1.get_value() == "Dionysus"

    answer_2 = label_classification_2.get_static_answer()
    answer_2.copy_from(answer_1)
    assert answer_2.get_value() == "Dionysus"

    answer_2.set("Hades")
    assert answer_2.get_value() == "Hades"
    assert answer_1.get_value() == "Dionysus"


def test_add_and_get_label_classifications_to_label_row():
    label_row = LabelRow(empty_image_group_labels, all_types_structure)
    label_classification_1 = LabelClassification(text_classification)
    label_classification_2 = LabelClassification(text_classification)
    label_classification_3 = LabelClassification(checklist_classification)

    label_classification_1.add_to_frames([1, 2])
    label_classification_2.add_to_frames([3, 4])
    label_classification_3.add_to_frames([1, 2, 3, 4])

    label_row.add_classification(label_classification_1)
    label_row.add_classification(label_classification_2)
    label_row.add_classification(label_classification_3)

    label_classifications = label_row.get_classifications()
    assert set(label_classifications) == {label_classification_1, label_classification_2, label_classification_3}

    filtered_label_classifications = label_row.get_classifications(text_classification)
    assert set(filtered_label_classifications) == {label_classification_1, label_classification_2}

    overlapping_label_classification = LabelClassification(text_classification)
    overlapping_label_classification.add_to_frames([1])
    with pytest.raises(ValueError):
        label_row.add_classification(overlapping_label_classification)

    overlapping_label_classification.set_frames([5])
    label_row.add_classification(overlapping_label_classification)
    with pytest.raises(ValueError):
        overlapping_label_classification.add_to_frames([1])
    with pytest.raises(ValueError):
        overlapping_label_classification.set_frames([1])

    label_row.remove_classification(label_classification_1)
    overlapping_label_classification.add_to_frames([1])

    with pytest.raises(ValueError):
        overlapping_label_classification.add_to_frames([3])
    label_classification_2.remove_from_frames([3])
    overlapping_label_classification.add_to_frames([3])


# ==========================================================
# =========== actually working tests above here ============
# ==========================================================


# def test_read_improvements():
#     label_row = LabelRow(empty_image_group_labels, all_types_structure)
#
#     frame_view: FrameView = label_row.get_frame(1)
#
#     added_label_object = frame_view.add_label_object(
#         coordinates=KEYPOINT_COORDINATES,
#         label_object_type=box_ontology_item,  # optional ontology item.
#         existing_object=1,  # Optional
#     )
#     # DENIS: either create a new one or add the existing one.
#
#     # now what about answers?
#     static_answers = added_label_object.get_static_answers()
#
#     ## otherwise how would it look like?
#     object_ = label_row.new_object(ontology_type=box_ontology_item, coordinates=KEYPOINT_COORDINATES, frames={1})
#     object_.set_coordinates(KEYPOINT_COORDINATES, frames=[1, 2, 3])


# def test_frame_view():
# DENIS: implement this view!
#     label_row = LabelRow(empty_image_group_labels, all_types_structure)
#
#     frame_view: FrameView = label_row.get_frame(1)
#
#     object_instance_1: LabelObject = frame_view.create_object(BOX_COORDINATES, box_ontology_item, answer=None)
#     frame_view.add_object(BOX_COORDINATES, existing_object, answer=None)  # answer is optional
#
#     existing_instances: Dict[InternalUuid, LabelObject] = {}
#
#     for frame in label_row.frames():
#         assert frame.number == 1
#         assert frame.uuid == "abc"
#         assert frame.has_object(object_instance_1)
#
#     assert frame_view.get_objects == [object_instance_1]


# def test_read_coordinates():
#     label_object = LabelObject()
#     x = label_object.get_coordinates()  # list of frame to coordinates (maybe a map?)
#     x = label_object.get_coordinates_for_frame()
#     x = label_object.dynamic_answers()  # list of dynamic answers. (maybe a map from the frame?)
#     x = label_object.dynamic_answer_for_frame()
#     x = label_object.answer_objects
#
#
# def test_workflow_with_label_structure():
#     project = Project()
#     label_structure = project.get_label_structure()
#
#     used_frames = label_structure.get_used_frames()
#     label_row = label_structure.get_or_create_label_by_frame(used_frames[0])
#
#     # Do the transformations
#
#     label_structure.upload()


# def test_david_notes():
#
#     project = ...
#
#     label_class = project.get_label_class(label_hash)
#
#     label_object = label_class.get_object(object_hash)
#     assert label_object.frames() == [1, 2, 3]
#     assert label_object.coordinates_for_frame(1) == BOX_COORDINATES
#
#     new_label_ojbect = LabelObject(...)
#     new_label_ojbect.set_coordinates(BOX_COORDINATES, frames={3})
#
#     label_class.add_object(new_label_ojbect)  # validation
#
#     label_class.save()
#
#     project.delete_label_rows([...])
#
#     save_multiple_label_classes([label_class, ...])  # DENIS: bulk getter and setters are needed by David.
#     # DENIS: ensure terminology is similar to open source given that it might be used for Encord Active
