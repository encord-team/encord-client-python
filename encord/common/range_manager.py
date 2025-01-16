from typing import Iterable, List, Optional, Set, Union, cast

from encord.objects.frames import Frames, Range, Ranges


class RangeManager:
    """Range Manager class to hold a list of frame ranges, and operate on them."""

    def __init__(self, frame_class: Optional[Frames] = None):
        self.ranges: Ranges = []
        if isinstance(frame_class, int):
            self.add_range(Range(start=frame_class, end=frame_class))
        elif isinstance(frame_class, Range):
            self.add_range(frame_class)
        elif isinstance(frame_class, list):
            if all(isinstance(x, int) for x in frame_class):
                for frame in frame_class:
                    self.add_range(Range(start=cast(int, frame), end=cast(int, frame)))
            elif all(isinstance(x, Range) for x in frame_class):
                self.add_ranges(cast(Ranges, frame_class))
        elif frame_class is None:
            self.ranges = []
        else:
            raise RuntimeError("Unexpected type for frames.")

    def add_range(self, new_range: Range) -> None:
        """Add a range, merging any overlapping ranges."""
        if not self.ranges:
            self.ranges.append(new_range)
            return

        merged_ranges = []

        # Sort ranges based on the start of each range
        for existing_range in sorted(self.ranges, key=lambda r: r.start):
            if existing_range.overlaps(new_range):
                new_range.merge(existing_range)
            else:
                merged_ranges.append(existing_range)

        merged_ranges.append(new_range)  # Add the new (merged) range
        self.ranges = sorted(merged_ranges, key=lambda r: r.start)

    def add_ranges(self, new_ranges: Ranges) -> None:
        """Add multiple ranges."""
        for new_range in new_ranges:
            self.add_range(new_range)

    def remove_range(self, range_to_remove: Range) -> None:
        """Remove a specific range."""
        new_ranges = []

        for r in self.ranges:
            if not r.overlaps(range_to_remove):
                # No overlap
                new_ranges.append(r)
            else:
                # Partial overlap: split if needed
                if r.start < range_to_remove.start:
                    new_ranges.append(Range(r.start, range_to_remove.start - 1))
                if r.end > range_to_remove.end:
                    new_ranges.append(Range(range_to_remove.end + 1, r.end))

        self.ranges = new_ranges

    def remove_ranges(self, ranges_to_remove: Ranges) -> None:
        """Remove multiple ranges."""
        for r in ranges_to_remove:
            self.remove_range(r)

    def clear_ranges(self) -> None:
        """Clear all ranges."""
        self.ranges = []

    def get_ranges(self) -> Ranges:
        """Return the sorted list of merged ranges."""
        copied_ranges = [range.copy() for range in self.ranges]

        return sorted(copied_ranges, key=lambda r: r.start)

    def get_ranges_as_frames(self) -> Set[int]:
        """Returns set of intersecting frames"""
        res = set()
        for r in self.ranges:
            res.update(list(range(r.start, r.end + 1)))

        return res

    def intersection(self, other_frame_class: Frames) -> Ranges:
        """Returns list of intersecting ranges"""
        intersection_ranges: Ranges = []
        other_range_manager = RangeManager(other_frame_class)
        other_ranges = other_range_manager.get_ranges()
        current_ranges = self.get_ranges()

        # If either list of ranges is empty, there is no intersection
        if len(other_ranges) == 0 or len(current_ranges) == 0:
            return []

        # Since ranges are sorted, we can use 2-pointer method to find intersections
        current_index, other_index = 0, 0

        while current_index < len(current_ranges) and other_index < len(other_ranges):
            current_range = current_ranges[current_index]
            other_range = other_ranges[other_index]

            if current_range.overlaps(other_range):
                intersect_start = max(current_range.start, other_range.start)
                intersect_end = min(current_range.end, other_range.end)
                intersection_ranges.append(Range(intersect_start, intersect_end))

            # Move pointer for the range that ends first
            if current_range.end < other_range.end:
                current_index += 1
            else:
                other_index += 1

        return intersection_ranges
