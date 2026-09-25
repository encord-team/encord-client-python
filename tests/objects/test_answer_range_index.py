from unittest.mock import patch

import pytest

from encord.common.range_manager import RangeManager
from encord.objects.answers import TextAnswer
from encord.objects.attributes import TextAttribute
from encord.objects.common import Shape
from encord.objects.frames import Range
from encord.objects.ontology_object import Object
from encord.objects.ontology_object_instance import AnswerRangeIndex


@pytest.fixture
def answers():
    obj = Object(name="Point", shape=Shape.POINT, feature_node_hash="point", uid=1, color="#ff0000")
    attribute = obj.add_attribute(TextAttribute, "Text", dynamic=True)
    other_attribute = obj.add_attribute(TextAttribute, "Other text", dynamic=True)
    result = []
    for attr, value in [(attribute, "a"), (attribute, "b"), (attribute, "c"), (other_attribute, "a")]:
        answer = TextAnswer(attr)
        answer.set(value)
        result.append(answer)
    return result


def snapshot(index):
    return [(answer, index.ranges_for(answer)) for answer in index.answers()]


def assert_consistent(index):
    by_attribute = {}
    for answer, ranges in snapshot(index):
        for range_ in ranges:
            by_attribute.setdefault(answer.ontology_attribute.feature_node_hash, []).append(
                (range_.start, range_.end, answer)
            )
    for intervals in by_attribute.values():
        intervals.sort()
        assert all(left[1] < right[0] for left, right in zip(intervals, intervals[1:]))
    assert index._ranges_by_attribute == by_attribute


def test_assign_normalizes_splits_and_merges_ranges(answers):
    a, b, _, _ = answers
    index = AnswerRangeIndex()
    index.assign(a, [Range(6, 9), Range(0, 4), Range(2, 6)])
    assert snapshot(index) == [(a, [Range(0, 9)])]
    index.assign(b, [Range(3, 6)])
    assert snapshot(index) == [(a, [Range(0, 2), Range(7, 9)]), (b, [Range(3, 6)])]
    index.assign(a, [Range(3, 6)])
    assert snapshot(index) == [(a, [Range(0, 9)])]
    assert_consistent(index)


@pytest.mark.parametrize(
    "selected,remaining",
    [
        ([Range(0, 2)], [Range(3, 9)]),
        ([Range(7, 12)], [Range(0, 6)]),
        ([Range(3, 6)], [Range(0, 2), Range(7, 9)]),
        ([Range(10, 20)], [Range(0, 9)]),
        ([Range(7, 9), Range(1, 3), Range(2, 4)], [Range(0, 0), Range(5, 6)]),
        ([], [Range(0, 9)]),
        (None, []),
    ],
)
def test_remove_preserves_unselected_frames_and_other_attributes(answers, selected, remaining):
    a, _, _, other = answers
    index = AnswerRangeIndex()
    index.assign(a, [Range(0, 9)])
    index.assign(other, [Range(0, 9)])
    index.remove(a.ontology_attribute, selected)
    expected = ([(a, remaining)] if remaining else []) + [(other, [Range(0, 9)])]
    assert snapshot(index) == expected
    assert_consistent(index)


def test_remove_can_filter_answer_values(answers):
    a, b, _, _ = answers
    index = AnswerRangeIndex()
    index.assign(a, [Range(0, 9)])
    index.assign(b, [Range(3, 6)])
    index.remove(a.ontology_attribute, [Range(1, 8)], filter_answer="a")
    assert snapshot(index) == [(a, [Range(0, 0), Range(9, 9)]), (b, [Range(3, 6)])]
    index.remove(a.ontology_attribute, filter_answer="b")
    assert snapshot(index) == [(a, [Range(0, 0), Range(9, 9)])]
    assert_consistent(index)


def test_overlapping_selects_answers_without_clipping_their_ranges(answers):
    a, b, _, other = answers
    index = AnswerRangeIndex()
    index.assign(a, [Range(0, 2), Range(8, 10)])
    index.assign(b, [Range(4, 6)])
    index.assign(other, [Range(0, 10)])
    assert index.overlapping(a.ontology_attribute, [Range(2, 4)]) == {a, b}
    assert index.overlapping(a.ontology_attribute, [Range(3, 3)]) == set()
    assert index.overlapping(a.ontology_attribute, []) == set()
    assert index.overlapping(a.ontology_attribute, [Range(10, 10), Range(0, 0)]) == {a}
    assert index.ranges_for(a) == [Range(0, 2), Range(8, 10)]


