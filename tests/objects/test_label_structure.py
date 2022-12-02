from dataclasses import dataclass
from typing import Any, List, Tuple

import pytest

from encord import Project
from encord.objects.label_structure import (
    BoundingBoxCoordinates,
    LabelObject,
    LabelRow,
    LabelRowReadOnlyData,
    ObjectFrameInstanceInfo,
    PointCoordinate,
    PolygonCoordinates,
    TextAnswer,
)
from encord.objects.ontology_structure import OntologyStructure
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.empty_image_group import empty_image_group

"""

DENIS: Talk to Alexey
Iterate over the frames, not only objects/classifications.
"""


def get_item_by_hash(feature_node_hash: str, ontology: OntologyStructure):
    for object_ in ontology.objects:
        if object_.feature_node_hash == feature_node_hash:
            return object_
    for classification in ontology.classifications:
        if classification.feature_node_hash == feature_node_hash:
            return classification

    raise RuntimeError("Item not found.")


box_ontology_item = get_item_by_hash("MjI2NzEy", all_types_structure)
polygon_ontology_item = get_item_by_hash("ODkxMzAx", all_types_structure)
polyline_ontology_item = get_item_by_hash("OTcxMzIy", all_types_structure)

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


def test_create_label_object_one_coordinate():
    label_object = LabelObject(box_ontology_item)  # DENIS: takes ontology item

    coordinates = BoundingBoxCoordinates(
        height=0.1,
        width=0.2,
        top_left_x=0.3,
        top_left_y=0.4,
    )

    label_object.set_coordinates(coordinates=coordinates, frames={1})
    assert label_object.is_valid()


def test_create_a_label_row_from_empty_image_group_label_row_dict():
    label_row = LabelRow(empty_image_group)

    assert label_row.get_classifications() == []
    assert label_row.get_objects() == []
    read_only_data = label_row.label_row_read_only_data
    assert isinstance(read_only_data, LabelRowReadOnlyData)
    # TODO: do more assertions


def test_add_label_object_to_label_row():
    label_row = LabelRow(empty_image_group)
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
    label_row = LabelRow(empty_image_group)
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


def test_filter_for_objects():
    label_row = LabelRow(empty_image_group)
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
    label_row = LabelRow(empty_image_group)
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
    label_row_1 = LabelRow(empty_image_group)
    label_row_2 = LabelRow(empty_image_group)
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
    label_row = LabelRow(empty_image_group)
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


# ==========================================================
# =========== actually working tests above here ============
# ==========================================================


