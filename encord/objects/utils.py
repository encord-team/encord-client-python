from __future__ import annotations

import base64
import uuid
from dataclasses import dataclass
from typing import Any, List, Union


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


def range_to_ranges(range_: Range) -> Ranges:
    return [range_]


def range_to_frames(range_: Range) -> List[int]:
    return [i for i in range(range_.start, range_.end + 1)]


def ranges_to_frames(range_list: Ranges) -> List[int]:
    frames = set()
    for range_ in range_list:
        frames |= set(range_to_frames(range_))
    return sorted(list(frames))


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
    # DENIS: ^ this can be part of the ontology_attribute maybe?
    # I need to update the docs actually, as they're slightly off.
    return s.lower().replace(" ", "_")


def check_type(obj: object, type_: Any) -> None:
    if type_ is None:
        return
    if not isinstance(obj, type_):
        raise TypeError(f"Expected {type_}, got {type(obj)}")
