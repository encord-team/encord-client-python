"""Interpolation between keyframes of an event-based label row.

A non-``hold`` upsert runs into the geometry of the object's next event when that event is an upsert (before a
``delete`` it holds) and nothing is stored in between, so the formulas here are the label: they mirror the editor's
(``cord-frontend`` ``labels/events/linear.ts``, via three.js) and must not change. A new rule is a new mode.
"""

from __future__ import annotations

import math
from typing import Callable, Literal, Mapping, Optional, Tuple

from encord.objects.common import Shape
from encord.objects.coordinates import CuboidCoordinates, EventCoordinates, PointCoordinate, PointCoordinate3D

InterpolationMode = Literal["hold", "linear"]
"""``"hold"``: the geometry stands until the next event (what an unset field means). ``"linear"``: it moves in a
straight line, over time, into the next upsert's."""

INTERPOLATED_CONFIDENCE = 0.99
"""Confidence of a derived frame, matching the editor."""

_Interpolator = Callable[[EventCoordinates, EventCoordinates, float], EventCoordinates]
_Triple = Tuple[float, float, float]
_Quaternion = Tuple[float, float, float, float]  # (x, y, z, w)


def _lerp(start: float, end: float, fraction: float) -> float:
    return start + (end - start) * fraction


def _lerp_triple(start: _Triple, end: _Triple, fraction: float) -> _Triple:
    return (_lerp(start[0], end[0], fraction), _lerp(start[1], end[1], fraction), _lerp(start[2], end[2], fraction))


def _quaternion_from_euler_xyz(angles: _Triple) -> _Quaternion:
    """three.js ``Quaternion.setFromEuler``, order ``XYZ``."""
    c1, c2, c3 = math.cos(angles[0] / 2), math.cos(angles[1] / 2), math.cos(angles[2] / 2)
    s1, s2, s3 = math.sin(angles[0] / 2), math.sin(angles[1] / 2), math.sin(angles[2] / 2)
    return (
        s1 * c2 * c3 + c1 * s2 * s3,
        c1 * s2 * c3 - s1 * c2 * s3,
        c1 * c2 * s3 + s1 * s2 * c3,
        c1 * c2 * c3 - s1 * s2 * s3,
    )


def _slerp(start: _Quaternion, end: _Quaternion, fraction: float) -> _Quaternion:
    """three.js ``Quaternion.slerp``."""
    ax, ay, az, aw = start
    bx, by, bz, bw = end
    dot = ax * bx + ay * by + az * bz + aw * bw
    if dot < 0:
        bx, by, bz, bw = -bx, -by, -bz, -bw
        dot = -dot

    s = 1 - fraction
    t = fraction
    if dot < 0.9995:
        theta = math.acos(dot)
        sin = math.sin(theta)
        s = math.sin(s * theta) / sin
        t = math.sin(t * theta) / sin
        return (ax * s + bx * t, ay * s + by * t, az * s + bz * t, aw * s + bw * t)

    x, y, z, w = ax * s + bx * t, ay * s + by * t, az * s + bz * t, aw * s + bw * t
    length = math.sqrt(x * x + y * y + z * z + w * w)
    if length == 0:
        return (0.0, 0.0, 0.0, 1.0)
    inverse = 1 / length
    return (x * inverse, y * inverse, z * inverse, w * inverse)


def _euler_xyz_from_quaternion(quaternion: _Quaternion) -> _Triple:
    """three.js ``Euler.setFromQuaternion``, order ``XYZ``."""
    x, y, z, w = quaternion
    x2, y2, z2 = x + x, y + y, z + z
    xx, xy, xz = x * x2, x * y2, x * z2
    yy, yz, zz = y * y2, y * z2, z * z2
    wx, wy, wz = w * x2, w * y2, w * z2

    m11 = 1 - (yy + zz)
    m12 = xy - wz
    m13 = xz + wy
    m22 = 1 - (xx + zz)
    m23 = yz - wx
    m32 = yz + wx
    m33 = 1 - (xx + yy)

    euler_y = math.asin(min(max(m13, -1.0), 1.0))
    if abs(m13) < 0.9999999:
        return (math.atan2(-m23, m33), euler_y, math.atan2(-m12, m11))
    return (math.atan2(m32, m22), euler_y, 0.0)


def _slerp_orientation(start: _Triple, end: _Triple, fraction: float) -> _Triple:
    return _euler_xyz_from_quaternion(
        _slerp(_quaternion_from_euler_xyz(start), _quaternion_from_euler_xyz(end), fraction)
    )


def _linear_cuboid(start: EventCoordinates, end: EventCoordinates, fraction: float) -> EventCoordinates:
    assert isinstance(start, CuboidCoordinates) and isinstance(end, CuboidCoordinates)
    return CuboidCoordinates(
        position=_lerp_triple(start.position, end.position, fraction),
        orientation=_slerp_orientation(start.orientation, end.orientation, fraction),
        size=_lerp_triple(start.size, end.size, fraction),
    )


def _linear_point(start: EventCoordinates, end: EventCoordinates, fraction: float) -> EventCoordinates:
    if isinstance(start, PointCoordinate3D) and isinstance(end, PointCoordinate3D):
        return PointCoordinate3D(
            x=_lerp(start.x, end.x, fraction), y=_lerp(start.y, end.y, fraction), z=_lerp(start.z, end.z, fraction)
        )
    assert isinstance(start, PointCoordinate) and isinstance(end, PointCoordinate)
    return PointCoordinate(x=_lerp(start.x, end.x, fraction), y=_lerp(start.y, end.y, fraction))


_INTERPOLATORS: Mapping[str, Mapping[Shape, _Interpolator]] = {
    "linear": {
        Shape.POINT: _linear_point,
        Shape.CUBOID: _linear_cuboid,
    },
}
"""Every non-``hold`` mode and the shapes it is implemented for. Adding a mode or a shape is an entry here."""

INTERPOLATION_MODES: frozenset[str] = frozenset({"hold", *_INTERPOLATORS})

INTERPOLATION_SHAPES: Mapping[str, frozenset[Shape]] = {
    mode: frozenset(interpolators) for mode, interpolators in _INTERPOLATORS.items()
}
"""The shapes each non-``hold`` mode supports. ``hold`` supports every shape."""


def check_interpolation_supported(mode: object, shape: object) -> None:
    """Raise unless ``mode`` is readable on ``shape`` (a :class:`Shape` or its value).

    Raises:
        ValueError: For an unknown mode, or a mode the shape does not support.
    """
    if mode == "hold":
        return
    if mode not in _INTERPOLATORS:
        raise ValueError(f"Unsupported interpolation mode {mode!r}; supported modes are {sorted(INTERPOLATION_MODES)}.")
    shapes = INTERPOLATION_SHAPES[mode]  # type: ignore[index]
    if shape not in shapes and shape not in {s.value for s in shapes}:
        raise ValueError(
            f"Interpolation mode {mode!r} is not supported for shape `{getattr(shape, 'value', shape)}`; it supports "
            f"{sorted(s.value for s in shapes)}."
        )


def interpolate(
    mode: str, shape: Shape, start: EventCoordinates, end: EventCoordinates, fraction: float
) -> Optional[EventCoordinates]:
    """``start`` a ``fraction`` of the way to ``end`` under ``mode``, or None where it holds."""
    interpolator: Optional[_Interpolator] = _INTERPOLATORS.get(mode, {}).get(shape)
    if interpolator is None or type(start) is not type(end):
        return None
    return interpolator(start, end, fraction)
