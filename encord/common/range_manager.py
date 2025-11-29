from typing import List, Optional, Set, Tuple, cast

from encord.common.integer_range_set import IntegerRangeSet
from encord.objects.frames import Frames, Range, Ranges


class RangeManager:
    """Range Manager implemented using IntegerRangeSet for optimal performance.

    This is a wrapper around IntegerRangeSet that provides the same API as RangeManager
    but with improved performance characteristics.
    """

    def __init__(self, frame_class: Optional[Frames] = None):
        self._range_set = IntegerRangeSet()

        if isinstance(frame_class, int):
            self._range_set.add(frame_class, frame_class)
        elif isinstance(frame_class, Range):
            self._range_set.add(frame_class.start, frame_class.end)
        elif isinstance(frame_class, (list, set)):
            if all(isinstance(x, int) for x in frame_class):
                # Add individual frames
                for frame in frame_class:
                    self._range_set.add(cast(int, frame), cast(int, frame))
            elif all(isinstance(x, Range) for x in frame_class):
                # Add ranges
                for r in cast(Ranges, frame_class):
                    self._range_set.add(r.start, r.end)
        elif frame_class is None:
            pass  # Empty range set
        else:
            raise RuntimeError(f"Unexpected type for frames {type(frame_class)}.")

    @property
    def ranges(self) -> List[Tuple[int, int]]:
        return self._range_set._ranges

    def add_range(self, new_range: Range) -> None:
        """Add a range, merging any overlapping ranges."""
        self._range_set.add(new_range.start, new_range.end)

    def add_ranges(self, new_ranges: Ranges) -> None:
        """Add multiple ranges."""
        for new_range in new_ranges:
            self._range_set.add(new_range.start, new_range.end)

    def remove_range(self, range_to_remove: Range) -> None:
        """Remove a specific range using IntegerRangeSet's native remove method."""
        self._range_set.remove(range_to_remove.start, range_to_remove.end)

    def remove_ranges(self, ranges_to_remove: Ranges) -> None:
        """Remove multiple ranges."""
        for r in ranges_to_remove:
            self.remove_range(r)

    def clear_ranges(self) -> None:
        """Clear all ranges."""
        self._range_set.clear()

    def get_ranges(self) -> Ranges:
        """Return the sorted list of merged ranges."""
        return [Range(start, end) for start, end in self._range_set._ranges]

    def get_ranges_as_frames(self) -> Set[int]:
        """Returns set of intersecting frames."""
        res: Set[int] = set()
        for start, end in self._range_set._ranges:
            res.update(range(start, end + 1))
        return res

    def intersection(self, other_frame_class: Frames) -> Ranges:
        """Returns list of intersecting ranges."""
        # Convert other_frame_class to ranges
        other_manager = RangeManager(other_frame_class)

        if not self._range_set._ranges or not other_manager._range_set._ranges:
            return []

        intersection_ranges: Ranges = []

        # For each range in self, check intersection with other
        for self_start, self_end in self._range_set._ranges:
            overlaps = other_manager._range_set.intersection(self_start, self_end)
            if overlaps:
                for o_start, o_end in overlaps:
                    intersection_ranges.append(Range(o_start, o_end))

        return intersection_ranges
