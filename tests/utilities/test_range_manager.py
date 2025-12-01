import pytest

from encord.common.range_manager import RangeManager
from encord.objects.frames import Range


@pytest.fixture
def range_manager() -> RangeManager:
    initial_ranges = [Range(start=2, end=5), Range(start=10, end=20)]
    return RangeManager(frame_class=initial_ranges)


def test_initialize_ranges(range_manager: RangeManager) -> None:
    actual_ranges = range_manager.get_ranges()
    assert actual_ranges[0].start == 2
    assert actual_ranges[0].end == 5
    assert actual_ranges[1].start == 10
    assert actual_ranges[1].end == 20


def test_add_ranges(range_manager: RangeManager) -> None:
    range_manager.add_ranges([Range(start=5, end=7), Range(start=21, end=22)])

    actual_ranges = range_manager.get_ranges()
    assert actual_ranges[0].start == 2
    assert actual_ranges[0].end == 7
    assert actual_ranges[1].start == 10
    assert actual_ranges[1].end == 22  # IntegerRangeSet merges adjacent ranges: (10-20) + (21-22) = (10-22)


def test_remove_ranges(range_manager: RangeManager) -> None:
    range_manager.remove_ranges([Range(start=4, end=5), Range(start=16, end=19)])

    actual_ranges = range_manager.get_ranges()
    assert actual_ranges[0].start == 2
    assert actual_ranges[0].end == 3
    assert actual_ranges[1].start == 10
    assert actual_ranges[1].end == 15
    assert actual_ranges[2].start == 20
    assert actual_ranges[2].end == 20


def test_get_ranges_as_frames(range_manager: RangeManager) -> None:
    frames = range_manager.get_ranges_as_frames()
    assert frames == {2, 3, 4, 5, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20}


def test_get_intersection_with_other_frames(range_manager: RangeManager) -> None:
    other_frames = [1, 3, 16, 25]
    intersecting_ranges = range_manager.intersection(other_frames)
    assert intersecting_ranges[0].start == 3
    assert intersecting_ranges[0].end == 3
    assert intersecting_ranges[1].start == 16
    assert intersecting_ranges[1].end == 16

    other_ranges = [Range(start=0, end=3), Range(start=19, end=22)]
    intersecting_ranges = range_manager.intersection(other_ranges)
    assert intersecting_ranges[0].start == 2
    assert intersecting_ranges[0].end == 3
    assert intersecting_ranges[1].start == 19
    assert intersecting_ranges[1].end == 20


# Initialization tests
def test_initialize_with_single_int() -> None:
    rm = RangeManager(frame_class=5)
    actual_ranges = rm.get_ranges()
    assert len(actual_ranges) == 1
    assert actual_ranges[0].start == 5
    assert actual_ranges[0].end == 5


def test_initialize_with_single_range() -> None:
    rm = RangeManager(frame_class=Range(start=10, end=15))
    actual_ranges = rm.get_ranges()
    assert len(actual_ranges) == 1
    assert actual_ranges[0].start == 10
    assert actual_ranges[0].end == 15


def test_initialize_with_list_of_ints() -> None:
    rm = RangeManager(frame_class=[1, 3, 5, 7])
    actual_ranges = rm.get_ranges()
    assert len(actual_ranges) == 4
    assert actual_ranges[0].start == 1
    assert actual_ranges[0].end == 1
    assert actual_ranges[1].start == 3
    assert actual_ranges[1].end == 3
    assert actual_ranges[2].start == 5
    assert actual_ranges[2].end == 5
    assert actual_ranges[3].start == 7
    assert actual_ranges[3].end == 7


def test_initialize_with_set_of_ints() -> None:
    rm = RangeManager(frame_class={1, 5, 3, 7})
    actual_ranges = rm.get_ranges()
    assert len(actual_ranges) == 4
    # Should be sorted
    assert actual_ranges[0].start == 1
    assert actual_ranges[1].start == 3
    assert actual_ranges[2].start == 5
    assert actual_ranges[3].start == 7


def test_initialize_with_none() -> None:
    rm = RangeManager(frame_class=None)
    actual_ranges = rm.get_ranges()
    assert len(actual_ranges) == 0


def test_initialize_with_no_args() -> None:
    rm = RangeManager()
    actual_ranges = rm.get_ranges()
    assert len(actual_ranges) == 0


