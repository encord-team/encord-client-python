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
    assert actual_ranges[1].end == 20
    assert actual_ranges[2].start == 21
    assert actual_ranges[2].end == 22


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
