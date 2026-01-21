"""Coordinate transformation utilities for scene frames of reference.

This module provides classes for working with hierarchical coordinate systems
(frames of reference) in 3D scenes, including building transformation matrices
and converting points between coordinate systems.
"""

from typing import TYPE_CHECKING, Dict, List, Optional

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from encord.orm.scene import SceneData


def rotation_matrix_to_quaternion(rotation: NDArray[np.float64]) -> NDArray[np.float64]:
    """Convert a 3x3 rotation matrix to a quaternion [w, x, y, z].

    Args:
        rotation: A 3x3 rotation matrix.

    Returns:
        A quaternion as [w, x, y, z].
    """
    m = rotation
    trace = np.trace(m)
    s = np.sqrt(max(0.0, 1.0 + trace)) / 2.0
    w = s
    x = (m[2, 1] - m[1, 2]) / (4.0 * s) if s > 1e-8 else 0.0
    y = (m[0, 2] - m[2, 0]) / (4.0 * s) if s > 1e-8 else 0.0
    z = (m[1, 0] - m[0, 1]) / (4.0 * s) if s > 1e-8 else 0.0
    return np.array([w, x, y, z], dtype=np.float64)


class FrameOfReference:
    """Represents a coordinate system with position and rotation.

    This class holds transformation data for a single frame of reference,
    including its relationship to a parent frame.

    Attributes:
        id: Unique identifier for this frame of reference.
        parent_id: ID of the parent frame, or None if this is the root.
        position: 3D position vector [x, y, z] relative to parent.
        rotation: 3x3 rotation matrix relative to parent.
    """

    def __init__(
        self,
        for_id: str,
        parent_id: Optional[str],
        position: NDArray[np.float64],
        rotation: NDArray[np.float64],
    ):
        """Initialize a frame of reference.

        Args:
            for_id: Unique identifier for this frame.
            parent_id: ID of the parent frame, or None for root.
            position: 3D position vector as numpy array of shape (3,).
            rotation: 3x3 rotation matrix as numpy array of shape (3, 3).
        """
        self.id = for_id
        self.parent_id = parent_id
        self._position = np.asarray(position, dtype=np.float64).reshape(3)
        self._rotation = np.asarray(rotation, dtype=np.float64).reshape(3, 3)

    @property
    def position(self) -> NDArray[np.float64]:
        """Get the position vector."""
        return self._position.copy()

    @property
    def rotation(self) -> NDArray[np.float64]:
        """Get the rotation matrix."""
        return self._rotation.copy()

    def get_transformation_matrix(self) -> NDArray[np.float64]:
        """Get the 4x4 homogeneous transformation matrix.

        Returns a matrix that transforms points from this frame's local
        coordinates to the parent frame's coordinates.

        Returns:
            4x4 transformation matrix.
        """
        matrix = np.eye(4, dtype=np.float64)
        matrix[:3, :3] = self._rotation
        matrix[:3, 3] = self._position
        return matrix

    def transform_points(self, points: NDArray[np.float64]) -> NDArray[np.float64]:
        """Transform points from this frame's coordinates to parent coordinates.

        Args:
            points: Array of shape (N, 3) containing 3D points.

        Returns:
            Transformed points as array of shape (N, 3).
        """
        points = np.asarray(points, dtype=np.float64)
        if points.ndim == 1:
            points = points.reshape(1, -1)

        # Apply rotation and translation: p' = R * p + t
        transformed = (self._rotation @ points.T).T + self._position
        return transformed

    def get_quaternion(self) -> NDArray[np.float64]:
        """Get the rotation as a quaternion [w, x, y, z]."""
        return rotation_matrix_to_quaternion(self._rotation)

    def __repr__(self) -> str:
        return f"FrameOfReference(id={self.id!r}, parent_id={self.parent_id!r})"


