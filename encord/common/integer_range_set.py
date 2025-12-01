import bisect
import sys
from typing import List, Optional, Tuple


class IntegerRangeSet:
    def __init__(self) -> None:
        self._ranges: List[Tuple[int, int]] = []

    def add(self, start: int, end: int) -> None:
        if start > end:
            raise ValueError(f"Start of range {start} must not be greater than end {end}.")

        # 1. Find Merge Window
        i = bisect.bisect_left(self._ranges, (start, end))
        if i > 0 and self._ranges[i - 1][1] >= start - 1:
            i -= 1
            start = self._ranges[i][0]

        j = bisect.bisect_right(self._ranges, (end + 1, sys.maxsize))
        if j > i:
            end = max(end, self._ranges[j - 1][1])

        # 2. Bulk Replace
        self._ranges[i:j] = [(start, end)]

    def intersection(self, start: int, end: int) -> Optional[List[Tuple[int, int]]]:
        """
        Returns a list of overlapping tuples or None.
        Complexity: O(log N + K) where K is the number of overlapping fragments.
        """
        if start > end or not self._ranges:
            return None

        # 1. Define Search Window
        # We only need to check ranges that could possibly overlap.
        # Start Index (lo): The range immediately before where 'start' would fit.
        # End Index (hi): The first range that starts strictly AFTER 'end'.
        lo = bisect.bisect_right(self._ranges, (start, sys.maxsize)) - 1
        hi = bisect.bisect_right(self._ranges, (end, sys.maxsize))

        # Ensure lo isn't negative (if start is smaller than the very first range)
        lo = max(0, lo)

        overlaps: List[Tuple[int, int]] = []

        # 2. Iterate only the relevant slice
        for i in range(lo, hi):
            r_start, r_end = self._ranges[i]

            # Calculate mathematical intersection: [max(starts), min(ends)]
            o_start = max(start, r_start)
            o_end = min(end, r_end)

            # If valid range, it's an overlap
            if o_start <= o_end:
                overlaps.append((o_start, o_end))

        return overlaps

    def remove(self, start: int, end: int) -> None:
        """Removes a range, splitting or deleting existing ranges."""
        if start > end:
            return

        # 1. Find Search Window
        # i: The first range that *could* overlap (starts before the removal ends)
        # j: The first range that definitely starts *after* the removal ends
        i = bisect.bisect_right(self._ranges, (start, sys.maxsize)) - 1
        i = max(0, i)
        j = bisect.bisect_right(self._ranges, (end, sys.maxsize))

        new_ranges = []

        # 2. Iterate only the affected slice
        for k in range(i, j):
            r_start, r_end = self._ranges[k]

            # Optimization: If this range is entirely to the left, keep it as is.
            # (This happens because our 'i' search is slightly loose)
            if r_end < start:
                new_ranges.append((r_start, r_end))
                continue

            # Check for Left Survivor (Range starts before removal starts)
            if r_start < start:
                new_ranges.append((r_start, start - 1))

            # Check for Right Survivor (Range ends after removal ends)
            if r_end > end:
                new_ranges.append((end + 1, r_end))

        # 3. Bulk Replace the affected slice with the survivors
        self._ranges[i:j] = new_ranges

    def clear(self) -> None:
        self._ranges = []

    def __repr__(self) -> str:
        return f"IntegerRangeSet({self._ranges})"
