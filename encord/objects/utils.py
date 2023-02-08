from __future__ import annotations

import base64
import re
import uuid
from dataclasses import dataclass
from typing import Any, Iterable, List, Optional, TypeVar, Union


def _decode_nested_uid(nested_uid: list) -> str:
    return ".".join([str(uid) for uid in nested_uid])


def short_uuid_str() -> str:
    """This is being used as a condensed uuid."""
    return base64.b64encode(uuid.uuid4().bytes[:6]).decode("utf-8")


@dataclass
class Range:
    start: int
    end: int


Ranges = List[Range]
Frames = Union[int, Range, Ranges]


def frame_to_range(frame: int) -> Range:
    return Range(frame, frame)


def frames_to_ranges(frames: Iterable[int]) -> Ranges:
    """
    Create a sorted list (in ascending order) of run length encoded ranges of the frames. The Ranges will not
    be overlapping.
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
    return [[r.start, r.end] for r in ranges]


def range_to_ranges(range_: Range) -> Ranges:
    return [range_]


def range_to_frames(range_: Range) -> List[int]:
    return [i for i in range(range_.start, range_.end + 1)]


def ranges_to_frames(range_list: Ranges) -> List[int]:
    frames = set()
    for range_ in range_list:
        frames |= set(range_to_frames(range_))
    return sorted(list(frames))


def ranges_list_to_ranges(range_list: List[List[int]]) -> Ranges:
    return [Range(start, end) for start, end in range_list]


def frames_class_to_frames_list(frames_class: Frames) -> List[int]:
    if isinstance(frames_class, int):
        return [frames_class]
    elif isinstance(frames_class, Range):
        return range_to_frames(frames_class)
    elif isinstance(frames_class, list):
        return ranges_to_frames(frames_class)
    else:
        raise RuntimeError("Unexpected type for frames.")


def _lower_snake_case(s: str):
    return s.lower().replace(" ", "_")


def check_type(obj: object, type_: Any) -> None:
    if not does_type_match(obj, type_):
        raise TypeError(f"Expected {type_}, got {type(obj)}")


def does_type_match(obj: object, type_: Any) -> bool:
    if type_ is None:
        return True
    if not isinstance(obj, type_):
        return False
    return True


T = TypeVar("T")


def filter_by_type(objects: List[object], type_: Optional[T]) -> List[T]:
    return [object_ for object_ in objects if does_type_match(object_, type_)]


def is_valid_email(email: str) -> bool:
    """
    Validate that an email is a valid one
    """
    regex = r"[^@]+@[^@]+\.[^@]+"
    return bool(re.match(regex, email))


def check_email(email: str) -> None:
    if not is_valid_email(email):
        raise ValueError("Invalid email address")
