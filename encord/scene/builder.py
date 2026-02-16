"""Builder API for constructing Encord scene payloads.

Provides a multi-stage builder pattern for assembling scene data without
exposing internal Pydantic definitions. Each stream type has its own
nested builder, and all events support optional timestamps.

**Stages:**

1. Create a :class:`SceneBuilder` and (optionally) configure global settings.
2. Add one or more streams -- each ``add_*_stream`` call returns a nested
   stream builder.
3. Populate streams with events via ``add_event`` / ``add_events``.
4. Call :meth:`SceneBuilder.build` to validate and serialize.

Pose helpers
------------
* :func:`quaternion_pose` -- unit quaternion + translation
* :func:`euler_pose` -- Euler angles (radians) + translation
* :func:`matrix_pose` -- 3x3 rotation matrix + translation
* :func:`affine_transform` -- full 4x4 affine matrix

Intrinsics helpers
------------------
* :func:`intrinsics_simple` -- focal length / principal point (+ optional
  distortion model)
* :func:`intrinsics_advanced` -- full camera / rectification / projection
  matrices

Supported distortion models (pass as ``model=`` string):
``"radial"``, ``"plumb_bob"``, ``"fisheye"``, ``"rational_polynomial"``,
``"pinhole"``, ``"division"``, ``"ucm"``.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Any, Sequence

from encord.exceptions import EncordException

# Internal types -- imported as private, never exposed to the user.
from encord.scene.internal import Direction  # public enum, re-exported
from encord.scene.internal import (
    InputAffineTransform as _InputAffineTransform,
)
from encord.scene.internal import (
    InputEulerRotation as _InputEulerRotation,
)
from encord.scene.internal import (
    InputPosition as _InputPosition,
)
from encord.scene.internal import (
    InputQuaternion as _InputQuaternion,
)
from encord.scene.internal import (
    InputRotationMatrix as _InputRotationMatrix,
)

__all__ = [
    # Public domain types
    "Pose",
    "CompositePose",
    "AffinePose",
    "Rotation",
    "QuaternionRotation",
    "EulerRotation",
    "MatrixRotation",
    "Position",
    "Intrinsics",
    "SimpleIntrinsics",
    "AdvancedIntrinsics",
    # Scene builder
    "SceneBuilder",
    # Stream builders
    "CameraStreamBuilder",
    "FoRStreamBuilder",
    "ImageStreamBuilder",
    "ModelStreamBuilder",
    "PCDStreamBuilder",
    # Pose helpers
    "affine_transform",
    "euler_pose",
    "matrix_pose",
    "quaternion_pose",
    # Intrinsics helpers
    "intrinsics_advanced",
    "intrinsics_simple",
    # Enum
    "Direction",
]


# ===================================================================
# Timestamp
# ===================================================================

Timestamp = int | float | datetime.datetime | datetime.time | None
SerializedTimestamp = int | float | str


def _serialize_timestamp(ts: Timestamp) -> SerializedTimestamp | None:
    if ts is None:
        return None
    if isinstance(ts, datetime.datetime | datetime.time):
        return ts.isoformat()
    return ts


# ===================================================================
# Public domain types -- wrap internal Pydantic models
# ===================================================================


# --- Position ---


@dataclass(slots=True)
class Position:
    """3-D position (translation)."""

    x: float
    y: float
    z: float
    _inner: _InputPosition | None = field(init=False, repr=False, compare=False, default=None)

    def __post_init__(self) -> None:
        self._inner = _InputPosition.model_construct(x=self.x, y=self.y, z=self.z)

    def _to_dict(self) -> dict[str, float]:
        return {"x": self.x, "y": self.y, "z": self.z}


# --- Rotation types ---


@dataclass(slots=True)
class QuaternionRotation:
    """Unit-quaternion rotation."""

    qx: float
    qy: float
    qz: float
    qw: float
    _inner: _InputQuaternion | None = field(init=False, repr=False, compare=False, default=None)

    def __post_init__(self) -> None:
        self._inner = _InputQuaternion.model_construct(x=self.qx, y=self.qy, z=self.qz, w=self.qw)

    def _to_dict(self) -> dict[str, str | float]:
        return {
            "type": "quaternion",
            "qx": self.qx,
            "qy": self.qy,
            "qz": self.qz,
            "qw": self.qw,
        }


@dataclass(slots=True)
class EulerRotation:
    """Euler-angle rotation (radians)."""

    rx: float
    ry: float
    rz: float
    _inner: _InputEulerRotation | None = field(init=False, repr=False, compare=False, default=None)

    def __post_init__(self) -> None:
        self._inner = _InputEulerRotation.model_construct(x=self.rx, y=self.ry, z=self.rz)

    def _to_dict(self) -> dict[str, str | float]:
        return {"type": "euler", "rx": self.rx, "ry": self.ry, "rz": self.rz}


@dataclass(slots=True)
class MatrixRotation:
    """3x3 rotation matrix (9 floats, row-major)."""

    values: tuple[float, float, float, float, float, float, float, float, float]
    _inner: _InputRotationMatrix | None = field(init=False, repr=False, compare=False, default=None)

    def __post_init__(self) -> None:
        self._inner = _InputRotationMatrix.model_construct(root=self.values)

    def _to_dict(self) -> dict[str, str | list[float]]:
        return {"type": "rotation_matrix", "values": list(self.values)}


Rotation = QuaternionRotation | EulerRotation | MatrixRotation


# --- Pose types ---


@dataclass(slots=True)
class CompositePose:
    """Rotation + position pair."""

    rotation: Rotation
    position: Position

    def _to_dict(self) -> dict[str, Any]:
        return {
            "rotation": self.rotation._to_dict(),
            "position": self.position._to_dict(),
        }


@dataclass(slots=True)
class AffinePose:
    """4x4 affine transform matrix (16 floats, row-major)."""

    matrix: tuple[
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
    ]
    _inner: _InputAffineTransform | None = field(init=False, repr=False, compare=False, default=None)

    def __post_init__(self) -> None:
        self._inner = _InputAffineTransform.model_construct(root=self.matrix)

    def _to_dict(self) -> dict[str, str | list[float]]:
        return {"type": "affine_transform", "matrix": list(self.matrix)}


Pose = CompositePose | AffinePose


# --- Intrinsics types ---
# Not backed by _inner because the internal Pydantic models validate
# eagerly (e.g. matrix-length checks) while the builder defers
# validation to build().


@dataclass(slots=True)
class SimpleIntrinsics:
    """Simple camera intrinsics (focal length + principal point)."""

    fx: float
    fy: float
    ox: float
    oy: float
    model: str | None = None
    extra: dict[str, float] = field(default_factory=dict, repr=False)

    def _to_dict(self) -> dict[str, str | float]:
        d: dict[str, str | float] = {
            "type": "simple",
            "fx": self.fx,
            "fy": self.fy,
            "ox": self.ox,
            "oy": self.oy,
        }
        if self.model is not None:
            d["model"] = self.model
        d.update(self.extra)
        return d


@dataclass(slots=True)
class AdvancedIntrinsics:
    """Advanced camera intrinsics (full calibration matrices)."""

    k: tuple[float, ...] | None = None
    r: tuple[float, ...] | None = None
    p: tuple[float, ...] | None = None
    model: str | None = None

    def _to_dict(self) -> dict[str, str | list[float]]:
        d: dict[str, str | list[float]] = {"type": "advanced"}
        if self.k is not None:
            d["k"] = list(self.k)
        if self.r is not None:
            d["r"] = list(self.r)
        if self.p is not None:
            d["p"] = list(self.p)
        if self.model is not None:
            d["model"] = self.model
        return d


Intrinsics = SimpleIntrinsics | AdvancedIntrinsics


# ===================================================================
# Pose convenience constructors
# ===================================================================


def quaternion_pose(
    qx: float,
    qy: float,
    qz: float,
    qw: float,
    x: float,
    y: float,
    z: float,
) -> CompositePose:
    """Create a pose from a unit quaternion rotation and a position.

    Args:
        qx: Quaternion *x* component.
        qy: Quaternion *y* component.
        qz: Quaternion *z* component.
        qw: Quaternion *w* (scalar) component.
        x: Translation along the world *x*-axis.
        y: Translation along the world *y*-axis.
        z: Translation along the world *z*-axis.
    """
    return CompositePose(
        rotation=QuaternionRotation(qx=qx, qy=qy, qz=qz, qw=qw),
        position=Position(x=x, y=y, z=z),
    )


def euler_pose(
    rx: float,
    ry: float,
    rz: float,
    x: float,
    y: float,
    z: float,
) -> CompositePose:
    """Create a pose from Euler angles (radians) and a position.

    Args:
        rx: Rotation around the *x*-axis in radians.
        ry: Rotation around the *y*-axis in radians.
        rz: Rotation around the *z*-axis in radians.
        x: Translation along the world *x*-axis.
        y: Translation along the world *y*-axis.
        z: Translation along the world *z*-axis.
    """
    return CompositePose(
        rotation=EulerRotation(rx=rx, ry=ry, rz=rz),
        position=Position(x=x, y=y, z=z),
    )


def matrix_pose(
    rotation: tuple[float, float, float, float, float, float, float, float, float],
    x: float,
    y: float,
    z: float,
) -> CompositePose:
    """Create a pose from a 3x3 rotation matrix and a position.

    Args:
        rotation: Nine floats in row-major order representing a 3x3
            rotation matrix.
        x: Translation along the world *x*-axis.
        y: Translation along the world *y*-axis.
        z: Translation along the world *z*-axis.
    """
    return CompositePose(
        rotation=MatrixRotation(values=rotation),
        position=Position(x=x, y=y, z=z),
    )


def affine_transform(
    matrix: tuple[
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
    ],
) -> AffinePose:
    """Create a pose from a 4x4 affine transform matrix.

    Args:
        matrix: Sixteen floats in row-major order.  The bottom row must
            be ``[0, 0, 0, 1]``.
    """
    return AffinePose(matrix=matrix)


# ===================================================================
# Intrinsics convenience constructors
# ===================================================================


def intrinsics_simple(
    fx: float,
    fy: float,
    ox: float,
    oy: float,
    *,
    model: str | None = None,
    **kwargs: float,
) -> SimpleIntrinsics:
    """Build simple camera intrinsics (focal length + principal point).

    Args:
        fx: Focal length along the *x*-axis (pixels).
        fy: Focal length along the *y*-axis (pixels).
        ox: Principal-point *x* offset (pixels).
        oy: Principal-point *y* offset (pixels).
        model: Optional distortion model name.  One of ``"radial"``,
            ``"plumb_bob"``, ``"fisheye"``, ``"rational_polynomial"``,
            ``"pinhole"``, ``"division"``, ``"ucm"``.
        **kwargs: Extra distortion coefficients (e.g. ``k1=0.1``,
            ``p1=0.01``, ``dfx=…``, ``skew=…``).
    """
    return SimpleIntrinsics(fx=fx, fy=fy, ox=ox, oy=oy, model=model, extra=dict(kwargs))


def intrinsics_advanced(
    k: Sequence[float] | None = None,
    r: Sequence[float] | None = None,
    p: Sequence[float] | None = None,
    *,
    model: str | None = None,
) -> AdvancedIntrinsics:
    """Build advanced camera intrinsics using full calibration matrices.

    Args:
        k: 9-element intrinsic camera matrix (row-major 3x3).
        r: 9-element rectification matrix (row-major 3x3).
        p: 12-element projection matrix (row-major 3x4).
        model: Optional distortion model name.
    """
    return AdvancedIntrinsics(
        k=tuple(k) if k is not None else None,
        r=tuple(r) if r is not None else None,
        p=tuple(p) if p is not None else None,
        model=model,
    )


# ===================================================================
# Internal event types
# ===================================================================


@dataclass(slots=True)
class _URIEvent:
    uri: str
    timestamp: SerializedTimestamp | None = None


@dataclass(slots=True)
class _CameraEvent:
    width_px: int
    height_px: int
    intrinsics: Intrinsics
    timestamp: SerializedTimestamp | None = None
    extrinsics: Pose | None = None


@dataclass(slots=True)
class _FoREvent:
    pose: Pose
    timestamp: SerializedTimestamp | None = None


# ===================================================================
# Stream builders
# ===================================================================


class _StreamBuilderBase:
    """Internal base -- not part of the public API."""

    def __init__(self, name: str, scene: SceneBuilder) -> None:
        self._name = name
        self._scene = scene

    @property
    def _event_count(self) -> int:
        raise NotImplementedError

    def _build(self) -> dict[str, Any]:
        raise NotImplementedError


# -------------------------------------------------------------------
# Helpers for serialising events inside _build()
# -------------------------------------------------------------------


def _serialise_uri_event(e: _URIEvent) -> dict[str, str | SerializedTimestamp]:
    d: dict[str, str | SerializedTimestamp] = {"uri": e.uri}
    if e.timestamp is not None:
        d["timestamp"] = e.timestamp
    return d


def _serialise_pose(pose: Pose) -> dict[str, Any]:
    return pose._to_dict()


# -------------------------------------------------------------------
# Point-cloud stream
# -------------------------------------------------------------------


class PCDStreamBuilder(_StreamBuilderBase):
    """Builder for a point-cloud stream.

    Supports:
        * Per-event URIs with optional timestamps.
        * Static pose relative to the scene origin.
        * Linkage to a frame-of-reference stream.
    """

    def __init__(
        self,
        name: str,
        scene: SceneBuilder,
        *,
        frame_of_reference: str | None = None,
        pose: Pose | None = None,
    ) -> None:
        super().__init__(name, scene)
        self._events: list[_URIEvent] = []
        self._frame_of_reference = frame_of_reference
        self._pose = pose

    @property
    def _event_count(self) -> int:
        return len(self._events)

    # -- full-detail API --------------------------------------------------

    def add_event(self, *, uri: str, timestamp: Timestamp = None) -> PCDStreamBuilder:
        """Append a single point-cloud event."""
        self._events.append(_URIEvent(uri=uri, timestamp=_serialize_timestamp(timestamp)))
        return self

    # -- convenience wrappers ---------------------------------------------

    def add_events(
        self,
        uris: Sequence[str],
        timestamps: Sequence[Timestamp] | None = None,
    ) -> PCDStreamBuilder:
        """Bulk-add point-cloud events.

        *timestamps* defaults to ``0, 1, 2, …``
        """
        if timestamps is None:
            timestamps = list(range(len(uris)))
        for uri, ts in zip(uris, timestamps):
            self.add_event(uri=uri, timestamp=ts)
        return self

    # -- mutators ---------------------------------------------------------

    def set_frame_of_reference(self, for_id: str) -> PCDStreamBuilder:
        """Link this stream to a frame-of-reference stream by name."""
        self._frame_of_reference = for_id
        return self

    def set_pose(self, pose: Pose) -> PCDStreamBuilder:
        """Set a static pose for this stream."""
        self._pose = pose
        return self

    def done(self) -> SceneBuilder:
        """Return the parent :class:`SceneBuilder` for continued chaining."""
        return self._scene

    # -- serialization ----------------------------------------------------

    def _build(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "type": "point_cloud",
            "events": [_serialise_uri_event(e) for e in self._events],
        }
        if self._frame_of_reference is not None:
            d["frame_of_reference"] = self._frame_of_reference
        if self._pose is not None:
            d["pose"] = _serialise_pose(self._pose)
        return d


# -------------------------------------------------------------------
# Camera-parameters stream
# -------------------------------------------------------------------


class CameraStreamBuilder(_StreamBuilderBase):
    """Builder for a camera-parameters stream.

    Supports:
        * Simple intrinsics (focal length / principal point) with any
          supported distortion model.
        * Advanced intrinsics (full K, R, P matrices).
        * Optional extrinsics per event.
        * Static pose and frame-of-reference linkage.
    """

    def __init__(
        self,
        name: str,
        scene: SceneBuilder,
        *,
        frame_of_reference: str | None = None,
        pose: Pose | None = None,
    ) -> None:
        super().__init__(name, scene)
        self._events: list[_CameraEvent] = []
        self._frame_of_reference = frame_of_reference
        self._pose = pose

    @property
    def _event_count(self) -> int:
        return len(self._events)

    # -- full-detail API --------------------------------------------------

    def add_event(
        self,
        width: int,
        height: int,
        intrinsics: Intrinsics,
        *,
        timestamp: Timestamp = None,
        extrinsics: Pose | None = None,
    ) -> CameraStreamBuilder:
        """Append a camera-parameters event."""
        self._events.append(
            _CameraEvent(
                width_px=width,
                height_px=height,
                intrinsics=intrinsics,
                timestamp=_serialize_timestamp(timestamp),
                extrinsics=extrinsics,
            )
        )
        return self

    # -- convenience wrappers ---------------------------------------------

    def add_static(
        self,
        width: int,
        height: int,
        intrinsics: Intrinsics,
        *,
        timestamp: Timestamp = 0,
        extrinsics: Pose | None = None,
    ) -> CameraStreamBuilder:
        """Convenience for a camera whose parameters never change.

        Identical to :meth:`add_event` but defaults *timestamp* to ``0``.
        """
        return self.add_event(width, height, intrinsics, timestamp=timestamp, extrinsics=extrinsics)

    # -- mutators ---------------------------------------------------------

    def set_frame_of_reference(self, for_id: str) -> CameraStreamBuilder:
        """Link this stream to a frame-of-reference stream by name."""
        self._frame_of_reference = for_id
        return self

    def set_pose(self, pose: Pose) -> CameraStreamBuilder:
        """Set a static pose for this stream."""
        self._pose = pose
        return self

    def done(self) -> SceneBuilder:
        """Return the parent :class:`SceneBuilder` for continued chaining."""
        return self._scene

    # -- serialization ----------------------------------------------------

    def _build(self) -> dict[str, Any]:
        events: list[dict[str, Any]] = []
        for e in self._events:
            ev: dict[str, Any] = {
                "width_px": e.width_px,
                "height_px": e.height_px,
                "intrinsics": e.intrinsics._to_dict(),
            }
            if e.timestamp is not None:
                ev["timestamp"] = e.timestamp
            if e.extrinsics is not None:
                ev["extrinsics"] = _serialise_pose(e.extrinsics)
            events.append(ev)

        d: dict[str, Any] = {"type": "camera", "events": events}
        if self._frame_of_reference is not None:
            d["frame_of_reference"] = self._frame_of_reference
        if self._pose is not None:
            d["pose"] = _serialise_pose(self._pose)
        return d


# -------------------------------------------------------------------
# Frame-of-reference stream
# -------------------------------------------------------------------


class FoRStreamBuilder(_StreamBuilderBase):
    """Builder for a frame-of-reference (FoR) stream.

    Supports:
        * Any rotation encoding (quaternion, Euler, matrix, affine).
        * Parent-child FoR chains.
    """

    def __init__(
        self,
        name: str,
        scene: SceneBuilder,
        *,
        for_id: str,
        parent_for_id: str | None = None,
    ) -> None:
        super().__init__(name, scene)
        self._events: list[_FoREvent] = []
        self._for_id = for_id
        self._parent_for_id = parent_for_id

    @property
    def _event_count(self) -> int:
        return len(self._events)

    # -- full-detail API --------------------------------------------------

    def add_event(
        self,
        pose: Pose,
        *,
        timestamp: Timestamp = None,
    ) -> FoRStreamBuilder:
        """Append a frame-of-reference event."""
        self._events.append(_FoREvent(pose=pose, timestamp=_serialize_timestamp(timestamp)))
        return self

    # -- convenience wrappers ---------------------------------------------

    def add_events(
        self,
        poses: Sequence[Pose],
        timestamps: Sequence[Timestamp] | None = None,
    ) -> FoRStreamBuilder:
        """Bulk-add FoR events.

        *timestamps* defaults to ``0, 1, 2, …``
        """
        if timestamps is None:
            timestamps = list(range(len(poses)))
        for pose, ts in zip(poses, timestamps):
            self.add_event(pose, timestamp=ts)
        return self

    def done(self) -> SceneBuilder:
        """Return the parent :class:`SceneBuilder` for continued chaining."""
        return self._scene

    # -- serialization ----------------------------------------------------

    def _build(self) -> dict[str, Any]:
        events: list[dict[str, Any]] = []
        for e in self._events:
            ev: dict[str, Any] = {"pose": _serialise_pose(e.pose)}
            if e.timestamp is not None:
                ev["timestamp"] = e.timestamp
            events.append(ev)

        d: dict[str, Any] = {
            "type": "frame_of_reference",
            "for_id": self._for_id,
            "events": events,
        }
        if self._parent_for_id is not None:
            d["parent_for_id"] = self._parent_for_id
        return d


# -------------------------------------------------------------------
# Image stream
# -------------------------------------------------------------------


class ImageStreamBuilder(_StreamBuilderBase):
    """Builder for an image stream linked to a camera."""

    def __init__(
        self,
        name: str,
        scene: SceneBuilder,
        *,
        camera: str,
    ) -> None:
        super().__init__(name, scene)
        self._events: list[_URIEvent] = []
        self._camera = camera

    @property
    def _event_count(self) -> int:
        return len(self._events)

    # -- full-detail API --------------------------------------------------

    def add_event(self, *, uri: str, timestamp: Timestamp = None) -> ImageStreamBuilder:
        """Append an image event."""
        self._events.append(_URIEvent(uri=uri, timestamp=_serialize_timestamp(timestamp)))
        return self

    # -- convenience wrappers ---------------------------------------------

    def add_events(
        self,
        uris: Sequence[str],
        timestamps: Sequence[Timestamp] | None = None,
    ) -> ImageStreamBuilder:
        """Bulk-add image events.

        *timestamps* defaults to ``0, 1, 2, …``
        """
        if timestamps is None:
            timestamps = list(range(len(uris)))
        for uri, ts in zip(uris, timestamps):
            self.add_event(uri=uri, timestamp=ts)
        return self

    def done(self) -> SceneBuilder:
        """Return the parent :class:`SceneBuilder` for continued chaining."""
        return self._scene

    # -- serialization ----------------------------------------------------

    def _build(self) -> dict[str, Any]:
        return {
            "type": "image",
            "camera": self._camera,
            "events": [_serialise_uri_event(e) for e in self._events],
        }


# -------------------------------------------------------------------
# 3-D model stream
# -------------------------------------------------------------------


class ModelStreamBuilder(_StreamBuilderBase):
    """Builder for a 3-D model stream.

    Supports:
        * Per-event model URIs with timestamps.
        * Static pose and frame-of-reference linkage.
    """

    def __init__(
        self,
        name: str,
        scene: SceneBuilder,
        *,
        frame_of_reference: str | None = None,
        pose: Pose | None = None,
    ) -> None:
        super().__init__(name, scene)
        self._events: list[_URIEvent] = []
        self._frame_of_reference = frame_of_reference
        self._pose = pose

    @property
    def _event_count(self) -> int:
        return len(self._events)

    # -- full-detail API --------------------------------------------------

    def add_event(self, *, uri: str, timestamp: Timestamp = None) -> ModelStreamBuilder:
        """Append a 3-D model event."""
        self._events.append(_URIEvent(uri=uri, timestamp=_serialize_timestamp(timestamp)))
        return self

    # -- convenience wrappers ---------------------------------------------

    def add_events(
        self,
        uris: Sequence[str],
        timestamps: Sequence[Timestamp] | None = None,
    ) -> ModelStreamBuilder:
        """Bulk-add model events.

        *timestamps* defaults to ``0, 1, 2, …``
        """
        if timestamps is None:
            timestamps = list(range(len(uris)))
        for uri, ts in zip(uris, timestamps):
            self.add_event(uri=uri, timestamp=ts)
        return self

    # -- mutators ---------------------------------------------------------

    def set_frame_of_reference(self, for_id: str) -> ModelStreamBuilder:
        """Link this stream to a frame-of-reference stream by name."""
        self._frame_of_reference = for_id
        return self

    def set_pose(self, pose: Pose) -> ModelStreamBuilder:
        """Set a static pose for this stream."""
        self._pose = pose
        return self

    def done(self) -> SceneBuilder:
        """Return the parent :class:`SceneBuilder` for continued chaining."""
        return self._scene

    # -- serialization ----------------------------------------------------

    def _build(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "type": "3d_model",
            "events": [_serialise_uri_event(e) for e in self._events],
        }
        if self._frame_of_reference is not None:
            d["frame_of_reference"] = self._frame_of_reference
        if self._pose is not None:
            d["pose"] = _serialise_pose(self._pose)
        return d


# ===================================================================
# Scene builder (top-level)
# ===================================================================


@dataclass(slots=True)
class _ConventionDict:
    x: str
    y: str
    z: str

    def to_dict(self) -> dict[str, str]:
        return {"x": self.x, "y": self.y, "z": self.z}


class SceneBuilder:
    """Top-level builder for constructing an Encord scene payload.

    Supported stream types:
        * **Point cloud** -- :meth:`add_pcd_stream`
        * **Camera parameters** -- :meth:`add_camera_stream`
        * **Frame of reference** -- :meth:`add_for_stream`
        * **Image** -- :meth:`add_image_stream`
        * **3-D model** -- :meth:`add_model_stream`
    """

    def __init__(self) -> None:
        self._streams: dict[str, _StreamBuilderBase] = {}
        self._ground_height: float | None = None
        self._world_convention: _ConventionDict | None = None
        self._camera_convention: _ConventionDict | None = None

    # -- global configuration ---------------------------------------------

    def set_ground_height(self, height: float) -> SceneBuilder:
        """Set the default ground height (value on the UP axis)."""
        self._ground_height = height
        return self

    def set_world_convention(self, *, x: Direction, y: Direction, z: Direction) -> SceneBuilder:
        """Set the world coordinate-system convention.

        Available directions: ``Direction.UP``, ``DOWN``, ``LEFT``,
        ``RIGHT``, ``FORWARD``, ``BACKWARD``.
        """
        self._world_convention = _ConventionDict(x=str(x), y=str(y), z=str(z))
        return self

    def set_camera_convention(self, *, x: Direction, y: Direction, z: Direction) -> SceneBuilder:
        """Set the camera coordinate-system convention.

        Must share handedness with the world convention.
        """
        self._camera_convention = _ConventionDict(x=str(x), y=str(y), z=str(z))
        return self

    # -- stream factories -------------------------------------------------

    def add_pcd_stream(
        self,
        name: str,
        *,
        frame_of_reference: str | None = None,
        pose: Pose | None = None,
    ) -> PCDStreamBuilder:
        """Add a point-cloud stream."""
        sb = PCDStreamBuilder(name, self, frame_of_reference=frame_of_reference, pose=pose)
        self._streams[name] = sb
        return sb

    def add_camera_stream(
        self,
        name: str,
        *,
        frame_of_reference: str | None = None,
        pose: Pose | None = None,
    ) -> CameraStreamBuilder:
        """Add a camera-parameters stream."""
        sb = CameraStreamBuilder(name, self, frame_of_reference=frame_of_reference, pose=pose)
        self._streams[name] = sb
        return sb

    def add_for_stream(
        self,
        name: str,
        *,
        for_id: str,
        parent_for_id: str | None = None,
    ) -> FoRStreamBuilder:
        """Add a frame-of-reference stream."""
        sb = FoRStreamBuilder(name, self, for_id=for_id, parent_for_id=parent_for_id)
        self._streams[name] = sb
        return sb

    def add_image_stream(
        self,
        name: str,
        *,
        camera: str,
    ) -> ImageStreamBuilder:
        """Add an image stream linked to a camera stream."""
        sb = ImageStreamBuilder(name, self, camera=camera)
        self._streams[name] = sb
        return sb

    def add_model_stream(
        self,
        name: str,
        *,
        frame_of_reference: str | None = None,
        pose: Pose | None = None,
    ) -> ModelStreamBuilder:
        """Add a 3-D model stream."""
        sb = ModelStreamBuilder(name, self, frame_of_reference=frame_of_reference, pose=pose)
        self._streams[name] = sb
        return sb

    # -- build & validate -------------------------------------------------

    def build(self) -> dict[str, Any]:
        """Validate the scene and serialize to a plain ``dict``.

        Raises:
            EncordException: When validation fails.  All detected problems
                are reported in a single message.
        """
        if not self._streams:
            raise EncordException("Scene must contain at least one stream")

        errors: list[str] = []

        # Collect cross-reference sets.
        camera_names: set[str] = set()
        for_stream_names: set[str] = set()
        for name, sb in self._streams.items():
            if isinstance(sb, CameraStreamBuilder):
                camera_names.add(name)
            if isinstance(sb, FoRStreamBuilder):
                for_stream_names.add(name)

        # Per-stream validation.
        streams_dict: dict[str, Any] = {}
        for name, sb in self._streams.items():
            # 1. Must have events.
            if sb._event_count == 0:
                errors.append(f"Stream '{name}' has no events")

            # 2. URI must not be empty.
            if isinstance(sb, PCDStreamBuilder | ImageStreamBuilder | ModelStreamBuilder):
                for idx, event in enumerate(sb._events):
                    if not event.uri:
                        errors.append(f"Stream '{name}' event {idx} has an empty URI")

            # 3. Advanced intrinsics matrix-length checks.
            if isinstance(sb, CameraStreamBuilder):
                for idx, event in enumerate(sb._events):
                    intr = event.intrinsics
                    if isinstance(intr, AdvancedIntrinsics):
                        if intr.k is not None and len(intr.k) != 9:
                            errors.append(
                                f"Camera '{name}' event {idx}: " f"'k' must have 9 elements, got {len(intr.k)}"
                            )
                        if intr.r is not None and len(intr.r) != 9:
                            errors.append(
                                f"Camera '{name}' event {idx}: " f"'r' must have 9 elements, got {len(intr.r)}"
                            )
                        if intr.p is not None and len(intr.p) != 12:
                            errors.append(
                                f"Camera '{name}' event {idx}: " f"'p' must have 12 elements, got {len(intr.p)}"
                            )

            # 4. Image → camera reference.
            if isinstance(sb, ImageStreamBuilder):
                if sb._camera not in camera_names:
                    errors.append(
                        f"Image stream '{name}' references camera "
                        f"'{sb._camera}' which does not exist. "
                        f"Available cameras: {camera_names or '{}'}"
                    )

            # 5. Frame-of-reference linkage.
            if isinstance(sb, PCDStreamBuilder | CameraStreamBuilder | ModelStreamBuilder):
                ref = sb._frame_of_reference
                if ref is not None and ref not in for_stream_names:
                    errors.append(
                        f"Stream '{name}' references frame of reference "
                        f"'{ref}' which does not exist. "
                        f"Available FoR streams: {for_stream_names or '{}'}"
                    )

            # 6. FoR parent reference.
            if isinstance(sb, FoRStreamBuilder) and sb._parent_for_id is not None:
                if sb._parent_for_id not in for_stream_names:
                    errors.append(
                        f"FoR stream '{name}' references parent "
                        f"'{sb._parent_for_id}' which does not exist. "
                        f"Available FoR streams: {for_stream_names or '{}'}"
                    )

            streams_dict[name] = sb._build()

        if errors:
            raise EncordException("Scene validation failed:\n- " + "\n- ".join(errors))

        # Output shape.
        has_config = (
            self._ground_height is not None or self._world_convention is not None or self._camera_convention is not None
        )

        if has_config:
            result: dict[str, Any] = {"content": streams_dict}
            if self._ground_height is not None:
                result["default_ground_height"] = self._ground_height
            if self._world_convention is not None:
                result["world_convention"] = self._world_convention.to_dict()
            if self._camera_convention is not None:
                result["camera_convention"] = self._camera_convention.to_dict()
            return result

        return streams_dict
