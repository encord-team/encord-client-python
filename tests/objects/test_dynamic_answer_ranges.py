from copy import deepcopy
from random import Random
from unittest.mock import Mock, patch

import pytest

from encord.exceptions import LabelRowError
from encord.objects import AnswerForFrames, LabelRowV2, Object, Shape
from encord.objects.attributes import ChecklistAttribute, NumericAttribute, RadioAttribute, TextAttribute
from encord.objects.frames import Range, frames_class_to_frames_list, frames_to_ranges
from tests.objects.common import BASE_LABEL_ROW_METADATA
from tests.objects.data.empty_video import labels as empty_video_labels


def make_object():
    ontology_object = Object(
        name="Dynamic point", shape=Shape.POINT, feature_node_hash="dynamic-point", uid=1, color="#ff0000"
    )
    attribute = ontology_object.add_attribute(TextAttribute, "Text", dynamic=True)
    return ontology_object.create_instance(), attribute


@pytest.mark.parametrize("frames", [[], Range(5, 4), [Range(5, 4)], [Range(5, 4), Range(1, 2)]])
def test_empty_and_reversed_ranges_keep_dense_selection_semantics(frames):
    obj, attribute = make_object()
    obj.set_answer("before", attribute=attribute, frames=Range(0, 6))
    obj.set_answer("after", attribute=attribute, frames=frames)
    selected = set(frames_class_to_frames_list(frames))
    expected = [AnswerForFrames("before", frames_to_ranges(set(range(7)) - selected))]
    if selected:
        expected.append(AnswerForFrames("after", frames_to_ranges(selected)))
    assert obj.get_answer(attribute) == expected
    manager = obj._dynamic_answer_manager
    assert manager.get_answer(attribute, filter_frames=Range(9, 8)) == []
    manager.delete_answer(attribute, Range(9, 8))
    assert obj.get_answer(attribute) == expected


@pytest.mark.parametrize("populated", [False, True])
@pytest.mark.parametrize("frames", [{1, 2}, (1, 2), [1, Range(2, 3)], ["1"], "1"])
def test_invalid_selectors_still_raise_for_writes_reads_and_deletes(populated, frames):
    obj, attribute = make_object()
    if populated:
        obj.set_answer("before", attribute=attribute, frames=Range(0, 3))
    expected = obj.get_answer(attribute)
    manager = obj._dynamic_answer_manager
    for operation in (
        lambda: obj.set_answer("after", attribute=attribute, frames=frames),
        lambda: manager.get_answer(attribute, filter_frames=frames),
        lambda: manager.delete_answer(attribute, frames),
    ):
        with pytest.raises(RuntimeError, match="Unexpected type for frames"):
            operation()
        assert obj.get_answer(attribute) == expected


def test_range_bounds_are_validated_before_any_mutation(all_types_ontology):
    obj, attribute = make_object()
    row = LabelRowV2(deepcopy(BASE_LABEL_ROW_METADATA), Mock(), all_types_ontology)
    row.from_labels_dict(deepcopy(empty_video_labels))
    obj._parent = row
    obj.set_answer("before", attribute=attribute, frames=Range(0, 2))
    limit = row.number_of_frames
    expected = obj.get_answer(attribute)
    for frames, invalid_frame in (
        ([Range(0, 1), Range(limit - 1, limit + 5)], limit),
        ([Range(0, 1), Range(-3, -1)], -3),
    ):
        with pytest.raises(LabelRowError, match=f"supplied frame of `{invalid_frame}`"):
            obj.set_answer("after", attribute=attribute, frames=frames)
        assert obj.get_answer(attribute) == expected


def test_failed_answer_validation_preserves_existing_dense_behavior():
    obj, attribute = make_object()
    obj.set_answer("before", attribute=attribute, frames=Range(0, 4))
    with pytest.raises(ValueError, match="TextAnswer can only be set to a string"):
        obj.set_answer(1.5, attribute=attribute, frames=Range(1, 3))
    assert obj.get_answer(attribute) == [AnswerForFrames("before", [Range(0, 0), Range(4, 4)])]


def test_default_empty_selection_does_not_validate_an_unused_answer():
    obj, attribute = make_object()
    obj.set_answer(1.5, attribute=attribute)
    assert obj.get_answer(attribute) == []


def test_range_inputs_and_results_do_not_alias_stored_answers():
    obj, attribute = make_object()
    input_range = Range(2, 8)
    obj.set_answer("answer", attribute=attribute, frames=[input_range])
    input_range.start = 0
    answers = obj.get_answer(attribute)
    answers[0].ranges[0].end = 99
    answers[0].ranges.append(Range(100, 101))
    obj._get_all_dynamic_answers()[0][1][0].start = 1
    assert obj.get_answer(attribute) == [AnswerForFrames("answer", [Range(2, 8)])]


