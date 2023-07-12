from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, List, Union, cast


@dataclass
class Range:
    start: int
    end: int


Ranges = List[Range]
FramesList = List[int]
Frames = Union[int, FramesList, Range, Ranges]


def frame_to_range(frame: int) -> Range:
    """
    Convert a single frame to a Range.

    Args:
        frame: The single frame
    """
    return Range(frame, frame)


def frames_to_ranges(frames: Collection[int]) -> Ranges:
    """
    Create a sorted list (in ascending order) of run length encoded ranges of the frames. The Ranges will not
    be overlapping.

    Args:
        frames: A collection of integers representing frames
    """
    if len(frames) == 0:
        return []

    ret = []

    frames_sorted = sorted(frames)
    last_value = frames_sorted[0]
    next_range = Range(start=last_value, end=last_value)
    idx = 1
    while idx < len(frames_sorted):
        if frames_sorted[idx] == last_value + 1:
            next_range.end = frames_sorted[idx]
        else:
            ret.append(next_range)
            next_range = Range(frames_sorted[idx], frames_sorted[idx])
        last_value = frames_sorted[idx]
        idx += 1

    ret.append(next_range)
    return ret


def ranges_to_list(ranges: Ranges) -> List[List[int]]:
    """
    Convert a list of Range to a list of lists (run length encoded) of integers.

    Args:
        ranges: A list of Range objects
    """
    return [[r.start, r.end] for r in ranges]


def range_to_ranges(range_: Range) -> Ranges:
    """
    Convert a single Range to a list of Ranges.

    Args:
        range_: The single Range
    """
    return [range_]


def range_to_frames(range_: Range) -> List[int]:
    """
    Convert a single Range (run length encoded) to a list of integers. Useful to flatten out run length encoded
    values.

    Args:
        range_: The single Range
    """
    return [i for i in range(range_.start, range_.end + 1)]


def ranges_to_frames(range_list: Ranges) -> List[int]:
    """
    Convert a list of Ranges (run length encoded) to a list of integers. Useful to flatten out run length encoded
    values.

    Args:
        range_list: A list of Ranges
    """
    frames = set()
    for range_ in range_list:
        frames |= set(range_to_frames(range_))
    return sorted(list(frames))


def ranges_list_to_ranges(range_list: List[List[int]]) -> Ranges:
    """
    Convert a list of lists (run length encoded) of integers to a list of Ranges.

    Args:
        range_list: A list of lists (run length encoded) of integers
    """
    return [Range(start, end) for start, end in range_list]


def frames_class_to_frames_list(frames_class: Frames) -> List[int]:
    """
    Convert a flexible Frames class to a list of integers.

    Args:
        frames_class: A Frames class
    """
    if isinstance(frames_class, int):
        return [frames_class]
    elif isinstance(frames_class, Range):
        return range_to_frames(frames_class)
    elif isinstance(frames_class, list):
        if all([isinstance(x, int) for x in frames_class]):
            return cast(List[int], sorted(list(set(frames_class))))
        elif all([isinstance(x, Range) for x in frames_class]):
            return ranges_to_frames(cast(List[Range], frames_class))
        else:
            raise RuntimeError("Unexpected type for frames.")
    else:
        raise RuntimeError("Unexpected type for frames.")
