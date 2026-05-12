"""Public rotation types and convenience constructors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Union, cast

from encord.beta.scene.internal.upload import InputEulerRotation as _InputEulerRotation
from encord.beta.scene.internal.upload import InputQuaternion as _InputQuaternion
from encord.beta.scene.internal.upload import InputRotationMatrix as _InputRotationMatrix


@dataclass
class QuaternionRotation:
    """Unit-quaternion rotation.

    Each component must be in ``[-1.0, 1.0]`` and the quaternion must
    have unit magnitude (``sqrt(qx**2 + qy**2 + qz**2 + qw**2) ≈ 1.0``,
    tolerance ``1e-2``). These constraints are enforced server-side.
    """

    qx: float
    qy: float
    qz: float
    qw: float

    def _to_internal(self) -> _InputQuaternion:
        return _InputQuaternion.model_construct(x=self.qx, y=self.qy, z=self.qz, w=self.qw)


@dataclass
class EulerRotation:
    """Euler-angle rotation (radians), applied as extrinsic X-Y-Z.

    Each angle must be in ``[-2.1pi, 2.1pi]`` (roughly +/-378 degrees).
    This constraint is enforced server-side.
    """

    rx: float
    ry: float
    rz: float

    def _to_internal(self) -> _InputEulerRotation:
        return _InputEulerRotation.model_construct(x=self.rx, y=self.ry, z=self.rz)


@dataclass
class MatrixRotation:
    """3x3 rotation matrix (9 floats, **column-major**).

    The 9 values are stored column-by-column::

        Given the matrix:
            | r00  r01  r02 |
            | r10  r11  r12 |
            | r20  r21  r22 |

        Flat order: [r00, r10, r20, r01, r11, r21, r02, r12, r22]
                     -- col 0 --  -- col 1 --  -- col 2 --

    The matrix must be a proper rotation matrix: each column must be a
    unit vector, all column pairs must be orthogonal, and the determinant
    must equal ``1.0``. These constraints are enforced server-side.
    """

    values: Sequence[float]

    def __post_init__(self) -> None:
        if len(self.values) != 9:
            raise ValueError(f"Rotation matrix requires exactly 9 values, got {len(self.values)}")

    def _to_internal(self) -> _InputRotationMatrix:
        return _InputRotationMatrix.model_construct(
            root=cast(
                tuple[float, float, float, float, float, float, float, float, float],
                tuple(self.values),
            )
        )


Rotation = Union[QuaternionRotation, EulerRotation, MatrixRotation]


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
