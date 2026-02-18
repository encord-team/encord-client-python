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

Every mutator returns ``self``, so calls can be chained fluently.  Each
stream builder also exposes a :meth:`done` method that returns the parent
:class:`SceneBuilder` for multi-stream chaining::

    scene = (
        SceneBuilder()
        .add_pcd_stream("lidar")
            .add_event(uri="s3://bucket/frame0.pcd", timestamp=0)
            .done()
        .build()
    )

Timestamps
----------
All ``timestamp`` parameters accept ``int``, ``float``,
``datetime.datetime``, ``datetime.time``, or ``None``.  Numeric values
are passed through as-is; ``datetime`` / ``time`` objects are serialized
via ``.isoformat()``.

Coordinate conventions
----------------------
The world and camera conventions define which :class:`Direction` maps to
each axis.  The three directions must form a valid orthogonal coordinate
system (each spatial axis used exactly once) and the world and camera
conventions **must share the same handedness** (both right-handed or both
left-handed).  A convention is right-handed when ``cross(x, y) == z``.

If only one convention is set, the other defaults to
``x=FORWARD, y=LEFT, z=UP`` for the handedness check.

Server-side validation
----------------------
The builder validates structural issues (missing events, broken
references, matrix sizes) at :meth:`SceneBuilder.build` time.  However,
numerical constraints on rotation values (quaternion unit magnitude,
rotation-matrix orthogonality, Euler-angle bounds, affine bottom-row
format) are enforced **server-side** and will surface as API errors
rather than client-side exceptions.

Pose helpers
------------
* :func:`quaternion_pose` -- unit quaternion + translation
* :func:`euler_pose` -- Euler angles (radians) + translation
* :func:`matrix_pose` -- 3x3 rotation matrix + translation
* :func:`affine_transform` -- full 4x4 affine matrix

Intrinsics helpers
------------------
* :func:`intrinsics_simple` -- focal length / principal point (+ optional
  distortion model).  **Start here** -- sufficient for the vast majority
  of use cases.
* :func:`intrinsics_advanced` -- full camera / rectification / projection
  matrices.  Only use when you have pre-computed K / R / P calibration
  matrices and need to supply them directly.

Dedicated intrinsics constructors (type-safe, named coefficients):

* :func:`intrinsics_pinhole` -- no distortion
* :func:`intrinsics_radial` -- ``k1``, ``k2``, ``k3``
* :func:`intrinsics_plumb_bob` -- ``k1``, ``k2``, ``k3``, ``t1``, ``t2``
* :func:`intrinsics_fisheye` -- ``k1``, ``k2``, ``k3``, ``k4``

Models without a dedicated constructor (use :func:`intrinsics_simple`
with ``model=`` and ``**kwargs``):

* ``"rational_polynomial"`` -- ``k1``–``k6``, ``t1``, ``t2``
* ``"division"`` -- ``k``
* ``"ucm"`` -- ``xi``, ``k1``, ``k2``, ``k3``
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Any, Sequence, Union, cast

from encord.exceptions import EncordException

# Internal types -- imported as private, never exposed to the user.
from encord.scene.internal import (
    CameraIntrinsicsAdvanced as _CameraIntrinsicsAdvanced,
)
from encord.scene.internal import (
    CameraIntrinsicsSimple as _CameraIntrinsicsSimple,
)

# Pydantic models used for final serialization in build().
from encord.scene.internal import (
    Convention as _Convention,
)
from encord.scene.internal import (
    Direction,  # public enum, re-exported
)
from encord.scene.internal import (
    DivisionDistortionModel as _DivisionDistortionModel,
)
from encord.scene.internal import (
    FishEyeDistortionModel as _FishEyeDistortionModel,
)
from encord.scene.internal import (
    InputAffineTransform as _InputAffineTransform,
)
from encord.scene.internal import (
    InputCameraParamsEvent as _InputCameraParamsEvent,
)
from encord.scene.internal import (
    InputCameraStream as _InputCameraStream,
)
from encord.scene.internal import (
    InputCompositePose as _InputCompositePose,
)
from encord.scene.internal import (
    InputEntityType as _InputEntityType,
)
from encord.scene.internal import (
    InputEulerRotation as _InputEulerRotation,
)
from encord.scene.internal import (
    InputFoREvent as _InputFoREvent,
)
from encord.scene.internal import (
    InputFoRStream as _InputFoRStream,
)
from encord.scene.internal import (
    InputImageStream as _InputImageStream,
)
from encord.scene.internal import (
    InputPCDStream as _InputPCDStream,
)
from encord.scene.internal import (
    InputPose as _InputPose,
)
from encord.scene.internal import (
    InputPosition as _InputPosition,
)
from encord.scene.internal import (
    InputQuaternion as _InputQuaternion,
)
from encord.scene.internal import (
    InputRotation as _InputRotation,
)
from encord.scene.internal import (
    InputRotationMatrix as _InputRotationMatrix,
)
from encord.scene.internal import (
    InputURIEvent as _InputURIEvent,
)
from encord.scene.internal import (
    PinholeDistortionModel as _PinholeDistortionModel,
)
from encord.scene.internal import (
    PlumbBobDistortionModel as _PlumbBobDistortionModel,
)
from encord.scene.internal import (
    RadialDistortionModel as _RadialDistortionModel,
)
from encord.scene.internal import (
    RationalPolynomialDistortionModel as _RationalPolynomialDistortionModel,
)
from encord.scene.internal import (
    SceneContent as _SceneContent,
)
from encord.scene.internal import (
    SceneWithConfig as _SceneWithConfig,
)
from encord.scene.internal import (
    Streams as _Streams,
)
from encord.scene.internal import (
    UCMDistortionModel as _UCMDistortionModel,
)

