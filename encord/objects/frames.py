"""
---
title: "Objects - Frames"
slug: "sdk-ref-objects-frames"
hidden: false
metadata:
  title: "Objects - Frames"
  description: "Encord SDK Objects - Frames."
category: "64e481b57b6027003f20aaa0"
---
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, List, Union, cast


@dataclass
class Range:
    """
    A class representing a range with a start and end value.

    Attributes:
        start (int): The starting value of the range.
        end (int): The ending value of the range.
    """

    start: int
    end: int

    def __repr__(self):
        return f"({self.start}:{self.end})"


Ranges = List[Range]
FramesList = List[int]
Frames = Union[int, FramesList, Range, Ranges]


def frame_to_range(frame: int) -> Range:
    """
    Convert a single frame to a Range.

    Args:
        frame (int): The single frame to be converted.

    Returns:
        Range: A Range object with both start and end set to the input frame.
    """
    return Range(frame, frame)


def frames_to_ranges(frames: Collection[int]) -> Ranges:
    """
    Create a sorted list (in ascending order) of non-overlapping run-length encoded ranges from a collection of frames.

    Args:
        frames (Collection[int]): A collection of integers representing frames.

    Returns:
        Ranges: A list of Range objects representing the non-overlapping ranges.
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
    Convert a list of Range objects to a list of lists (run-length encoded) of integers.

    Args:
        ranges (Ranges): A list of Range objects.

    Returns:
        List[List[int]]: A list of lists where each inner list contains two integers, the start and end of a range.
    """
    return [[r.start, r.end] for r in ranges]


def range_to_ranges(range_: Range) -> Ranges:
    """
    Convert a single Range to a list of Ranges.

    Args:
        range_ (Range): The single Range to be converted.

    Returns:
        Ranges: A list containing the input Range as its only element.
    """
    return [range_]


def range_to_frames(range_: Range) -> List[int]:
    """
    Convert a single Range (run-length encoded) to a list of integers.

    Args:
        range_ (Range): The single Range to be converted.

    Returns:
        List[int]: A list of integers representing the frames within the range.
    """
    return list(range(range_.start, range_.end + 1))


def ranges_to_frames(range_list: Ranges) -> List[int]:
    """
    Convert a list of Ranges (run-length encoded) to a list of integers.

    Args:
        range_list (Ranges): A list of Range objects.

    Returns:
        List[int]: A sorted list of integers representing all frames within the ranges.
    """
    frames = set()
    for range_ in range_list:
        frames |= set(range_to_frames(range_))
    return sorted(list(frames))


def ranges_list_to_ranges(range_list: List[List[int]]) -> Ranges:
    """
    Convert a list of lists (run-length encoded) of integers to a list of Range objects.

    Args:
        range_list (List[List[int]]): A list of lists where each inner list contains two integers, the start and end of a range.

    Returns:
        Ranges: A list of Range objects created from the input list of lists.
    """
    return [Range(start, end) for start, end in range_list]


def frames_class_to_frames_list(frames_class: Frames) -> List[int]:
    """
    Convert a Frames class (which can be an int, a list of ints, a Range, or a list of Ranges) to a list of integers.

    Args:
        frames_class (Frames): A Frames class which can be a single int, a list of ints, a Range object, or a list of Range objects.

    Returns:
        List[int]: A sorted list of integers representing all frames within the input Frames class.

    Raises:
        RuntimeError: If the input frames_class is of an unexpected type.
    """
    if isinstance(frames_class, int):
        return [frames_class]
    elif isinstance(frames_class, Range):
        return range_to_frames(frames_class)
    elif isinstance(frames_class, list):
        if all(isinstance(x, int) for x in frames_class):
            return sorted(list(set(cast(List[int], frames_class))))
        elif all(isinstance(x, Range) for x in frames_class):
            return ranges_to_frames(cast(List[Range], frames_class))

    raise RuntimeError("Unexpected type for frames.")
