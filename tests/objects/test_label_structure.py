from dataclasses import dataclass
from typing import Any, List, Tuple

from encord import Project
from encord.objects.label_structure import (
    BoundingBoxCoordinates,
    LabelObject,
    LabelRow,
    LabelRowReadOnlyData,
    TextAnswer,
)
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.empty_image_group import empty_image_group

"""

DENIS: Talk to Alexey
Iterate over the frames, not only objects/classifications.
"""


def get_item_by_hash(feature_node_hash: str):
    for object_ in all_types_structure.objects:
        if object_.feature_node_hash == feature_node_hash:
            return object_
    for classification in all_types_structure.classifications:
        if classification.feature_node_hash == feature_node_hash:
            return classification

    raise RuntimeError("Item not found.")


box_ontology_item = get_item_by_hash("MjI2NzEy")


def test_create_label_object_one_coordinate():
    label_object = LabelObject(box_ontology_item)  # DENIS: takes ontology item

    coordinates = BoundingBoxCoordinates(
        height=0.1,
        width=0.2,
        top_left_x=0.3,
        top_left_y=0.4,
    )

    label_object.add_coordinates(coordinates=coordinates, frames={1})
    assert label_object.is_valid()


def test_create_a_label_row_from_empty_image_group_label_row_dict():
    label_row = LabelRow(empty_image_group)

    assert label_row.classifications == []
    assert label_row.objects == []
    read_only_data = label_row.label_row_read_only_data
    assert isinstance(read_only_data, LabelRowReadOnlyData)
    # TODO: do more assertions


def test_add_label_object_to_label_row():
    label_row = LabelRow(empty_image_group)
    label_object = LabelObject(box_ontology_item)  # DENIS: takes ontology item

    coordinates = BoundingBoxCoordinates(
        height=0.1,
        width=0.2,
        top_left_x=0.3,
        top_left_y=0.4,
    )

    label_object.add_coordinates(coordinates=coordinates, frames={1})
    label_row.add_object(label_object)
    assert label_row.objects[0] == label_object


# ==========================================================
# =========== actually working tests above here ============
# ==========================================================


def test_add_same_answers_to_different_label_objects():
    label_row = LabelRow()
    feature_hash = "34535"
    label_object_1 = label_row.add_new_object(feature_hash)
    label_object_2 = label_row.add_new_object(feature_hash)

    text_attribute = 5  # TextAttribute
    answer = TextAnswer(text_attribute)
    answer.set_value("Alexey")

    label_object_1.set_answer(answer)
    label_object_2.set_answer(answer)


def test_create_label_object_with_answers():
    label_object = LabelObject()

    label_object.add_coordinates(coordinates={"x": 5, "y": 6}, frames=1)
    answer_objects = label_object.answer_objects
    for answer_object in answer_objects:
        if not answer_object.answered:
            answer_object.set(value="my text")

    label_object.is_valid()
    label_object.are_all_answered()  # maybe within .is_valid()


def test_create_label_object_with_dynamic_answers():
    label_object = LabelObject()

    label_object.add_coordinates(coordinates={"x": 5, "y": 6}, frames=1)
    """
    I want to be able to inspect dynamic answers, set them, leave them unanswered, 
    but I would like to not repeat myself across different frames.
    """
    # used_coordinates = label_object.used_coordinates()
    # label_object.add_dynamic_answer(coordinates=used_coordinates, )
    frames = label_object.used_frames()
    # DENIS: for now, try to just do them individually by label

    # ---- Getting which dynamic answer objects I'm interested in
    dynamic_answer_objects = label_object.dynamic_answer_for_frame(
        frames[0]
    )  # DENIS: or have a general search function
    # The dynamic_answer_object always has an association to the parent.

    # ---- Setting the answer
    for answer_object in dynamic_answer_objects:
        if not answer_object.answered:
            answer_object.set_answer(value="my text")

        #   DENIS: what if I want to use the same answer object in different LabelObjects and don't want to set it manually
        #     each time?

        # --- propagating the same answer.
        answer_object.set_full_range()
        answer_object.set_range([[1, 3]])
        # ^ throws if invalid.


