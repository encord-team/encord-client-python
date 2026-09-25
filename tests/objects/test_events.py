import pytest

from encord.exceptions import LabelRowError
from encord.objects.common import Shape
from encord.objects.coordinates import (
    EVENT_SHAPES,
    BoundingBoxCoordinates,
    CircleCoordinates,
    CuboidCoordinates,
    EllipseCoordinates,
    PointCoordinate,
    PolylineCoordinates,
    RotatableBoundingBoxCoordinates,
    zeroed_coordinates,
)
from encord.objects.events import (
    LabelDeleteEvent,
    LabelUpsertEvent,
    event_ranges,
    prune_dangling_deletes,
    resolve_event_at,
)
from encord.objects.frames import Range
from encord.objects.spaces.annotation.base_annotation import _AnnotationMetadata

BOX = BoundingBoxCoordinates(height=0.1, width=0.1, top_left_x=0.2, top_left_y=0.2)
BOX_2 = BoundingBoxCoordinates(height=0.3, width=0.3, top_left_x=0.4, top_left_y=0.4)
ZERO_BOX = BoundingBoxCoordinates(height=0, width=0, top_left_x=0, top_left_y=0)


def upsert(frame: int, coords=BOX) -> LabelUpsertEvent:
    return LabelUpsertEvent(frame=frame, coordinates=coords, metadata=_AnnotationMetadata())


def delete(frame: int) -> LabelDeleteEvent:
    return LabelDeleteEvent(frame=frame, metadata=_AnnotationMetadata())


# ---- resolve_event_at


def test_no_events_resolves_to_none():
    assert resolve_event_at([], 5) is None


def test_before_first_event_is_absent():
    assert resolve_event_at([upsert(10)], 9) is None


def test_exact_upsert_frame_resolves_to_that_event():
    event = upsert(10)
    assert resolve_event_at([event], 10) is event


def test_frame_between_events_holds_previous_upsert():
    first, second = upsert(10), upsert(20, BOX_2)
    assert resolve_event_at([first, second], 15) is first
    assert resolve_event_at([first, second], 20) is second
    assert resolve_event_at([first, second], 1_000_000) is second


def test_delete_frame_and_after_are_absent():
    events = [upsert(10), delete(20)]
    assert resolve_event_at(events, 19) is events[0]
    assert resolve_event_at(events, 20) is None
    assert resolve_event_at(events, 21) is None


def test_upsert_after_delete_reappears():
    events = [upsert(10), delete(20), upsert(30, BOX_2)]
    assert resolve_event_at(events, 25) is None
    assert resolve_event_at(events, 30) is events[2]
    assert resolve_event_at(events, 99) is events[2]


# ---- event_ranges


def test_no_events_no_ranges():
    assert event_ranges([]) == []


def test_trailing_upsert_is_unsupported():
    with pytest.raises(LabelRowError, match="events end on an `upsert` at frame `10`"):
        event_ranges([upsert(10)])


def test_trailing_upsert_after_a_closed_range_is_unsupported():
    with pytest.raises(LabelRowError, match="events end on an `upsert` at frame `30`"):
        event_ranges([upsert(10), delete(20), upsert(30)])


def test_delete_closes_range_on_frame_before_itself():
    assert event_ranges([upsert(10), delete(20)]) == [Range(10, 19)]


def test_consecutive_upserts_share_one_range():
    assert event_ranges([upsert(10), upsert(15), delete(20)]) == [Range(10, 19)]


def test_multiple_ranges():
    events = [upsert(10), delete(20), upsert(30), delete(40), upsert(50), delete(101)]
    assert event_ranges(events) == [
        Range(10, 19),
        Range(30, 39),
        Range(50, 100),
    ]


def test_leading_delete_is_ignored():
    assert event_ranges([delete(5), upsert(10), delete(20)]) == [Range(10, 19)]


# ---- prune_dangling_deletes


def test_nothing_to_prune():
    assert prune_dangling_deletes([upsert(10), delete(20)]) == []


def test_leading_delete_is_dangling():
    assert prune_dangling_deletes([delete(5), upsert(10)]) == [5]


def test_delete_after_delete_is_dangling():
    assert prune_dangling_deletes([upsert(10), delete(20), delete(30)]) == [30]


def test_only_deletes_all_dangling():
    assert prune_dangling_deletes([delete(1), delete(2)]) == [1, 2]


# ---- zeroed_coordinates


@pytest.mark.parametrize(
    "shape, expected",
    [
        (Shape.BOUNDING_BOX, BoundingBoxCoordinates(height=0, width=0, top_left_x=0, top_left_y=0)),
        (
            Shape.ROTATABLE_BOUNDING_BOX,
            RotatableBoundingBoxCoordinates(height=0, width=0, top_left_x=0, top_left_y=0, theta=0),
        ),
        (Shape.POINT, PointCoordinate(x=0, y=0)),
        (Shape.CIRCLE, CircleCoordinates(center_x=0, center_y=0, radius=0, stretch=0, theta=0)),
        (Shape.ELLIPSE, EllipseCoordinates(center_x=0, center_y=0, rx=0, ry=0, theta=0)),
        (Shape.POLYLINE, PolylineCoordinates(values=[])),
        (Shape.CUBOID, CuboidCoordinates(position=(0, 0, 0), orientation=(0, 0, 0), size=(0, 0, 0))),
    ],
)
def test_supported_shapes(shape, expected):
    assert zeroed_coordinates(shape) == expected


@pytest.mark.parametrize(
    "shape",
    [
        Shape.POLYGON,
        Shape.SKELETON,
        Shape.BITMASK,
        Shape.SEGMENTATION,
        Shape.CUBOID_2D,
        Shape.AUDIO,
        Shape.TIME_RANGE,
        Shape.TEXT,
    ],
)
def test_unsupported_shapes_raise(shape):
    with pytest.raises(LabelRowError):
        zeroed_coordinates(shape)


@pytest.mark.parametrize("shape", list(Shape))
def test_event_shapes_match_zeroed_coordinates(shape):
    if shape in EVENT_SHAPES:
        zeroed_coordinates(shape)
    else:
        with pytest.raises(LabelRowError):
            zeroed_coordinates(shape)
