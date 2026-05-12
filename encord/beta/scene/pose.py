"""Public pose types and convenience constructors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Union, cast

from encord.beta.scene.internal.upload import InputAffineTransform as _InputAffineTransform
from encord.beta.scene.internal.upload import InputCompositePose as _InputCompositePose
from encord.beta.scene.internal.upload import InputPosition as _InputPosition
from encord.beta.scene.internal.upload import InputRotation as _InputRotation
from encord.beta.scene.rotation import EulerRotation, MatrixRotation, QuaternionRotation, Rotation


@dataclass
class Position:
    """3-D position (translation)."""

    x: float
    y: float
    z: float

    def _to_internal(self) -> _InputPosition:
        return _InputPosition.model_construct(x=self.x, y=self.y, z=self.z)


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
    ``det = 1``). The fourth column is translation and the fourth row
    must be ``[0, 0, 0, 1]``. These constraints are enforced server-side.
    """

    matrix: Sequence[float]

    def __post_init__(self) -> None:
        if len(self.matrix) != 16:
            raise ValueError(f"Affine transform requires exactly 16 values, got {len(self.matrix)}")

    def _to_internal(self) -> _InputAffineTransform:
        return _InputAffineTransform.model_construct(
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


Pose = Union[CompositePose, AffinePose]


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

    Rotation order is extrinsic X-Y-Z. See :class:`EulerRotation` for
    constraints.

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
    rotation: Sequence[float],
    x: float,
    y: float,
    z: float,
) -> CompositePose:
    """Create a pose from a 3x3 rotation matrix and a position.

    See :class:`MatrixRotation` for constraints (orthogonal, ``det = 1``).

    Args:
        rotation: Nine floats in **column-major** order representing a
            3x3 rotation matrix.
        x: Translation along the world *x*-axis.
        y: Translation along the world *y*-axis.
        z: Translation along the world *z*-axis.
    """
    return CompositePose(
        rotation=MatrixRotation(values=rotation),
        position=Position(x=x, y=y, z=z),
    )


def affine_transform(matrix: Sequence[float]) -> AffinePose:
    """Create a pose from a 4x4 affine transform matrix.

    See :class:`AffinePose` for constraints (rotation submatrix must be
    proper, bottom row ``[0, 0, 0, 1]``).

    Args:
        matrix: Sixteen floats in **column-major** order. The fourth
            row must be ``[0, 0, 0, 1]``.
    """
    return AffinePose(matrix=matrix)


def identity_pose() -> CompositePose:
    """Return the identity pose (no rotation, no translation)."""
    return CompositePose(
        rotation=QuaternionRotation(qx=0.0, qy=0.0, qz=0.0, qw=1.0),
        position=Position(x=0.0, y=0.0, z=0.0),
    )


def translation_only(x: float, y: float, z: float) -> CompositePose:
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