class Answer:
    def set_value(self, value: Any):
        pass

    def propagate_to_frames(self, range):
        pass


@dataclass
class FrameThing:
    """has reference to LabelObject"""

    _frame_number: int
    _parent: LabelObject

    @property
    def dynamic_answers(self):
        # returns all dynamic answer

        pass


#
# class AnswerByFrames:
#     def __init__(self, frame_range: List[Tuple[int, int]], feature_hash: str):
#         pass
#
#     def get_for_frame(self, frame: int) -> Answer:
#         pass
#
#     def has_consistent_values(self) -> bool:
#         pass
#
#     def get_value(self):
#         """Throws if different values."""
#         pass
#
#     def split_to_consistent(self) -> List[AnswerByFrames]:
#         """Splits to the same value."""
#         pass
#
#     def get_sub_range(self, frame_range) -> AnswerByFrames:
#         pass
#
#     def set_value(self, v: Any):
#         """sets value for all the ranges."""
#         pass


class Answer4:
    def __init__(self, frame_num: int, feature_hash: str):
        pass

    def set_value(self, v: Any):
        pass

    def get_value(self):
        pass

    def copy_to_frames(self, range):
        pass

    def in_ranges(self):
        pass


def test_dynamic_attributes_4():
    label_object = LabelObject()

    label_object.add_coordinates(coordinates={"x": 5, "y": 6}, frames=1)
    label_object.add_coordinates(coordinates={"x": 5, "y": 6}, frames=2)
    label_object.add_coordinates(coordinates={"x": 5, "y": 6}, frames=3)

    answer_4 = label_object.answer_for_frame(frame=1)
    answer_4.set_value("1")
    answer_4.copy_to_frames(range=[2, 3])
    ranges = answer_4.in_ranges()
    assert ranges == List[(1, 3)]

    answer_5 = label_object.answer_for_frame(frame=3)
    answer_5.set_value("Denis")
    ranges = answer_5.in_ranges()
    assert ranges == List[(3, 3)]

    all_answers = label_object.get_all_dynamic_answers()
    assert all_answers == List[answer_4, answer_5]

    answer_4.copy_to_frames(3)
    assert answer_4.get_value() == answer_5.get_value()
    assert answer_4.in_ranges() == answer_5.in_ranges()


def test_dynamic_attributes_3():
    label_object = LabelObject()

    label_object.add_coordinates(coordinates={"x": 5, "y": 6}, frames=1)
    label_object.add_coordinates(coordinates={"x": 5, "y": 6}, frames=2)
    label_object.add_coordinates(coordinates={"x": 5, "y": 6}, frames=3)

    answer_by_frames = label_object.get_dynamic_answers_for_frame([1, 3], feature_hash="xyz")

    answer_by_frames.set_value("1")


def test_dynamic_attributes_2():
    label_object = LabelObject()

    label_object.add_coordinates(coordinates={"x": 5, "y": 6}, frames=1)

    frame: FrameThing = label_object.get_frame(1)


def test_read_coordinates():
    label_object = LabelObject()
    x = label_object.get_coordinates()  # list of frame to coordinates (maybe a map?)
    x = label_object.get_coordinates_for_frame()
    x = label_object.dynamic_answers()  # list of dynamic answers. (maybe a map from the frame?)
    x = label_object.dynamic_answer_for_frame()
    x = label_object.answer_objects


def test_workflow_with_label_structure():
    project = Project()
    label_structure = project.get_label_structure()

    used_frames = label_structure.get_used_frames()
    label_row = label_structure.get_or_create_label_by_frame(used_frames[0])

    # Do the transformations

    label_structure.upload()
