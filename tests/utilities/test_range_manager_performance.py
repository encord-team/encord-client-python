"""Performance regression tests for RangeManager."""

import time

import pytest

from encord.common.range_manager import RangeManager
from encord.objects.frames import Range

NUM_RANGES = 100_000

# Performance thresholds (in seconds)
# These are based on current performance and should alert if there's regression
ADD_RANGES_THRESHOLD = 1
ADD_RANGE_SEQUENTIAL_THRESHOLD = 1
INIT_FRAMES_THRESHOLD = 1
GET_RANGES_THRESHOLD = 1
INTERSECTION_THRESHOLD = 1
REMOVE_RANGE_THRESHOLD = 1


def test_add_ranges_performance_100k():
    """Test add_ranges() performance with 100,000 non-overlapping ranges."""
    rm = RangeManager()
    ranges = [Range(i * 10, i * 10 + 5) for i in range(NUM_RANGES)]

    start = time.perf_counter()
    rm.add_ranges(ranges)
    elapsed = time.perf_counter() - start

    print(f"\nadd_ranges(100k): {elapsed:.3f}s")
    assert len(rm.get_ranges()) == NUM_RANGES
    assert elapsed < ADD_RANGES_THRESHOLD, f"add_ranges took {elapsed:.3f}s, threshold is {ADD_RANGES_THRESHOLD}s"


def test_add_range_sequential_performance():
    """Test sequential add_range() calls performance."""
    rm = RangeManager()
    ranges = [Range(i * 10, i * 10 + 5) for i in range(NUM_RANGES)]

    start = time.perf_counter()
    for r in ranges:
        rm.add_range(r)
    elapsed = time.perf_counter() - start

    print(f"\nadd_range() × {NUM_RANGES}: {elapsed:.3f}s")
    assert len(rm.get_ranges()) == NUM_RANGES
    assert elapsed < ADD_RANGE_SEQUENTIAL_THRESHOLD, (
        f"Sequential add_range took {elapsed:.3f}s, threshold is {ADD_RANGE_SEQUENTIAL_THRESHOLD}s"
    )


def test_initialization_performance_100k():
    """Test initialization with 100,000 frames."""

    frames = list(range(NUM_RANGES))

    start = time.perf_counter()
    rm = RangeManager(frame_class=frames)
    elapsed = time.perf_counter() - start

    print(f"\nRangeManager(10k frames): {elapsed:.3f}s")
    # Should create one contiguous range
    assert len(rm.get_ranges()) == 1
    assert elapsed < INIT_FRAMES_THRESHOLD, f"Initialization took {elapsed:.3f}s, threshold is {INIT_FRAMES_THRESHOLD}s"


def test_initialization_performance_sparse():
    """Test initialization with 10,000 sparse frames."""
    # Every 10th frame - should create 10k separate ranges
    frames = list(range(0, NUM_RANGES, 10))

    start = time.perf_counter()
    rm = RangeManager(frame_class=frames)
    elapsed = time.perf_counter() - start

    print(f"\nRangeManager(10k sparse frames): {elapsed:.3f}s")
    assert len(rm.get_ranges()) == 10_000
    assert elapsed < INIT_FRAMES_THRESHOLD, (
        f"Sparse initialization took {elapsed:.3f}s, threshold is {INIT_FRAMES_THRESHOLD}s"
    )


def test_get_ranges_performance():
    """Test get_ranges() call performance with 10k ranges."""
    rm = RangeManager()
    rm.add_ranges([Range(i * 10, i * 10 + 5) for i in range(NUM_RANGES)])

    start = time.perf_counter()
    rm.get_ranges()
    elapsed = time.perf_counter() - start

    print(f"\nget_ranges() × 10k: {elapsed:.3f}s")
    assert elapsed < GET_RANGES_THRESHOLD, f"get_ranges took {elapsed:.3f}s, threshold is {GET_RANGES_THRESHOLD}s"


def test_intersection_performance_10k():
    """Test intersection performance with 10k ranges."""
    rm = RangeManager(frame_class=[Range(i * 10, i * 10 + 5) for i in range(NUM_RANGES)])
    other_ranges = [Range(i * 10 + 3, i * 10 + 8) for i in range(NUM_RANGES)]

    start = time.perf_counter()
    result = rm.intersection(other_ranges)
    elapsed = time.perf_counter() - start

    print(f"\nintersection(10k ranges): {elapsed:.3f}s")
    # Should have overlaps
    assert len(result) > 0
    assert elapsed < INTERSECTION_THRESHOLD, f"Intersection took {elapsed:.3f}s, threshold is {INTERSECTION_THRESHOLD}s"


def test_remove_range_performance():
    """Test remove_range() performance with 1000 removals."""
    # Create ranges with gaps to prevent merging
    rm = RangeManager(frame_class=[Range(i * 100, i * 100 + 50) for i in range(NUM_RANGES)])

    start = time.perf_counter()
    for i in range(1000):
        # Remove middle portion of each range, which will split it
        rm.remove_range(Range(i * 100 + 20, i * 100 + 30))
    elapsed = time.perf_counter() - start

    print(f"\nremove_range() × 1000: {elapsed:.3f}s")
    # After splitting 1000 ranges, we should have more ranges
    # Original: 10,000 ranges, split 1000 of them → ~11,000 ranges
    assert len(rm.get_ranges()) > 10_500
    assert elapsed < REMOVE_RANGE_THRESHOLD, f"remove_range took {elapsed:.3f}s, threshold is {REMOVE_RANGE_THRESHOLD}s"


@pytest.mark.parametrize("num_ranges", [1_000, 10_000, 50_000])
def test_scalability_add_ranges(num_ranges):
    """Test that add_ranges() scales reasonably with input size."""
    rm = RangeManager()
    ranges = [Range(i * 10, i * 10 + 5) for i in range(num_ranges)]

    start = time.perf_counter()
    rm.add_ranges(ranges)
    elapsed = time.perf_counter() - start

    # Should scale roughly linearly (O(n log n))
    # Allow 2ms per 1000 ranges as a rough guideline
    expected_max = (num_ranges / 1000) * 0.02
    print(f"\nadd_ranges({num_ranges:,}): {elapsed:.3f}s (max: {expected_max:.3f}s)")

    assert len(rm.get_ranges()) == num_ranges
    assert elapsed < expected_max, f"Scalability issue: {elapsed:.3f}s > {expected_max:.3f}s for {num_ranges} ranges"