__all__ = [
    "ROOT_FOR",
    "AdvancedIntrinsics",
    "AffinePose",
    "CameraStreamBuilder",
    "CompositePose",
    "Direction",
    "EulerRotation",
    "FoRStreamBuilder",
    "ImageStreamBuilder",
    "Intrinsics",
    "MatrixRotation",
    "PCDStreamBuilder",
    "Pose",
    "Position",
    "QuaternionRotation",
    "Rotation",
    "SceneBuilder",
    "SimpleIntrinsics",
    "affine_transform",
    "euler_pose",
    "intrinsics_advanced",
    "intrinsics_fisheye",
    "intrinsics_pinhole",
    "intrinsics_plumb_bob",
    "intrinsics_radial",
    "intrinsics_simple",
    "matrix_pose",
    "quaternion_pose",
]

ROOT_FOR: str = "root"
"""Sentinel ``parent_for_id`` value that references the implicit scene root.

Pass this as ``parent_for_id`` when creating a FoR stream whose parent is
the scene root rather than another FoR stream.
"""


# ===================================================================
# Timestamp
# ===================================================================

Timestamp = Union[int, float, datetime.datetime, datetime.time, None]
"""Accepted timestamp types.

* ``int`` / ``float`` -- passed through as-is (e.g. frame index or epoch).
* ``datetime.datetime`` / ``datetime.time`` -- serialized via ``.isoformat()``.
* ``None`` -- no timestamp for this event.
"""

SerializedTimestamp = Union[int, float, str]


def _serialize_timestamp(ts: Timestamp) -> SerializedTimestamp | None:
    if ts is None:
        return None
    if isinstance(ts, (datetime.datetime, datetime.time)):
        return ts.isoformat()
    return ts


# ===================================================================
# Public domain types -- wrap internal Pydantic models
# ===================================================================


# --- Position ---


@dataclass
class Position:
    """3-D position (translation)."""

    x: float
    y: float
    z: float
    _inner: _InputPosition | None = field(init=False, repr=False, compare=False, default=None)

    def __post_init__(self) -> None:
        self._inner = _InputPosition.model_construct(x=self.x, y=self.y, z=self.z)

    def _to_internal(self) -> _InputPosition:
        if self._inner is None:
            raise ValueError(f"{type(self).__name__} was not properly initialized")
        return self._inner


# --- Rotation types ---


@dataclass
class QuaternionRotation:
    """Unit-quaternion rotation.

    Each component must be in ``[-1.0, 1.0]`` and the quaternion must
    have unit magnitude (``sqrt(qx**2 + qy**2 + qz**2 + qw**2) ≈ 1.0``,
    tolerance ``1e-2``).  These constraints are enforced server-side.
    """

    qx: float
    qy: float
    qz: float
    qw: float
    _inner: _InputQuaternion | None = field(init=False, repr=False, compare=False, default=None)

    def __post_init__(self) -> None:
        self._inner = _InputQuaternion.model_construct(x=self.qx, y=self.qy, z=self.qz, w=self.qw)

    def _to_internal(self) -> _InputQuaternion:
        if self._inner is None:
            raise ValueError(f"{type(self).__name__} was not properly initialized")
        return self._inner


@dataclass
class EulerRotation:
    """Euler-angle rotation (radians), applied as extrinsic X-Y-Z.

    Each angle must be in ``[-2.1π, 2.1π]`` (roughly ±378°).
    This constraint is enforced server-side.
    """

    rx: float
    ry: float
    rz: float
    _inner: _InputEulerRotation | None = field(init=False, repr=False, compare=False, default=None)

    def __post_init__(self) -> None:
        self._inner = _InputEulerRotation.model_construct(x=self.rx, y=self.ry, z=self.rz)

    def _to_internal(self) -> _InputEulerRotation:
        if self._inner is None:
            raise ValueError(f"{type(self).__name__} was not properly initialized")
        return self._inner


@dataclass
class MatrixRotation:
    """3x3 rotation matrix (9 floats, **column-major**).

    The 9 values are stored column-by-column::

        Given the matrix:
            | r00  r01  r02 |
            | r10  r11  r12 |
            | r20  r21  r22 |

        Flat order: [r00, r10, r20, r01, r11, r21, r02, r12, r22]
                     ── col 0 ──  ── col 1 ──  ── col 2 ──

    The matrix must be a proper rotation matrix: each column must be a
    unit vector, all column pairs must be orthogonal, and the determinant
    must equal ``1.0``.  These constraints are enforced server-side.
    """

    values: Sequence[float]
    _inner: _InputRotationMatrix | None = field(init=False, repr=False, compare=False, default=None)

    def __post_init__(self) -> None:
        if len(self.values) != 9:
            raise ValueError(f"Rotation matrix requires exactly 9 values, got {len(self.values)}")
        self._inner = _InputRotationMatrix.model_construct(
            root=cast(tuple[float, float, float, float, float, float, float, float, float], tuple(self.values))
        )

    def _to_internal(self) -> _InputRotationMatrix:
        if self._inner is None:
            raise ValueError(f"{type(self).__name__} was not properly initialized")
        return self._inner


Rotation = Union[QuaternionRotation, EulerRotation, MatrixRotation]


# --- Rotation convenience constructors ---


def identity_rotation() -> QuaternionRotation:
    """Return the identity rotation (no rotation)."""
    return QuaternionRotation(qx=0.0, qy=0.0, qz=0.0, qw=1.0)


def rotation_x(angle: float) -> EulerRotation:
    """Rotation around the *x*-axis only.

    Args:
        angle: Rotation angle in radians.
    """
    return EulerRotation(rx=angle, ry=0.0, rz=0.0)


def rotation_y(angle: float) -> EulerRotation:
    """Rotation around the *y*-axis only.

    Args:
        angle: Rotation angle in radians.
    """
    return EulerRotation(rx=0.0, ry=angle, rz=0.0)