def test_initialize_with_invalid_type() -> None:
    with pytest.raises(RuntimeError, match="Unexpected type for frames"):
        RangeManager(frame_class="invalid")


# Single range operations
def test_add_single_range_to_empty() -> None:
    rm = RangeManager()
    rm.add_range(Range(start=5, end=10))
    actual_ranges = rm.get_ranges()
    assert len(actual_ranges) == 1
    assert actual_ranges[0].start == 5
    assert actual_ranges[0].end == 10


def test_add_range_merges_overlapping() -> None:
    rm = RangeManager(frame_class=[Range(start=5, end=10)])
    rm.add_range(Range(start=8, end=15))
    actual_ranges = rm.get_ranges()
    assert len(actual_ranges) == 1
    assert actual_ranges[0].start == 5
    assert actual_ranges[0].end == 15


def test_add_range_adjacent_merged() -> None:
    # IntegerRangeSet merges adjacent ranges for efficiency: (5-10) + (11-15) = (5-15)
    rm = RangeManager(frame_class=[Range(start=5, end=10)])
    rm.add_range(Range(start=11, end=15))
    actual_ranges = rm.get_ranges()
    assert len(actual_ranges) == 1
    assert actual_ranges[0].start == 5
    assert actual_ranges[0].end == 15


def test_cant_add_end_before_start() -> None:
    rm = RangeManager()
    with pytest.raises(ValueError):
        rm.add_range(Range(start=15, end=10))


def test_add_range_merges_contained() -> None:
    rm = RangeManager(frame_class=[Range(start=5, end=20)])
    rm.add_range(Range(start=10, end=15))
    actual_ranges = rm.get_ranges()
    assert len(actual_ranges) == 1
    assert actual_ranges[0].start == 5
    assert actual_ranges[0].end == 20


def test_add_range_merges_multiple() -> None:
    rm = RangeManager(frame_class=[Range(start=1, end=5), Range(start=10, end=15), Range(start=20, end=25)])
    rm.add_range(Range(start=4, end=22))
    actual_ranges = rm.get_ranges()
    assert len(actual_ranges) == 1
    assert actual_ranges[0].start == 1
    assert actual_ranges[0].end == 25


def test_add_range_no_overlap() -> None:
    rm = RangeManager(frame_class=[Range(start=5, end=10)])
    rm.add_range(Range(start=15, end=20))
    actual_ranges = rm.get_ranges()
    assert len(actual_ranges) == 2
    assert actual_ranges[0].start == 5
    assert actual_ranges[0].end == 10
    assert actual_ranges[1].start == 15
    assert actual_ranges[1].end == 20


# Remove range tests
def test_remove_range_no_overlap() -> None:
    rm = RangeManager(frame_class=[Range(start=5, end=10)])
    rm.remove_range(Range(start=15, end=20))
    actual_ranges = rm.get_ranges()
    assert len(actual_ranges) == 1
    assert actual_ranges[0].start == 5
    assert actual_ranges[0].end == 10


def test_remove_range_complete_overlap() -> None:
    rm = RangeManager(frame_class=[Range(start=5, end=10)])
    rm.remove_range(Range(start=5, end=10))
    actual_ranges = rm.get_ranges()
    assert len(actual_ranges) == 0


def test_remove_range_contained() -> None:
    rm = RangeManager(frame_class=[Range(start=5, end=20)])
    rm.remove_range(Range(start=10, end=15))
    actual_ranges = rm.get_ranges()
    assert len(actual_ranges) == 2
    assert actual_ranges[0].start == 5
    assert actual_ranges[0].end == 9
    assert actual_ranges[1].start == 16
    assert actual_ranges[1].end == 20


def test_remove_range_partial_left() -> None:
    rm = RangeManager(frame_class=[Range(start=5, end=15)])
    rm.remove_range(Range(start=1, end=10))
    actual_ranges = rm.get_ranges()
    assert len(actual_ranges) == 1
    assert actual_ranges[0].start == 11
    assert actual_ranges[0].end == 15


def test_remove_range_partial_right() -> None:
    rm = RangeManager(frame_class=[Range(start=5, end=15)])
    rm.remove_range(Range(start=10, end=20))
    actual_ranges = rm.get_ranges()
    assert len(actual_ranges) == 1
    assert actual_ranges[0].start == 5
    assert actual_ranges[0].end == 9


