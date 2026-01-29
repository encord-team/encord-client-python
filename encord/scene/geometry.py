"""Geometry utilities for 3D operations on point clouds."""

from typing import Tuple

import numpy as np
from numpy.typing import NDArray

from encord.objects.coordinates import CuboidCoordinates


def euler_to_rotation_matrix(alpha: float, beta: float, gamma: float) -> NDArray[np.float64]:
    """Convert Euler angles to a 3x3 rotation matrix.

    Uses ZYX intrinsic rotation order (yaw-pitch-roll convention):
    - alpha: rotation around Z axis (yaw)
    - beta: rotation around Y axis (pitch)
    - gamma: rotation around X axis (roll)

    Args:
        alpha: Rotation around Z axis in radians.
        beta: Rotation around Y axis in radians.
        gamma: Rotation around X axis in radians.

    Returns:
        3x3 rotation matrix.
    """
    ca, sa = np.cos(alpha), np.sin(alpha)
    cb, sb = np.cos(beta), np.sin(beta)
    cg, sg = np.cos(gamma), np.sin(gamma)

    # ZYX rotation: Rz(alpha) @ Ry(beta) @ Rx(gamma)
    rotation = np.array(
        [
            [ca * cb, ca * sb * sg - sa * cg, ca * sb * cg + sa * sg],
            [sa * cb, sa * sb * sg + ca * cg, sa * sb * cg - ca * sg],
            [-sb, cb * sg, cb * cg],
        ],
        dtype=np.float64,
    )
    return rotation


def points_in_cuboid(
    points: NDArray[np.float64],
    cuboid: CuboidCoordinates,
    margin: float = 0.0,
) -> NDArray[np.bool_]:
    """Check which points lie inside an oriented cuboid.

    Args:
        points: Array of shape (N, 3) containing 3D points.
        cuboid: CuboidCoordinates defining the oriented bounding box.
        margin: Extra margin to add to the cuboid bounds (in meters).
            Use positive values to expand the cuboid and capture points
            on or near the surface.

    Returns:
        Boolean array of shape (N,) where True indicates the point is inside.
    """
    points = np.asarray(points, dtype=np.float64)
    if points.ndim == 1:
        points = points.reshape(1, -1)

    position = np.array(cuboid.position, dtype=np.float64)
    orientation = cuboid.orientation
    size = np.array(cuboid.size, dtype=np.float64)

    # Translate points to cuboid center
    translated = points - position

    # Get rotation matrix and apply inverse (transpose) to points
    rotation = euler_to_rotation_matrix(*orientation)
    local_points = (rotation.T @ translated.T).T

    # Check if points are within half-size bounds (plus margin)
    half_size = size / 2.0 + margin
    inside = np.all(np.abs(local_points) <= half_size, axis=1)

    return inside


def points_in_cuboid_indices(
    points: NDArray[np.float64],
    cuboid: CuboidCoordinates,
    margin: float = 0.0,
) -> NDArray[np.intp]:
    """Get indices of points that lie inside an oriented cuboid.

    Args:
        points: Array of shape (N, 3) containing 3D points.
        cuboid: CuboidCoordinates defining the oriented bounding box.
        margin: Extra margin to add to the cuboid bounds (in meters).

    Returns:
        Array of indices where points are inside the cuboid.
    """
    mask = points_in_cuboid(points, cuboid, margin=margin)
    return np.nonzero(mask)[0]