def rotation_z(angle: float) -> EulerRotation:
    """Rotation around the *z*-axis only.

    Args:
        angle: Rotation angle in radians.
    """
    return EulerRotation(rx=0.0, ry=0.0, rz=angle)


# --- Pose types ---


@dataclass
class CompositePose:
    """Rotation + position pair."""

    rotation: Rotation
    position: Position

    def _to_internal(self) -> _InputCompositePose:
        return _InputCompositePose.model_construct(
            rotation=_InputRotation.model_construct(root=self.rotation._to_internal()),
            position=self.position._to_internal(),
        )


@dataclass
class AffinePose:
    """4x4 affine transform matrix (16 floats, **column-major**).

    The 16 values are stored column-by-column::

        Given the matrix:
            | r00  r01  r02  tx |
            | r10  r11  r12  ty |
            | r20  r21  r22  tz |
            |  0    0    0    1 |

        Flat order: [r00, r10, r20, 0,
                     r01, r11, r21, 0,
                     r02, r12, r22, 0,
                     tx,  ty,  tz,  1]

    The upper-left 3x3 must be a proper rotation matrix (orthogonal,
    ``det = 1``).  The fourth column is translation and the fourth row
    must be ``[0, 0, 0, 1]``.  These constraints are enforced
    server-side.
    """

    matrix: Sequence[float]
    _inner: _InputAffineTransform | None = field(init=False, repr=False, compare=False, default=None)

    def __post_init__(self) -> None:
        if len(self.matrix) != 16:
            raise ValueError(f"Affine transform requires exactly 16 values, got {len(self.matrix)}")
        self._inner = _InputAffineTransform.model_construct(
            root=cast(
                tuple[
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
                tuple(self.matrix),
            )
        )

    def _to_internal(self) -> _InputAffineTransform:
        if self._inner is None:
            raise ValueError(f"{type(self).__name__} was not properly initialized")
        return self._inner


Pose = Union[CompositePose, AffinePose]


# --- Intrinsics types ---

_INTRINSICS_EXTRA_FIELDS = frozenset({"dfx", "dfy", "dox", "doy", "skew"})

_DISTORTION_MODEL_MAP: dict[str, Any] = {
    "radial": _RadialDistortionModel,
    "plumb_bob": _PlumbBobDistortionModel,
    "fisheye": _FishEyeDistortionModel,
    "rational_polynomial": _RationalPolynomialDistortionModel,
    "pinhole": _PinholeDistortionModel,
    "division": _DivisionDistortionModel,
    "ucm": _UCMDistortionModel,
}


@dataclass
class SimpleIntrinsics:
    """Simple camera intrinsics (focal length + principal point).

    Prefer the dedicated constructors (:func:`intrinsics_pinhole`,
    :func:`intrinsics_radial`, :func:`intrinsics_plumb_bob`,
    :func:`intrinsics_fisheye`) or the generic :func:`intrinsics_simple`
    rather than instantiating this class directly.

    The ``extra`` dict holds distortion coefficients and optional fields.
    Distortion coefficients are model-specific (see the module docstring
    for the full table).  The following optional fields apply to all
    models: ``dfx``, ``dfy``, ``dox``, ``doy``, ``skew``.
    """

    fx: float
    fy: float
    ox: float
    oy: float
    model: str | None = None
    extra: dict[str, float] = field(default_factory=dict, repr=False)

    def _to_internal(self) -> _CameraIntrinsicsSimple:
        distortion_model = None
        if self.model is not None:
            model_params = {k: v for k, v in self.extra.items() if k not in _INTRINSICS_EXTRA_FIELDS}
            cls = _DISTORTION_MODEL_MAP.get(self.model)
            if cls is not None:
                distortion_model = cls.model_construct(type=self.model, **model_params)

        return _CameraIntrinsicsSimple.model_construct(
            type="simple",
            fx=self.fx,
            fy=self.fy,
            ox=self.ox,
            oy=self.oy,
            model=distortion_model,
            dfx=self.extra.get("dfx"),
            dfy=self.extra.get("dfy"),
            dox=self.extra.get("dox"),
            doy=self.extra.get("doy"),
            skew=self.extra.get("skew"),
        )


@dataclass
class AdvancedIntrinsics:
    """Advanced camera intrinsics (full calibration matrices).

    .. warning::
       In most cases :class:`SimpleIntrinsics` (via
       :func:`intrinsics_simple` or one of the dedicated constructors)
       is sufficient and much easier to work with.  Only use advanced
       intrinsics when you have pre-computed full K / R / P calibration
       matrices and genuinely need to supply them directly.

    Prefer :func:`intrinsics_advanced` rather than instantiating this
    class directly.

    Args:
        k: 9-element intrinsic camera matrix (row-major 3x3).
            Validated to have exactly 9 elements at build time.
        r: 9-element rectification matrix (row-major 3x3).
            Validated to have exactly 9 elements at build time.
        p: 12-element projection matrix (row-major 3x4).
            Validated to have exactly 12 elements at build time.
        model: Optional distortion model name.
    """

    k: Sequence[float] | None = None
    r: Sequence[float] | None = None
    p: Sequence[float] | None = None
    model: str | None = None

    def _to_internal(self) -> _CameraIntrinsicsAdvanced:
        distortion_model = None
        if self.model is not None:
            cls = _DISTORTION_MODEL_MAP.get(self.model)
            if cls is not None:
                distortion_model = cls.model_construct(type=self.model)

        return _CameraIntrinsicsAdvanced.model_construct(
            type="advanced",
            model=distortion_model,
            k=list(self.k) if self.k is not None else None,
            r=list(self.r) if self.r is not None else None,
            p=list(self.p) if self.p is not None else None,
            skew=None,
        )


Intrinsics = Union[SimpleIntrinsics, AdvancedIntrinsics]


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

    The quaternion must have unit magnitude (server-side validated).
    See :class:`QuaternionRotation` for constraints.

    Args:
        qx: Quaternion *x* component (in ``[-1, 1]``).
        qy: Quaternion *y* component (in ``[-1, 1]``).
        qz: Quaternion *z* component (in ``[-1, 1]``).
        qw: Quaternion *w* (scalar) component (in ``[-1, 1]``).
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

    Rotation order is extrinsic X-Y-Z.  See :class:`EulerRotation` for
    constraints.

    Args:
        rx: Rotation around the *x*-axis in radians (in ``[-2.1π, 2.1π]``).
        ry: Rotation around the *y*-axis in radians (in ``[-2.1π, 2.1π]``).
        rz: Rotation around the *z*-axis in radians (in ``[-2.1π, 2.1π]``).
        x: Translation along the world *x*-axis.
        y: Translation along the world *y*-axis.
        z: Translation along the world *z*-axis.
    """
    return CompositePose(
        rotation=EulerRotation(rx=rx, ry=ry, rz=rz),
        position=Position(x=x, y=y, z=z),
    )


def matrix_pose(
    rotation: Sequence[float],
    x: float,
    y: float,
    z: float,
) -> CompositePose:
    """Create a pose from a 3x3 rotation matrix and a position.

    See :class:`MatrixRotation` for constraints (orthogonal, ``det = 1``).

    Args:
        rotation: Nine floats in **column-major** order representing a
            3x3 rotation matrix.  Accepts any sequence (list, tuple,
            numpy array, etc.).
        x: Translation along the world *x*-axis.
        y: Translation along the world *y*-axis.
        z: Translation along the world *z*-axis.
    """
    return CompositePose(
        rotation=MatrixRotation(values=rotation),
        position=Position(x=x, y=y, z=z),
    )


def affine_transform(
    matrix: Sequence[float],
) -> AffinePose:
    """Create a pose from a 4x4 affine transform matrix.

    See :class:`AffinePose` for constraints (rotation submatrix must be
    proper, bottom row ``[0, 0, 0, 1]``).

    Args:
        matrix: Sixteen floats in **column-major** order.  The fourth
            row must be ``[0, 0, 0, 1]``.  Accepts any sequence (list,
            tuple, numpy array, etc.).
    """
    return AffinePose(matrix=matrix)


def identity_pose() -> CompositePose:
    """Return the identity pose (no rotation, no translation)."""
    return CompositePose(
        rotation=QuaternionRotation(qx=0.0, qy=0.0, qz=0.0, qw=1.0),
        position=Position(x=0.0, y=0.0, z=0.0),
    )


def translation_only(
    x: float,
    y: float,
    z: float,
) -> CompositePose:
    """Create a pose with translation but no rotation.

    Args:
        x: Translation along the world *x*-axis.
        y: Translation along the world *y*-axis.
        z: Translation along the world *z*-axis.
    """
    return CompositePose(
        rotation=QuaternionRotation(qx=0.0, qy=0.0, qz=0.0, qw=1.0),
        position=Position(x=x, y=y, z=z),
    )


def rotation_only(rotation: Rotation) -> CompositePose:
    """Create a pose with rotation but no translation.

    Args:
        rotation: Any supported rotation type (quaternion, Euler, or
            matrix).
    """
    return CompositePose(
        rotation=rotation,
        position=Position(x=0.0, y=0.0, z=0.0),
    )


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

    For models without a dedicated constructor, pass the model name and
    its coefficients as keyword arguments::

        intrinsics_simple(fx, fy, ox, oy, model="division", k=0.01)
        intrinsics_simple(fx, fy, ox, oy, model="ucm", xi=0.5, k1=0.1, k2=0.0, k3=0.0)
        intrinsics_simple(fx, fy, ox, oy, model="rational_polynomial",
                          k1=0.1, k2=0.0, k3=0.0, k4=0.0, k5=0.0, k6=0.0,
                          t1=0.0, t2=0.0)

    Args:
        fx: Focal length along the *x*-axis (pixels).
        fy: Focal length along the *y*-axis (pixels).
        ox: Principal-point *x* offset (pixels).
        oy: Principal-point *y* offset (pixels).
        model: Optional distortion model name.  One of ``"radial"``,
            ``"plumb_bob"``, ``"fisheye"``, ``"rational_polynomial"``,
            ``"pinhole"``, ``"division"``, ``"ucm"``.
        **kwargs: Distortion coefficients (model-specific, see the
            module docstring for the full table) and optional extra
            fields: ``dfx``, ``dfy``, ``dox``, ``doy``, ``skew``.
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

    .. warning::
       In most cases :func:`intrinsics_simple` (or one of the dedicated
       constructors like :func:`intrinsics_pinhole`) is sufficient and
       much easier to use.  Only reach for advanced intrinsics when you
       have pre-computed K / R / P matrices from a calibration tool and
       need to supply them directly.

    Matrix sizes are validated at :meth:`SceneBuilder.build` time.

    Args:
        k: 9-element intrinsic camera matrix (row-major 3x3).
            Must have exactly 9 elements if provided.
        r: 9-element rectification matrix (row-major 3x3).
            Must have exactly 9 elements if provided.
        p: 12-element projection matrix (row-major 3x4).
            Must have exactly 12 elements if provided.
        model: Optional distortion model name.
    """
    return AdvancedIntrinsics(
        k=k,
        r=r,
        p=p,
        model=model,
    )


# ===================================================================
# Dedicated intrinsics convenience constructors
# ===================================================================


def intrinsics_pinhole(
    fx: float,
    fy: float,
    ox: float,
    oy: float,
) -> SimpleIntrinsics:
    """Build pinhole intrinsics (no distortion coefficients).

    Args:
        fx: Focal length along the *x*-axis (pixels).
        fy: Focal length along the *y*-axis (pixels).
        ox: Principal-point *x* offset (pixels).
        oy: Principal-point *y* offset (pixels).
    """
    return SimpleIntrinsics(fx=fx, fy=fy, ox=ox, oy=oy, model="pinhole")


def intrinsics_radial(
    fx: float,
    fy: float,
    ox: float,
    oy: float,
    *,
    k1: float,
    k2: float,
    k3: float,
) -> SimpleIntrinsics:
    """Build intrinsics with a radial distortion model.

    Args:
        fx: Focal length along the *x*-axis (pixels).
        fy: Focal length along the *y*-axis (pixels).
        ox: Principal-point *x* offset (pixels).
        oy: Principal-point *y* offset (pixels).
        k1: First radial distortion coefficient.
        k2: Second radial distortion coefficient.
        k3: Third radial distortion coefficient.
    """
    return SimpleIntrinsics(fx=fx, fy=fy, ox=ox, oy=oy, model="radial", extra={"k1": k1, "k2": k2, "k3": k3})


def intrinsics_plumb_bob(
    fx: float,
    fy: float,
    ox: float,
    oy: float,
    *,
    k1: float,
    k2: float,
    k3: float,
    t1: float,
    t2: float,
) -> SimpleIntrinsics:
    """Build intrinsics with a plumb-bob (Brown-Conrady) distortion model.

    Args:
        fx: Focal length along the *x*-axis (pixels).
        fy: Focal length along the *y*-axis (pixels).
        ox: Principal-point *x* offset (pixels).
        oy: Principal-point *y* offset (pixels).
        k1: First radial distortion coefficient.
        k2: Second radial distortion coefficient.
        k3: Third radial distortion coefficient.
        t1: First tangential distortion coefficient.
        t2: Second tangential distortion coefficient.
    """
    return SimpleIntrinsics(
        fx=fx,
        fy=fy,
        ox=ox,
        oy=oy,
        model="plumb_bob",
        extra={"k1": k1, "k2": k2, "k3": k3, "t1": t1, "t2": t2},
    )


def intrinsics_fisheye(
    fx: float,
    fy: float,
    ox: float,
    oy: float,
    *,
    k1: float,
    k2: float,
    k3: float,
    k4: float,
) -> SimpleIntrinsics:
    """Build intrinsics with a fisheye (Kannala-Brandt) distortion model.

    Common in autonomous-vehicle camera rigs.

    Args:
        fx: Focal length along the *x*-axis (pixels).
        fy: Focal length along the *y*-axis (pixels).
        ox: Principal-point *x* offset (pixels).
        oy: Principal-point *y* offset (pixels).
        k1: First distortion coefficient.
        k2: Second distortion coefficient.
        k3: Third distortion coefficient.
        k4: Fourth distortion coefficient.
    """
    return SimpleIntrinsics(
        fx=fx,
        fy=fy,
        ox=ox,
        oy=oy,
        model="fisheye",
        extra={"k1": k1, "k2": k2, "k3": k3, "k4": k4},
    )


# ===================================================================
# Internal event types
# ===================================================================


@dataclass
class _URIEvent:
    uri: str
    timestamp: SerializedTimestamp | None = None


@dataclass
class _CameraEvent:
    width_px: int
    height_px: int
    intrinsics: Intrinsics
    timestamp: SerializedTimestamp | None = None


@dataclass
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

    def _to_internal(self) -> Any:
        raise NotImplementedError


# -------------------------------------------------------------------
# Helpers for converting builder events to internal models
# -------------------------------------------------------------------


def _pose_to_internal(pose: Pose) -> _InputPose:
    return _InputPose.model_construct(root=pose._to_internal())


# -------------------------------------------------------------------
# Point-cloud stream
# -------------------------------------------------------------------


class PCDStreamBuilder(_StreamBuilderBase):
    """Builder for a point-cloud stream.

    Returned by :meth:`SceneBuilder.add_pcd_stream`.  Call :meth:`done`
    to return to the parent :class:`SceneBuilder`.

    Supports:
        * Per-event URIs with optional timestamps.
        * Static pose relative to the scene origin (via ``pose``
          constructor arg or :meth:`set_pose` -- calling :meth:`set_pose`
          overwrites any previously set pose).
        * Linkage to a frame-of-reference stream (via ``frame_of_reference``
          constructor arg or :meth:`set_frame_of_reference`).  The value
          must be the **stream name** of a FoR stream registered on the
          same :class:`SceneBuilder`.
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
        """Append a single point-cloud event.

        Args:
            uri: Non-empty URI pointing to the point-cloud file.
                Validated at build time.
            timestamp: Event timestamp (``int``, ``float``,
                ``datetime``, or ``None``).  See :data:`Timestamp`.
        """
        self._events.append(_URIEvent(uri=uri, timestamp=_serialize_timestamp(timestamp)))
        return self

    # -- convenience wrappers ---------------------------------------------

    def add_events(
        self,
        uris: Sequence[str],
        timestamps: Sequence[Timestamp] | None = None,
    ) -> PCDStreamBuilder:
        """Bulk-add point-cloud events.

        When *timestamps* is ``None``, auto-generates ``0, 1, 2, …``.

        .. warning::
           If both *uris* and *timestamps* are provided and differ in
           length, the shorter sequence silently determines the number of
           events added (``zip`` truncation).
        """
        if timestamps is None:
            timestamps = list(range(len(uris)))
        for uri, ts in zip(uris, timestamps):
            self.add_event(uri=uri, timestamp=ts)
        return self

    # -- mutators ---------------------------------------------------------

    def set_frame_of_reference(self, for_id: str) -> PCDStreamBuilder:
        """Link this stream to a frame-of-reference stream by name.

        Args:
            for_id: The **stream name** (not the ``for_id``) of a FoR
                stream registered on the same :class:`SceneBuilder`.
                Overwrites any previously set frame of reference.
        """
        self._frame_of_reference = for_id
        return self

    def set_pose(self, pose: Pose) -> PCDStreamBuilder:
        """Set a static pose for this stream.

        Overwrites any pose previously set via the constructor or an
        earlier call to :meth:`set_pose`.
        """
        self._pose = pose
        return self

    def done(self) -> SceneBuilder:
        """Return the parent :class:`SceneBuilder` for continued chaining."""
        return self._scene

    # -- serialization ----------------------------------------------------

    def _to_internal(self) -> _InputPCDStream:
        return _InputPCDStream.model_construct(
            type=_InputEntityType.POINT_CLOUD,
            events=[_InputURIEvent.model_construct(uri=e.uri, timestamp=e.timestamp) for e in self._events],
            frame_of_reference=self._frame_of_reference,
            pose=_pose_to_internal(self._pose) if self._pose is not None else None,
        )


# -------------------------------------------------------------------
# Camera-parameters stream
# -------------------------------------------------------------------


class CameraStreamBuilder(_StreamBuilderBase):
    """Builder for a camera-parameters stream.

    Returned by :meth:`SceneBuilder.add_camera_stream`.  Call
    :meth:`done` to return to the parent :class:`SceneBuilder`.

    Supports:
        * Simple intrinsics (focal length / principal point) with any
          supported distortion model.
        * Advanced intrinsics (full K, R, P matrices).
        * Static pose and frame-of-reference linkage (same semantics as
          :class:`PCDStreamBuilder` -- ``frame_of_reference`` must be the
          **stream name** of a FoR stream).
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
    ) -> CameraStreamBuilder:
        """Append a camera-parameters event.

        Args:
            width: Image width in pixels (must be >= 0).
            height: Image height in pixels (must be >= 0).
            intrinsics: Camera intrinsics (:class:`SimpleIntrinsics` or
                :class:`AdvancedIntrinsics`).
            timestamp: Event timestamp.  See :data:`Timestamp`.
        """
        self._events.append(
            _CameraEvent(
                width_px=width,
                height_px=height,
                intrinsics=intrinsics,
                timestamp=_serialize_timestamp(timestamp),
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
    ) -> CameraStreamBuilder:
        """Convenience for a camera whose parameters never change.

        Identical to :meth:`add_event` but defaults *timestamp* to ``0``.
        """
        return self.add_event(width, height, intrinsics, timestamp=timestamp)

    # -- mutators ---------------------------------------------------------

    def set_frame_of_reference(self, for_id: str) -> CameraStreamBuilder:
        """Link this stream to a frame-of-reference stream by name.

        Args:
            for_id: The **stream name** (not the ``for_id``) of a FoR
                stream registered on the same :class:`SceneBuilder`.
                Overwrites any previously set frame of reference.
        """
        self._frame_of_reference = for_id
        return self

    def set_pose(self, pose: Pose) -> CameraStreamBuilder:
        """Set a static pose for this stream.

        Overwrites any pose previously set via the constructor or an
        earlier call to :meth:`set_pose`.
        """
        self._pose = pose
        return self

    def done(self) -> SceneBuilder:
        """Return the parent :class:`SceneBuilder` for continued chaining."""
        return self._scene

    # -- serialization ----------------------------------------------------

    def _to_internal(self) -> _InputCameraStream:
        return _InputCameraStream.model_construct(
            type=_InputEntityType.CAMERA_PARAMETERS,
            events=[
                _InputCameraParamsEvent.model_construct(
                    width_px=e.width_px,
                    height_px=e.height_px,
                    intrinsics=e.intrinsics._to_internal(),
                    timestamp=e.timestamp,
                )
                for e in self._events
            ],
            frame_of_reference=self._frame_of_reference,
            pose=_pose_to_internal(self._pose) if self._pose is not None else None,
        )


# -------------------------------------------------------------------
# Frame-of-reference stream
# -------------------------------------------------------------------


class FoRStreamBuilder(_StreamBuilderBase):
    """Builder for a frame-of-reference (FoR) stream.

    Returned by :meth:`SceneBuilder.add_for_stream`.  Call :meth:`done`
    to return to the parent :class:`SceneBuilder`.

    A FoR stream has two identifiers:

    * **name** -- the key used to register the stream in the
      :class:`SceneBuilder`.  This is what other streams pass as
      ``frame_of_reference``.
    * **for_id** -- the logical FoR identifier serialized into the
      payload.  It is used for parent-child FoR chains
      (``parent_for_id``).  Must not be ``"root"`` (reserved, see
      :data:`ROOT_FOR`).

    Supports:
        * Any rotation encoding (quaternion, Euler, matrix, affine).
        * Parent-child FoR chains via ``parent_for_id``.
    """

    def __init__(
        self,
        name: str,
        scene: SceneBuilder,
        *,
        parent_for_id: str | None = None,
    ) -> None:
        super().__init__(name, scene)
        self._events: list[_FoREvent] = []
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
        """Append a frame-of-reference event.

        Args:
            pose: The pose for this event (any supported rotation
                encoding).
            timestamp: Event timestamp.  See :data:`Timestamp`.
        """
        self._events.append(_FoREvent(pose=pose, timestamp=_serialize_timestamp(timestamp)))
        return self

    # -- convenience wrappers ---------------------------------------------

    def add_events(
        self,
        poses: Sequence[Pose],
        timestamps: Sequence[Timestamp] | None = None,
    ) -> FoRStreamBuilder:
        """Bulk-add FoR events.

        When *timestamps* is ``None``, auto-generates ``0, 1, 2, …``.

        .. warning::
           If both *poses* and *timestamps* are provided and differ in
           length, the shorter sequence silently determines the number of
           events added (``zip`` truncation).
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

    def _to_internal(self) -> _InputFoRStream:
        return _InputFoRStream.model_construct(
            type=_InputEntityType.FRAME_OF_REFERENCE,
            id=self._for_id,
            parent_FoR_id=self._parent_for_id,
            events=[
                _InputFoREvent.model_construct(
                    timestamp=e.timestamp,
                    pose=_pose_to_internal(e.pose),
                )
                for e in self._events
            ],
        )


# -------------------------------------------------------------------
# Image stream
# -------------------------------------------------------------------


class ImageStreamBuilder(_StreamBuilderBase):
    """Builder for an image stream linked to a camera.

    Returned by :meth:`SceneBuilder.add_image_stream` or
    :meth:`SceneBuilder.add_image_stream_with_camera`.  Call
    :meth:`done` to return to the parent :class:`SceneBuilder`.

    The ``camera`` argument must be the **stream name** of a
    :class:`CameraStreamBuilder` registered on the same
    :class:`SceneBuilder`.  This reference is validated at build time.
    """

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
        """Append an image event.

        Args:
            uri: Non-empty URI pointing to the image file.
                Validated at build time.
            timestamp: Event timestamp.  See :data:`Timestamp`.
        """
        self._events.append(_URIEvent(uri=uri, timestamp=_serialize_timestamp(timestamp)))
        return self

    # -- convenience wrappers ---------------------------------------------

    def add_events(
        self,
        uris: Sequence[str],
        timestamps: Sequence[Timestamp] | None = None,
    ) -> ImageStreamBuilder:
        """Bulk-add image events.

        When *timestamps* is ``None``, auto-generates ``0, 1, 2, …``.

        .. warning::
           If both *uris* and *timestamps* are provided and differ in
           length, the shorter sequence silently determines the number of
           events added (``zip`` truncation).
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

    def _to_internal(self) -> _InputImageStream:
        return _InputImageStream.model_construct(
            type=_InputEntityType.IMAGE,
            camera=self._camera,
            events=[_InputURIEvent.model_construct(uri=e.uri, timestamp=e.timestamp) for e in self._events],
        )


# ===================================================================
# Scene builder (top-level)
# ===================================================================


class SceneBuilder:
    """Top-level builder for constructing an Encord scene payload.

    Supported stream types:
        * **Point cloud** -- :meth:`add_pcd_stream`
        * **Camera parameters** -- :meth:`add_camera_stream`
        * **Frame of reference** -- :meth:`add_for_stream`
        * **Image** -- :meth:`add_image_stream`
        * **Image + camera shorthand** -- :meth:`add_image_stream_with_camera`

    Stream names must be unique.  Re-using a name silently overwrites the
    previously registered stream.

    The scene must contain at least one stream, and every stream must have
    at least one event.  Use :meth:`build` to validate and serialize.
    """

    def __init__(self) -> None:
        self._streams: dict[str, _StreamBuilderBase] = {}
        self._ground_height: float | None = None
        self._world_convention: _Convention | None = None
        self._camera_convention: _Convention | None = None

    # -- global configuration ---------------------------------------------

    def set_ground_height(self, height: float) -> SceneBuilder:
        """Set the default ground height (value on the UP axis)."""
        self._ground_height = height
        return self

    def set_world_convention(self, *, x: Direction, y: Direction, z: Direction) -> SceneBuilder:
        """Set the world coordinate-system convention.

        The three directions must map to three distinct spatial axes,
        forming a valid orthogonal coordinate system.  The convention's
        handedness (right-handed when ``cross(x, y) == z``) **must match**
        the camera convention.  If no camera convention is set, the
        default ``x=FORWARD, y=LEFT, z=UP`` is used for the handedness
        check.

        Available directions: ``Direction.UP``, ``DOWN``, ``LEFT``,
        ``RIGHT``, ``FORWARD``, ``BACKWARD``.
        """
        self._world_convention = _Convention(x=x, y=y, z=z)
        return self

    def set_camera_convention(self, *, x: Direction, y: Direction, z: Direction) -> SceneBuilder:
        """Set the camera coordinate-system convention.

        The three directions must map to three distinct spatial axes,
        forming a valid orthogonal coordinate system.  The convention's
        handedness **must match** the world convention -- both must be
        right-handed (``cross(x, y) == z``) or both left-handed.  If no
        world convention is set, the default ``x=FORWARD, y=LEFT, z=UP``
        is used for the handedness check.

        Available directions: ``Direction.UP``, ``DOWN``, ``LEFT``,
        ``RIGHT``, ``FORWARD``, ``BACKWARD``.
        """
        self._camera_convention = _Convention(x=x, y=y, z=z)
        return self

    # -- stream factories -------------------------------------------------

    def add_pcd_stream(
        self,
        name: str,
        *,
        frame_of_reference: str | None = None,
        pose: Pose | None = None,
    ) -> PCDStreamBuilder:
        """Add a point-cloud stream.

        Args:
            name: Unique stream name.  Re-using an existing name
                silently overwrites the previous stream.
            frame_of_reference: Optional **stream name** of a FoR stream
                to link to.
            pose: Optional static pose for the sensor mount.
        """
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
        """Add a camera-parameters stream.

        Args:
            name: Unique stream name.  Re-using an existing name
                silently overwrites the previous stream.
            frame_of_reference: Optional **stream name** of a FoR stream
                to link to.
            pose: Optional static pose for the sensor mount.
        """
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
        """Add a frame-of-reference stream.

        Args:
            name: Unique stream name.  Other streams reference this
                stream via this name (``frame_of_reference=name``).
                Re-using an existing name silently overwrites the
                previous stream.
            for_id: Logical FoR identifier serialized in the payload.
                Must not be ``"root"`` (see :data:`ROOT_FOR`).
            parent_for_id: Optional ``for_id`` of the parent FoR
                stream, or :data:`ROOT_FOR` to attach to the scene
                root.  Validated at build time.
        """
        if for_id == ROOT_FOR:
            raise EncordException(f"'{ROOT_FOR}' is reserved and cannot be used as a for_id")
        sb = FoRStreamBuilder(name, self, for_id=for_id, parent_for_id=parent_for_id)
        self._streams[name] = sb
        return sb

    def add_image_stream(
        self,
        name: str,
        *,
        camera: str,
    ) -> ImageStreamBuilder:
        """Add an image stream linked to a camera stream.

        Args:
            name: Unique stream name.  Re-using an existing name
                silently overwrites the previous stream.
            camera: The **stream name** of a camera-parameters stream
                registered on this builder.  Validated at build time.
        """
        sb = ImageStreamBuilder(name, self, camera=camera)
        self._streams[name] = sb
        return sb

    def add_image_stream_with_camera(
        self,
        name: str,
        *,
        width: int,
        height: int,
        intrinsics: Intrinsics,
        frame_of_reference: str | None = None,
        pose: Pose | None = None,
    ) -> ImageStreamBuilder:
        """Add an image stream and implicitly create its camera stream.

        Creates a camera stream named ``{name}/camera`` with a single
        event at timestamp 0, then returns the image stream builder so
        you can add image events.

        Args:
            name: Name of the image stream.
            width: Image width in pixels.
            height: Image height in pixels.
            intrinsics: Camera intrinsics (simple or advanced).
            frame_of_reference: Optional FoR linkage for the camera stream.
            pose: Optional static pose for the camera stream.
        """
        camera_name = f"{name}/camera"
        self.add_camera_stream(
            camera_name,
            frame_of_reference=frame_of_reference,
            pose=pose,
        ).add_static(width, height, intrinsics)
        return self.add_image_stream(name, camera=camera_name)

    # -- build & validate -------------------------------------------------

    def build(self) -> dict[str, Any]:
        """Validate the scene and serialize to a plain ``dict``.

        **Client-side validation** (checked here):

        1. At least one stream is present.
        2. Every stream has at least one event.
        3. PCD / image event URIs are non-empty.
        4. Advanced intrinsics matrix sizes (``k``: 9, ``r``: 9,
           ``p``: 12).
        5. Image stream → camera stream reference exists.
        6. PCD / camera ``frame_of_reference`` references an existing
           FoR stream name.
        7. FoR ``parent_for_id`` references an existing FoR stream name
           (or :data:`ROOT_FOR`).

        **Output shape** depends on whether global configuration was set:

        * **Without config** (no convention / ground height): returns a
          flat streams dict ``{"stream_name": {...}, ...}``.
        * **With config**: returns
          ``{"content": <streams>, "default_ground_height": ...,
          "world_convention": ..., "camera_convention": ...}``
          (``None`` fields are omitted).

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
        stream_models: dict[str, Any] = {}
        for name, sb in self._streams.items():
            # 1. Must have events.
            if sb._event_count == 0:
                errors.append(f"Stream '{name}' has no events")

            # 2. URI must not be empty.
            if isinstance(sb, (PCDStreamBuilder, ImageStreamBuilder)):
                for idx, event in enumerate(sb._events):
                    if not event.uri:
                        errors.append(f"Stream '{name}' event {idx} has an empty URI")

            # 3. Advanced intrinsics matrix-length checks.
            if isinstance(sb, CameraStreamBuilder):
                for idx, cam_event in enumerate(sb._events):
                    intr = cam_event.intrinsics
                    if isinstance(intr, AdvancedIntrinsics):
                        if intr.k is not None and len(intr.k) != 9:
                            errors.append(f"Camera '{name}' event {idx}: 'k' must have 9 elements, got {len(intr.k)}")
                        if intr.r is not None and len(intr.r) != 9:
                            errors.append(f"Camera '{name}' event {idx}: 'r' must have 9 elements, got {len(intr.r)}")
                        if intr.p is not None and len(intr.p) != 12:
                            errors.append(f"Camera '{name}' event {idx}: 'p' must have 12 elements, got {len(intr.p)}")

            # 4. Image → camera reference.
            if isinstance(sb, ImageStreamBuilder):
                if sb._camera not in camera_names:
                    errors.append(
                        f"Image stream '{name}' references camera "
                        f"'{sb._camera}' which does not exist. "
                        f"Available cameras: {camera_names or '{}'}"
                    )

            # 5. Frame-of-reference linkage.
            if isinstance(sb, (PCDStreamBuilder, CameraStreamBuilder)):
                ref = sb._frame_of_reference
                if ref is not None and ref not in for_stream_names:
                    errors.append(
                        f"Stream '{name}' references frame of reference "
                        f"'{ref}' which does not exist. "
                        f"Available FoR streams: {for_stream_names or '{}'}"
                    )

            # 6. FoR parent reference.
            if isinstance(sb, FoRStreamBuilder) and sb._parent_for_id is not None:
                if sb._parent_for_id != ROOT_FOR and sb._parent_for_id not in for_stream_names:
                    errors.append(
                        f"FoR stream '{name}' references parent "
                        f"'{sb._parent_for_id}' which does not exist. "
                        f"Available FoR streams: {for_stream_names or '{}'}"
                    )

            stream_models[name] = sb._to_internal()

        if errors:
            raise EncordException("Scene validation failed:\n- " + "\n- ".join(errors))

        # Serialize via Pydantic models from internal.py.
        streams = _Streams.model_construct(root=stream_models)

        has_config = (
            self._ground_height is not None or self._world_convention is not None or self._camera_convention is not None
        )
        if has_config:
            scene_content = _SceneContent.model_construct(root=streams)
            config = _SceneWithConfig.model_construct(
                content=scene_content,
                default_ground_height=self._ground_height,
                world_convention=self._world_convention,
                camera_convention=self._camera_convention,
            )
            return config.model_dump(exclude_none=True)

        return streams.model_dump(exclude_none=True)