class FORGraph:
    """Graph of all frames of reference in a scene.

    This class manages a hierarchical collection of frames of reference,
    allowing traversal and transformation computations between any two frames.

    The graph is built from frame of reference events in a scene, where each
    frame has a position and rotation relative to its parent frame.
    """

    def __init__(self):
        """Initialize an empty FOR graph."""
        self._frames: Dict[str, FrameOfReference] = {}
        self._children: Dict[str, List[str]] = {}

    def add_frame(self, frame: FrameOfReference) -> None:
        """Add a frame of reference to the graph.

        Args:
            frame: The frame of reference to add.
        """
        self._frames[frame.id] = frame
        if frame.parent_id is not None:
            if frame.parent_id not in self._children:
                self._children[frame.parent_id] = []
            self._children[frame.parent_id].append(frame.id)

    def get_frame(self, for_id: str) -> FrameOfReference:
        """Get a frame of reference by ID.

        Args:
            for_id: The frame ID to look up.

        Returns:
            The frame of reference.

        Raises:
            KeyError: If the frame ID is not found.
        """
        if for_id not in self._frames:
            raise KeyError(f"Frame of reference '{for_id}' not found in graph")
        return self._frames[for_id]

    def has_frame(self, for_id: str) -> bool:
        """Check if a frame exists in the graph."""
        return for_id in self._frames

    def get_all_frame_ids(self) -> List[str]:
        """Get all frame IDs in the graph."""
        return list(self._frames.keys())

    def get_children(self, for_id: str) -> List[str]:
        """Get the IDs of all direct children of a frame."""
        return self._children.get(for_id, [])

    def get_path_to_root(self, for_id: str) -> List[str]:
        """Get the path from a frame to the root.

        Args:
            for_id: Starting frame ID.

        Returns:
            List of frame IDs from the given frame to root (inclusive).
        """
        path = [for_id]
        current = for_id

        while self._frames[current].parent_id is not None:
            parent_id = self._frames[current].parent_id
            if parent_id not in self._frames:
                # Parent is the implicit root (e.g., "root")
                break
            path.append(parent_id)
            current = parent_id

        return path

    def get_transform_to_world(self, for_id: str) -> NDArray[np.float64]:
        """Get the transformation matrix from a frame to world coordinates.

        This computes the composed transformation by multiplying matrices
        from the given frame up through all ancestors to the root.

        Args:
            for_id: The frame ID to transform from.

        Returns:
            4x4 transformation matrix to world coordinates.
        """
        path = self.get_path_to_root(for_id)

        # Start with identity
        result = np.eye(4, dtype=np.float64)

        # Compose transformations from local to world (bottom-up)
        for frame_id in path:
            frame = self._frames[frame_id]
            result = frame.get_transformation_matrix() @ result

        return result

    def get_transform_between(self, from_for: str, to_for: str) -> NDArray[np.float64]:
        """Get the transformation matrix between two frames.

        Computes the transformation that converts points from `from_for`
        coordinates to `to_for` coordinates.

        Args:
            from_for: Source frame ID.
            to_for: Target frame ID.

        Returns:
            4x4 transformation matrix from source to target.
        """
        # Transform from source to world, then from world to target
        from_to_world = self.get_transform_to_world(from_for)
        to_to_world = self.get_transform_to_world(to_for)

        # Inverse of to_to_world gives world_to_target
        world_to_target = np.linalg.inv(to_to_world)

        return world_to_target @ from_to_world

    def transform_points_to_world(self, points: NDArray[np.float64], from_for: str) -> NDArray[np.float64]:
        """Transform points from a frame's coordinates to world coordinates.

        Args:
            points: Array of shape (N, 3) containing 3D points.
            from_for: The frame ID the points are currently in.

        Returns:
            Transformed points in world coordinates as array of shape (N, 3).
        """
        points = np.asarray(points, dtype=np.float64)
        if points.ndim == 1:
            points = points.reshape(1, -1)

        transform = self.get_transform_to_world(from_for)

        # Apply homogeneous transformation
        n_points = points.shape[0]
        homogeneous = np.ones((n_points, 4), dtype=np.float64)
        homogeneous[:, :3] = points

        transformed = (transform @ homogeneous.T).T
        return transformed[:, :3]

    def transform_points(self, points: NDArray[np.float64], from_for: str, to_for: str) -> NDArray[np.float64]:
        """Transform points between two frames.

        Args:
            points: Array of shape (N, 3) containing 3D points.
            from_for: The frame ID the points are currently in.
            to_for: The frame ID to transform the points to.

        Returns:
            Transformed points as array of shape (N, 3).
        """
        points = np.asarray(points, dtype=np.float64)
        if points.ndim == 1:
            points = points.reshape(1, -1)

        transform = self.get_transform_between(from_for, to_for)

        # Apply homogeneous transformation
        n_points = points.shape[0]
        homogeneous = np.ones((n_points, 4), dtype=np.float64)
        homogeneous[:, :3] = points

        transformed = (transform @ homogeneous.T).T
        return transformed[:, :3]

    @classmethod
    def from_scene_data(cls, scene_data: "SceneData") -> "FORGraph":  # noqa: F821
        """Build a FOR graph from scene data.

        Args:
            scene_data: The scene data containing frame of reference streams.

        Returns:
            A FORGraph populated with all frames from the scene.
        """
        from encord.orm.scene import FrameOfReferenceStream

        graph = cls()

        # Extract all frame of reference streams
        for_streams = scene_data.get_streams("frame_of_reference")

        for stream_id, stream in for_streams.items():
            if isinstance(stream, FrameOfReferenceStream):
                for event in stream.events:
                    # Convert rotation from 9-element list to 3x3 matrix
                    rotation = np.array(event.rotation, dtype=np.float64).reshape(3, 3)
                    position = np.array(event.position, dtype=np.float64)

                    parent_id = event.parent_FOR if event.parent_FOR != "root" else None

                    frame = FrameOfReference(
                        for_id=event.id,
                        parent_id=parent_id,
                        position=position,
                        rotation=rotation,
                    )
                    graph.add_frame(frame)

        return graph

    def __len__(self) -> int:
        return len(self._frames)

    def __repr__(self) -> str:
        return f"FORGraph(frames={len(self._frames)})"
