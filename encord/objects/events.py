from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from typing import ClassVar, List, Literal, Optional, Sequence, Union

from encord.exceptions import LabelRowError
from encord.objects.common import Shape
from encord.objects.coordinates import EventCoordinates
from encord.objects.frames import Range, Ranges
from encord.objects.interpolation import InterpolationMode, interpolate
from encord.objects.spaces.annotation.base_annotation import _AnnotationMetadata

EventKind = Literal["upsert", "delete"]
"""What a stored entry in an event-based label row asserts from its frame onward.

An event-based row (a continuous scene, see :attr:`~encord.objects.LabelRowV2.is_event_based`) stores sparse
events at nanosecond offsets rather than labels on a frame grid:

- ``"upsert"``: the object exists with this geometry until its next event. An untagged entry reads as an upsert.
- ``"delete"``: the object does not exist until a later upsert. Carries placeholder geometry nobody reads.
"""


@dataclass(frozen=True)
class _LabelEventBase:
    """An event defining an object in a label row.

    Attributes:
        frame: The frame the event occurs at. Frames are in nanoseconds, offset relative to the start of the
            scene. For MCAP scenes the start is the start time in the MCAP summary if present, otherwise the
            log time of the first message of any type.
        metadata: Provenance and confidence of the stored entry.
    """

    frame: int
    metadata: _AnnotationMetadata


@dataclass(frozen=True)
class LabelUpsertEvent(_LabelEventBase):
    """The object exists from ``frame`` until its next event.

    Unless ``interpolation`` is ``"hold"``, the geometry runs into the next event's if that event is an upsert.
    If the next event is a ``delete``, or there is none, it holds.
    """

    coordinates: EventCoordinates
    interpolation: InterpolationMode = "hold"

    kind: ClassVar[Literal["upsert"]] = "upsert"


@dataclass(frozen=True)
class LabelDeleteEvent(_LabelEventBase):
    """The object does not exist from ``frame`` until a later upsert.

    A delete carries no geometry, there are no ``coordinates`` to read.
    """

    kind: ClassVar[Literal["delete"]] = "delete"


LabelEvent = Union[LabelUpsertEvent, LabelDeleteEvent]
"""One stored event: narrow on ``kind``, or with ``isinstance``, to reach an upsert's ``coordinates``."""


def resolve_event_at(events: Sequence[LabelEvent], frame: int) -> Optional[LabelEvent]:
    """The event holding over ``frame``, or None where the object does not exist.

    Args:
        events: The object's events sorted by frame ascending.
        frame: The frame to resolve.

    Returns:
        The last upsert at or before ``frame``, unless the last event at or before ``frame`` is a delete.
    """
    frames = [event.frame for event in events]
    index = bisect_right(frames, frame) - 1
    if index < 0:
        return None
    preceding = events[index]
    if preceding.kind == "delete":
        return None
    return preceding


def _preceding_index(events: Sequence[LabelEvent], frame: int) -> int:
    return bisect_right([event.frame for event in events], frame) - 1


def interpolation_target(events: Sequence[LabelEvent], index: int) -> Optional[LabelUpsertEvent]:
    """What an interpolating upsert at ``events[index]`` runs to: the next event, if it is an upsert.

    None where the next event is a delete or there is none: the upsert then holds until that delete.
    """
    following = events[index + 1] if index + 1 < len(events) else None
    return following if isinstance(following, LabelUpsertEvent) else None


def interpolated_coordinates_at(
    shape: Shape, start: LabelUpsertEvent, target: Optional[LabelUpsertEvent], frame: int
) -> Optional[EventCoordinates]:
    """What ``start`` shows at ``frame`` on its way to ``target``, or None where it holds.

    The fraction is over time, so unevenly spaced keyframes move at a constant speed.
    """
    if target is None or start.interpolation == "hold" or not start.frame < frame < target.frame:
        return None
    fraction = (frame - start.frame) / (target.frame - start.frame)
    return interpolate(start.interpolation, shape, start.coordinates, target.coordinates, fraction)