def test_point_queries_do_not_scan_unrelated_answer_fragments():
    obj, attribute = make_object()
    for frame in range(200):
        obj.set_answer(str(frame % 2), attribute=attribute, frames=frame)
    with patch(
        "encord.common.range_manager.RangeManager.intersection",
        side_effect=AssertionError("Point queries must use the interval index"),
    ):
        assert obj.get_answer(attribute, filter_frame=300) == []
        assert obj.get_answer(attribute, filter_frame=199) == [
            AnswerForFrames("1", [Range(frame, frame) for frame in range(1, 200, 2)])
        ]


def test_range_operations_never_expand_the_selected_span():
    obj, attribute = make_object()
    end = 10**9
    with patch(
        "encord.objects.ontology_object_instance.frames_class_to_frames_list",
        side_effect=AssertionError("Dynamic answers must not expand ranges"),
    ):
        obj.set_answer("whole", attribute=attribute, frames=Range(0, end))
        obj.set_answer("middle", attribute=attribute, frames=Range(10, end - 10))
        obj._dynamic_answer_manager.delete_answer(attribute, Range(20, end - 20))
        assert obj.get_answer(attribute, filter_frame=15) == [
            AnswerForFrames("middle", [Range(10, 19), Range(end - 19, end - 10)])
        ]
        copied = obj.copy()
        assert copied._get_all_dynamic_answers() == obj._get_all_dynamic_answers()
        serialized = [answer.to_encord_dict(ranges=ranges) for answer, ranges in obj._get_all_dynamic_answers()]
        assert [answer["range"] for answer in serialized] == [
            [[0, 9], [end - 9, end]],
            [[10, 19], [end - 19, end - 10]],
        ]
        with pytest.raises(LabelRowError, match="no coordinates"):
            obj.are_dynamic_answers_valid()


@pytest.mark.parametrize("seed", range(8))
def test_range_operations_match_dense_model_for_all_answer_types(seed):
    obj, text = make_object()
    numeric = obj.ontology_item.add_attribute(NumericAttribute, "Score", dynamic=True)
    radio = obj.ontology_item.add_attribute(RadioAttribute, "Choice", dynamic=True)
    radio.add_option("First")
    radio.add_option("Second")
    checklist = obj.ontology_item.add_attribute(ChecklistAttribute, "Tags", dynamic=True)
    checklist.add_option("First")
    checklist.add_option("Second")
    obj = obj.ontology_item.create_instance()
    attributes = [text, numeric, radio, checklist]
    values = [["", "a", "b"], [0, 1.5, -2], radio.options, [[], checklist.options[:1], checklist.options]]
    expected = {}
    rng = Random(seed)

    # The oracle stores individual frames and insertion order, independent of range algorithms.
    for _ in range(200):
        index = rng.randrange(len(attributes))
        attribute = attributes[index]
        value_index = rng.randrange(len(values[index]))
        value = values[index][value_index]
        selector = rng.choice(
            [
                rng.randrange(20),
                [rng.randrange(20) for _ in range(5)],
                Range(*sorted([rng.randrange(20), rng.randrange(20)])),
                [Range(*sorted([rng.randrange(20), rng.randrange(20)])) for _ in range(3)],
                [],
            ]
        )
        selected = set(frames_class_to_frames_list(selector))
        write = rng.randrange(3) != 0
        filter_value = None if rng.randrange(2) else value
        if not write and rng.randrange(4) == 0:
            selector = None
            selected = set(range(20))
        for key in list(expected):
            attr_index, answer_index = key
            if attr_index == index and (
                write or filter_value is None or values[attr_index][answer_index] == filter_value
            ):
                expected[key] -= selected
                if not expected[key]:
                    del expected[key]
        if write:
            obj.set_answer(value, attribute=attribute, frames=selector)
            if selected:
                expected.setdefault((index, value_index), set()).update(selected)
        else:
            obj._dynamic_answer_manager.delete_answer(attribute, selector, filter_value)

        for attr_index, attr in enumerate(attributes):
            answers = [
                AnswerForFrames(values[i][j], frames_to_ranges(frames))
                for (i, j), frames in expected.items()
                if i == attr_index
            ]
            assert obj.get_answer(attr) == answers, (seed, index, selector)
            probe = rng.randrange(20)
            assert obj.get_answer(attr, filter_frame=probe) == [
                answer for answer in answers if any(r.start <= probe <= r.end for r in answer.ranges)
            ]
        assert [
            (answer.ontology_attribute.feature_node_hash, answer.get(), ranges)
            for answer, ranges in obj._get_all_dynamic_answers()
        ] == [
            (attributes[i].feature_node_hash, values[i][j], frames_to_ranges(frames))
            for (i, j), frames in expected.items()
        ]