def test_remove_range_from_empty() -> None:
    rm = RangeManager()
    rm.remove_range(Range(start=5, end=10))
    actual_ranges = rm.get_ranges()
    assert len(actual_ranges) == 0


# Clear ranges test
def test_clear_ranges(range_manager: RangeManager) -> None:
    range_manager.clear_ranges()
    actual_ranges = range_manager.get_ranges()
    assert len(actual_ranges) == 0


# Intersection edge cases
def test_intersection_with_empty_other() -> None:
    rm = RangeManager(frame_class=[Range(start=5, end=10)])
    intersecting_ranges = rm.intersection([])
    assert len(intersecting_ranges) == 0


def test_intersection_with_empty_self() -> None:
    rm = RangeManager()
    intersecting_ranges = rm.intersection([Range(start=5, end=10)])
    assert len(intersecting_ranges) == 0


def test_intersection_no_overlap() -> None:
    rm = RangeManager(frame_class=[Range(start=5, end=10)])
    intersecting_ranges = rm.intersection([Range(start=15, end=20)])
    assert len(intersecting_ranges) == 0


def test_intersection_complete_overlap() -> None:
    rm = RangeManager(frame_class=[Range(start=5, end=20)])
    intersecting_ranges = rm.intersection([Range(start=5, end=20)])
    assert len(intersecting_ranges) == 1
    assert intersecting_ranges[0].start == 5
    assert intersecting_ranges[0].end == 20


def test_intersection_partial_overlap() -> None:
    rm = RangeManager(frame_class=[Range(start=5, end=15)])
    intersecting_ranges = rm.intersection([Range(start=10, end=20)])
    assert len(intersecting_ranges) == 1
    assert intersecting_ranges[0].start == 10
    assert intersecting_ranges[0].end == 15


def test_intersection_multiple_ranges() -> None:
    rm = RangeManager(frame_class=[Range(start=1, end=5), Range(start=10, end=15), Range(start=20, end=25)])
    intersecting_ranges = rm.intersection([Range(start=3, end=12), Range(start=22, end=30)])
    assert len(intersecting_ranges) == 3
    assert intersecting_ranges[0].start == 3
    assert intersecting_ranges[0].end == 5
    assert intersecting_ranges[1].start == 10
    assert intersecting_ranges[1].end == 12
    assert intersecting_ranges[2].start == 22
    assert intersecting_ranges[2].end == 25


# Test that get_ranges returns a copy
def test_get_ranges_returns_copy() -> None:
    rm = RangeManager(frame_class=[Range(start=5, end=10)])
    ranges = rm.get_ranges()
    ranges[0].start = 100
    actual_ranges = rm.get_ranges()
    assert actual_ranges[0].start == 5


# Test sorting
def test_ranges_are_sorted() -> None:
    rm = RangeManager()
    rm.add_range(Range(start=20, end=25))
    rm.add_range(Range(start=5, end=10))
    rm.add_range(Range(start=1, end=3))
    actual_ranges = rm.get_ranges()
    assert actual_ranges[0].start == 1
    assert actual_ranges[1].start == 5
    assert actual_ranges[2].start == 20


def test_sorted_invariant_maintained() -> None:
    """Verify sorted invariant is maintained after all operations."""
    rm = RangeManager()

    # Add ranges in random order
    rm.add_range(Range(start=50, end=55))
    rm.add_range(Range(start=10, end=15))
    rm.add_range(Range(start=30, end=35))

    # Verify sorted after each add
    ranges = rm.get_ranges()
    for i in range(len(ranges) - 1):
        assert ranges[i].start <= ranges[i + 1].start

    # Add batch of ranges
    rm.add_ranges([Range(start=5, end=8), Range(start=60, end=65), Range(start=20, end=25)])

    # Verify sorted after batch add
    ranges = rm.get_ranges()
    for i in range(len(ranges) - 1):
        assert ranges[i].start <= ranges[i + 1].start

    # Remove range
    rm.remove_range(Range(start=12, end=13))

    # Verify still sorted after remove
    ranges = rm.get_ranges()
    for i in range(len(ranges) - 1):
        assert ranges[i].start <= ranges[i + 1].start