def inherited_interpolation(events: Sequence[LabelEvent], frame: int) -> InterpolationMode:
    """The mode a write at ``frame`` takes when none is given: that of the upsert it replaces or splits, so both
    halves of a split stretch keep running. ``hold`` over a delete or where the object is absent."""
    index = _preceding_index(events, frame)
    if index < 0:
        return "hold"
    preceding = events[index]
    return preceding.interpolation if isinstance(preceding, LabelUpsertEvent) else "hold"


def stranded_interpolations(events: Sequence[LabelEvent]) -> List[int]:
    """The frames of upserts that interpolate but have nothing to run to: no upsert directly follows them."""
    return [
        event.frame
        for index, event in enumerate(events)
        if isinstance(event, LabelUpsertEvent)
        and event.interpolation != "hold"
        and interpolation_target(events, index) is None
    ]


def check_events_terminated(events: Sequence[LabelEvent], *, object_hash: Optional[str] = None) -> None:
    """Raise unless every stretch the events open is closed by a delete.

    A trailing upsert is a dangling stretch: the object is present from it with no end. The editor never writes
    one — an object running to the end of the timeline is closed on the frame after it — so it is not a layout
    the SDK stores or loads. Half-built objects are allowed to dangle in memory while a caller assembles them;
    this is checked at the two points where the row meets stored labels, parsing them and writing them back out.

    Args:
        events: The object's stored events, sorted by frame ascending.
        object_hash: The object the events belong to, named in the error.

    Raises:
        LabelRowError: If the events end on an upsert.
    """
    if not events or events[-1].kind == "delete":
        return
    subject = "This object's" if object_hash is None else f"Object `{object_hash}`:"
    raise LabelRowError(
        f"{subject} events end on an `upsert` at frame `{events[-1].frame}`, leaving it present with no end. "
        f"Event-based rows terminate every object with a `delete`, so a dangling upsert is an unsupported data "
        f"layout. If the object is meant to be static — present to the end of the timeline — insert the "
        f"`delete` one past the end, at the last nanosecond + 1."
    )


def event_ranges(events: Sequence[LabelEvent]) -> Ranges:
    """The closed ranges an object is present over.

    Each upsert following absence opens a range; the next delete closes it on the frame before itself. Every
    range is closed: an object that runs to the end of the timeline is terminated by a delete on the frame
    after it.

    Args:
        events: The object's events sorted by frame ascending.

    Raises:
        LabelRowError: If the events end on an upsert, leaving a range with no closing delete.
    """
    check_events_terminated(events)

    ranges: Ranges = []
    start: Optional[int] = None
    for event in events:
        if event.kind == "upsert":
            if start is None:
                start = event.frame
        elif start is not None:
            ranges.append(Range(start, event.frame - 1))
            start = None

    return ranges


def events_intersect(events: Sequence[LabelEvent], start: int, end: int) -> bool:
    """Whether the object is present anywhere in ``[start, end]`` (both inclusive).

    Args:
        events: The object's events sorted by frame ascending.
        start: First frame of the window.
        end: Last frame of the window.

    Raises:
        LabelRowError: If the events end on an upsert, leaving a range with no closing delete.
    """
    window = Range(start, end)
    return any(range_.overlaps(window) for range_ in event_ranges(events))


def prune_dangling_deletes(events: Sequence[LabelEvent]) -> List[int]:
    """Frames of delete events that terminate nothing.

    A delete is dangling when it is the first event or directly follows another delete.

    Args:
        events: The object's events sorted by frame ascending.
    """
    dangling: List[int] = []
    previous_kind: Optional[EventKind] = None
    for event in events:
        if event.kind == "delete" and previous_kind != "upsert":
            dangling.append(event.frame)
            continue
        previous_kind = event.kind
    return dangling