def test_replacing_all_of_an_answer_preserves_global_insertion_order(answers):
    a, b, _, other = answers
    index = AnswerRangeIndex()
    index.assign(a, [Range(0, 1)])
    index.assign(other, [Range(0, 0)])
    index.assign(b, [Range(2, 2)])
    index.assign(a, [Range(0, 0)])
    assert list(index.answers()) == [a, other, b]
    index.assign(a, [Range(0, 1)])
    assert list(index.answers()) == [other, b, a]
    assert_consistent(index)


def test_empty_assignment_does_not_register_an_answer(answers):
    index = AnswerRangeIndex()
    index.assign(answers[0], [])
    assert snapshot(index) == []
    assert index.answered_ranges() == []


def test_invalid_assignment_does_not_partially_mutate_the_index(answers):
    a, b, _, _ = answers
    index = AnswerRangeIndex()
    index.assign(a, [Range(0, 9)])
    with pytest.raises(ValueError, match="must not be greater than end"):
        index.assign(b, [Range(0, 2), Range(6, 5)])
    assert snapshot(index) == [(a, [Range(0, 9)])]
    assert_consistent(index)


def test_empty_ranges_and_missing_attributes_select_nothing(answers):
    a, _, _, other = answers
    index = AnswerRangeIndex()
    index.remove(a.ontology_attribute)
    assert index.overlapping(a.ontology_attribute, [Range(0, 0)]) == set()
    index.assign(a, [Range(0, 9)])
    index.remove(other.ontology_attribute)
    index.remove(a.ontology_attribute, [Range(5, 4)])
    assert index.overlapping(a.ontology_attribute, [Range(5, 4)]) == set()
    assert snapshot(index) == [(a, [Range(0, 9)])]
    assert_consistent(index)


def test_range_results_and_copies_are_independent(answers):
    a, b, _, _ = answers
    index = AnswerRangeIndex()
    supplied = Range(0, 9)
    index.assign(a, [supplied])
    supplied.end = 99
    index.ranges_for(a)[0].start = 5
    index.answered_ranges()[0].end = 100
    assert snapshot(index) == [(a, [Range(0, 9)])]
    copied = index.copy()
    assert copied == index
    copied.assign(b, [Range(3, 6)])
    index.remove(a.ontology_attribute, [Range(0, 0)])
    assert snapshot(index) == [(a, [Range(1, 9)])]
    assert snapshot(copied) == [(a, [Range(0, 2), Range(7, 9)]), (b, [Range(3, 6)])]
    assert copied != index
    assert index != object()
    assert_consistent(index)
    assert_consistent(copied)


class CountingIntervals(list):
    shifted_items = 0

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            start, stop, _ = key.indices(len(self))
            if len(value) != stop - start:
                self.shifted_items += len(self) - stop
        super().__setitem__(key, value)


@pytest.mark.parametrize("distinct", [False, True])
def test_replacing_answers_does_not_repeatedly_shift_the_interval_index(answers, distinct):
    attribute = answers[0].ontology_attribute
    index = AnswerRangeIndex()
    count = 200
    for frame in range(count):
        answer = TextAnswer(attribute)
        answer.set(str(frame if distinct else frame % 2))
        index.assign(answer, [Range(frame, frame)])
    intervals = CountingIntervals(index._ranges_by_attribute[attribute.feature_node_hash])
    index._ranges_by_attribute[attribute.feature_node_hash] = intervals
    for frame in range(count):
        answer = TextAnswer(attribute)
        answer.set(f"edited-{frame if distinct else frame % 2}")
        index.assign(answer, [Range(frame, frame)])
    assert intervals.shifted_items <= count * 2
    for frame in range(count):
        [answer] = index.overlapping(attribute, [Range(frame, frame)])
        assert answer.get() == f"edited-{frame if distinct else frame % 2}"
    assert_consistent(index)


def test_aggregating_fragmented_answers_does_not_repeatedly_shift_ranges(answers):
    index = AnswerRangeIndex()
    count = 200
    for frame in range(count):
        index.assign(answers[frame % 2], [Range(frame, frame)])
    merged = RangeManager()
    intervals = CountingIntervals()
    merged._range_set._ranges = intervals
    with patch("encord.objects.ontology_object_instance.RangeManager", return_value=merged):
        assert index.answered_ranges() == [Range(0, count - 1)]
    assert intervals.shifted_items <= count * 2


def test_large_ranges_remain_compact(answers):
    a, b, _, _ = answers
    index = AnswerRangeIndex()
    end = 10**9
    index.assign(a, [Range(0, end)])
    index.assign(b, [Range(10, end - 10)])
    index.remove(a.ontology_attribute, [Range(20, end - 20)])
    assert snapshot(index) == [
        (a, [Range(0, 9), Range(end - 9, end)]),
        (b, [Range(10, 19), Range(end - 19, end - 10)]),
    ]
    assert_consistent(index)
