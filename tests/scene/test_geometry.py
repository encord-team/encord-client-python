"""Tests for the geometry module."""

import numpy as np

from encord.objects.coordinates import CuboidCoordinates
from encord.scene.geometry import euler_to_rotation_matrix, points_in_cuboid, points_in_cuboid_indices


def test_euler_to_rotation_identity() -> None:
    """Zero euler angles should give identity matrix."""
    rotation = euler_to_rotation_matrix(0, 0, 0)
    np.testing.assert_array_almost_equal(rotation, np.eye(3))


def test_euler_to_rotation_z_90() -> None:
    """90 degree rotation around Z axis (third parameter in XYZ order)."""
    rotation = euler_to_rotation_matrix(0, 0, np.pi / 2)
    expected = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]], dtype=np.float64)
    np.testing.assert_array_almost_equal(rotation, expected)


def test_points_in_axis_aligned_cuboid() -> None:
    """Test point containment in an axis-aligned cuboid."""
    cuboid = CuboidCoordinates(
        position=(0.0, 0.0, 0.0),
        orientation=(0.0, 0.0, 0.0),
        size=(2.0, 2.0, 2.0),
    )

    points = np.array(
        [
            [0.0, 0.0, 0.0],  # Inside (center)
            [0.5, 0.5, 0.5],  # Inside
            [1.0, 0.0, 0.0],  # On edge
            [1.5, 0.0, 0.0],  # Outside
            [-1.0, -1.0, -1.0],  # On corner
            [2.0, 0.0, 0.0],  # Outside
        ]
    )

    result = points_in_cuboid(points, cuboid)
    expected = np.array([True, True, True, False, True, False])
    np.testing.assert_array_equal(result, expected)


def test_points_in_rotated_cuboid() -> None:
    """Test point containment in a rotated cuboid."""
    # Cuboid rotated 90 degrees around Z axis (third parameter in XYZ order)
    cuboid = CuboidCoordinates(
        position=(0.0, 0.0, 0.0),
        orientation=(0.0, 0.0, np.pi / 2),  # 90 deg rotation around Z
        size=(4.0, 2.0, 2.0),  # Long in X direction (but rotated to Y)
    )

    points = np.array(
        [
            [0.0, 0.0, 0.0],  # Inside (center)
            [0.0, 1.5, 0.0],  # Inside (along rotated X axis = world Y)
            [1.5, 0.0, 0.0],  # Outside (beyond half-width in world X)
            [0.0, 2.5, 0.0],  # Outside (beyond half-length in world Y)
        ]
    )

    result = points_in_cuboid(points, cuboid)
    expected = np.array([True, True, False, False])
    np.testing.assert_array_equal(result, expected)


def test_points_in_translated_cuboid() -> None:
    """Test point containment in a translated cuboid."""
    cuboid = CuboidCoordinates(
        position=(10.0, 20.0, 30.0),
        orientation=(0.0, 0.0, 0.0),
        size=(2.0, 2.0, 2.0),
    )

    points = np.array(
        [
            [10.0, 20.0, 30.0],  # Inside (center)
            [10.5, 20.5, 30.5],  # Inside
            [0.0, 0.0, 0.0],  # Outside (far from cuboid)
            [12.0, 20.0, 30.0],  # Outside
        ]
    )

    result = points_in_cuboid(points, cuboid)
    expected = np.array([True, True, False, False])
    np.testing.assert_array_equal(result, expected)


def test_points_in_cuboid_indices() -> None:
    """Test that indices function returns correct indices."""
    cuboid = CuboidCoordinates(
        position=(0.0, 0.0, 0.0),
        orientation=(0.0, 0.0, 0.0),
        size=(2.0, 2.0, 2.0),
    )

    points = np.array(
        [
            [0.0, 0.0, 0.0],  # 0: Inside
            [5.0, 0.0, 0.0],  # 1: Outside
            [0.5, 0.5, 0.5],  # 2: Inside
            [10.0, 10.0, 10.0],  # 3: Outside
            [-0.5, -0.5, -0.5],  # 4: Inside
        ]
    )

    indices = points_in_cuboid_indices(points, cuboid)
    expected = np.array([0, 2, 4])
    np.testing.assert_array_equal(indices, expected)