# def test_add_same_answers_to_different_label_objects():
#     label_row = LabelRow()
#     feature_hash = "34535"
#     label_object_1 = label_row.add_new_object(feature_hash)
#     label_object_2 = label_row.add_new_object(feature_hash)
#
#     text_attribute = 5  # TextAttribute
#     answer = TextAnswer(text_attribute)
#     answer.set_value("Alexey")
#
#     label_object_1.set_answer(answer)
#     label_object_2.set_answer(answer)
#
#
# def test_create_label_object_with_answers():
#     label_object = LabelObject()
#
#     label_object.set_coordinates(coordinates={"x": 5, "y": 6}, frames=1)
#     answer_objects = label_object.answer_objects
#     for answer_object in answer_objects:
#         if not answer_object.answered:
#             answer_object.set(value="my text")
#
#     label_object.is_valid()
#     label_object.are_all_answered()  # maybe within .is_valid()
#
#
# def test_create_label_object_with_dynamic_answers():
#     label_object = LabelObject()
#
#     label_object.set_coordinates(coordinates={"x": 5, "y": 6}, frames=1)
#     """
#     I want to be able to inspect dynamic answers, set them, leave them unanswered,
#     but I would like to not repeat myself across different frames.
#     """
#     # used_coordinates = label_object.used_coordinates()
#     # label_object.add_dynamic_answer(coordinates=used_coordinates, )
#     frames = label_object.used_frames()
#     # DENIS: for now, try to just do them individually by label
#
#     # ---- Getting which dynamic answer objects I'm interested in
#     dynamic_answer_objects = label_object.dynamic_answer_for_frame(
#         frames[0]
#     )  # DENIS: or have a general search function
#     # The dynamic_answer_object always has an association to the parent.
#
#     # ---- Setting the answer
#     for answer_object in dynamic_answer_objects:
#         if not answer_object.answered:
#             answer_object.set_answer(value="my text")
#
#         #   DENIS: what if I want to use the same answer object in different LabelObjects and don't want to set it manually
#         #     each time?
#
#         # --- propagating the same answer.
#         answer_object.set_full_range()
#         answer_object.set_range([[1, 3]])
#         # ^ throws if invalid.
#
#
# class Answer:
#     def set_value(self, value: Any):
#         pass
#
#     def propagate_to_frames(self, range):
#         pass
#
#
# @dataclass
# class FrameThing:
#     """has reference to LabelObject"""
#
#     _frame_number: int
#     _parent: LabelObject
#
#     @property
#     def dynamic_answers(self):
#         # returns all dynamic answer
#
#         pass
#
#
# #
# # class AnswerByFrames:
# #     def __init__(self, frame_range: List[Tuple[int, int]], feature_hash: str):
# #         pass
# #
# #     def get_for_frame(self, frame: int) -> Answer:
# #         pass
# #
# #     def has_consistent_values(self) -> bool:
# #         pass
# #
# #     def get_value(self):
# #         """Throws if different values."""
# #         pass
# #
# #     def split_to_consistent(self) -> List[AnswerByFrames]:
# #         """Splits to the same value."""
# #         pass
# #
# #     def get_sub_range(self, frame_range) -> AnswerByFrames:
# #         pass
# #
# #     def set_value(self, v: Any):
# #         """sets value for all the ranges."""
# #         pass
#
#
# class Answer4:
#     def __init__(self, frame_num: int, feature_hash: str):
#         pass
#
#     def set_value(self, v: Any):
#         pass
#
#     def get_value(self):
#         pass
#
#     def copy_to_frames(self, range):
#         pass
#
#     def in_ranges(self):
#         pass
#
#
# def test_dynamic_attributes_4():
#     label_object = LabelObject()
#
#     label_object.set_coordinates(coordinates={"x": 5, "y": 6}, frames=1)
#     label_object.set_coordinates(coordinates={"x": 5, "y": 6}, frames=2)
#     label_object.set_coordinates(coordinates={"x": 5, "y": 6}, frames=3)
#
#     answer_4 = label_object.answer_for_frame(frame=1)
#     answer_4.set_value("1")
#     answer_4.copy_to_frames(range=[2, 3])
#     ranges = answer_4.in_ranges()
#     assert ranges == List[(1, 3)]
#
#     answer_5 = label_object.answer_for_frame(frame=3)
#     answer_5.set_value("Denis")
#     ranges = answer_5.in_ranges()
#     assert ranges == List[(3, 3)]
#
#     all_answers = label_object.get_all_dynamic_answers()
#     assert all_answers == List[answer_4, answer_5]
#
#     answer_4.copy_to_frames(3)
#     assert answer_4.get_value() == answer_5.get_value()
#     assert answer_4.in_ranges() == answer_5.in_ranges()
#
#
# def test_dynamic_attributes_3():
#     label_object = LabelObject()
#
#     label_object.set_coordinates(coordinates={"x": 5, "y": 6}, frames=1)
#     label_object.set_coordinates(coordinates={"x": 5, "y": 6}, frames=2)
#     label_object.set_coordinates(coordinates={"x": 5, "y": 6}, frames=3)
#
#     answer_by_frames = label_object.get_dynamic_answers_for_frame([1, 3], feature_hash="xyz")
#
#     answer_by_frames.set_value("1")
#
#
# def test_dynamic_attributes_2():
#     label_object = LabelObject()
#
#     label_object.set_coordinates(coordinates={"x": 5, "y": 6}, frames=1)
#
#     frame: FrameThing = label_object.get_frame(1)
#
#
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
