"""Geometry utilities for 3D operations on point clouds."""

import numpy as np
from numpy.typing import NDArray

from encord.objects.coordinates import CuboidCoordinates


def euler_to_rotation_matrix(alpha: float, beta: float, gamma: float) -> NDArray[np.float64]:
    """Convert Euler angles to a 3x3 rotation matrix.

    Uses XYZ intrinsic rotation order (matching Three.js default Euler order):
    - alpha: rotation around X axis (roll)
    - beta: rotation around Y axis (pitch)
    - gamma: rotation around Z axis (yaw)

    The combined rotation is: Rz(gamma) @ Ry(beta) @ Rx(alpha)

    Args:
        alpha: Rotation around X axis in radians.
        beta: Rotation around Y axis in radians.
        gamma: Rotation around Z axis in radians.

    Returns:
        3x3 rotation matrix.
    """
    ca, sa = np.cos(alpha), np.sin(alpha)
    cb, sb = np.cos(beta), np.sin(beta)
    cg, sg = np.cos(gamma), np.sin(gamma)

    # XYZ intrinsic rotation: Rz(gamma) @ Ry(beta) @ Rx(alpha)
    rotation = np.array(
        [
            [cb * cg, sa * sb * cg - ca * sg, ca * sb * cg + sa * sg],
            [cb * sg, sa * sb * sg + ca * cg, ca * sb * sg - sa * cg],
            [-sb, sa * cb, ca * cb],
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
    half_size = np.array(cuboid.size, dtype=np.float64) / 2.0 + margin

    # Get rotation matrix (transpose = inverse for rotation matrices)
    rotation_T = euler_to_rotation_matrix(*orientation).T

    # Transform points to cuboid local coordinates: R^T @ (p - center)
    # Using matrix multiplication: (N,3) @ (3,3) = (N,3)
    local_points = (points - position) @ rotation_T.T

    # Check bounds along each axis separately to allow short-circuit evaluation
    # and avoid creating intermediate arrays
    inside = (
        (np.abs(local_points[:, 0]) <= half_size[0])
        & (np.abs(local_points[:, 1]) <= half_size[1])
        & (np.abs(local_points[:, 2]) <= half_size[2])
    )

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
