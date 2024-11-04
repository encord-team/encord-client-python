from typing import Union, Optional, Iterable, Set

from encord.objects.frames import Ranges, Range


class RangeManager:
    def __init__(self, ranges: Optional[Ranges] = None):
        self.ranges: Ranges = []
        if ranges:
            for r in ranges:
                self.add_range(r)

    def add_range(self, new_range: Range):
        """Add a range, merging any overlapping or contiguous ranges."""
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

    def add_ranges(self, new_ranges: Ranges):
        """Add multiple ranges"""
        for new_range in new_ranges:
            self.add_range(new_range)

    def update_range(self, old_range: Range, new_range: Range):
        """Update an existing range by removing the old one and adding the new one."""
        self.remove_range(old_range)
        self.add_range(new_range)

    def remove_range(self, range_to_remove: Range):
        """Remove a specific range."""
        new_ranges = []

        for r in self.ranges:
            if r.end < range_to_remove.start or r.start > range_to_remove.end:
                # No overlap
                new_ranges.append(r)
            else:
                # Partial overlap: split if needed
                if r.start < range_to_remove.start:
                    new_ranges.append(Range(r.start, range_to_remove.start - 1))
                if r.end > range_to_remove.end:
                    new_ranges.append(Range(range_to_remove.end + 1, r.end))

        self.ranges = new_ranges

    def get_ranges(self):
        """Return the sorted list of merged ranges."""
        return sorted(self.ranges, key=lambda r: r.start)

    def get_ranges_as_frames(self) -> Set[int]:
        """Returns set of intersecting frames"""
        res = set()
        for r in self.ranges:
            res.update(list(range(r.start, r.end + 1)))

        return res

    def intersection(self, other_frames: Iterable[int]) -> Set[int]:
        """Returns set of intersecting frames"""
        current_frames = self.get_ranges_as_frames()
        return current_frames.intersection(other_frames)

# Example usage:
ranges = [Range(start=1, end=5), Range(start=10, end=20), Range(start=25, end=30)]
manager = RangeManager(ranges)
print("Initial Ranges:", manager.get_ranges())  # Should show merged initial ranges

manager.add_range(Range(start=3, end=12))
print("After Adding [3, 12]:", manager.get_ranges())  # Should merge overlapping ranges

manager.update_range(Range(start=20, end=25), Range(start=22, end=30))
print("After Updating [20, 25] to [22, 30]:", manager.get_ranges())  # Should reflect update

manager.remove_range(Range(start=10, end=12))
print("After Removing [10, 12]:", manager.get_ranges())
