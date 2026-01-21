"""Scene SDK for working with 3D scene data.

This module provides the main entry point for working with scene data,
including point clouds, frames of reference, and coordinate transformations.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Dict, List, Literal, Optional, Union, overload

if TYPE_CHECKING:
    import numpy as np

from encord.orm.scene import ImageStream, PointCloudStream, SceneData
from encord.scene.pcd_loader import PointCloud
from encord.scene.transformations import FORGraph


class Scene:
    """Main Scene SDK class for working with 3D scene data.

    This class provides methods to:
    - Access scene metadata and streams
    - Load point clouds from signed URLs
    - Build and traverse the frame of reference (FOR) graph
    - Transform coordinates between different frames of reference

    Example:
        >>> # Get a scene from a storage item
        >>> storage_item = encord_user_client.get_storage_item(item_uuid)
        >>> scene = storage_item.get_scene()
        >>>
        >>> # Load a point cloud
        >>> pc_streams = scene.get_streams("point_cloud")
        >>> point_cloud = scene.load_point_cloud(pc_streams[0].stream_id, event_index=0)
        >>>
        >>> # Transform to world coordinates
        >>> for_graph = scene.get_for_graph()
        >>> world_points = for_graph.transform_points_to_world(
        ...     point_cloud.points, from_for="LIDAR_TOP-calibration"
        ... )
    """

    def __init__(self, scene_data: SceneData):
        """Initialize a Scene from scene data.

        Args:
            scene_data: The SceneData ORM model containing the scene definition.
        """
        self._scene_data = scene_data
        self._for_graph: Optional[FORGraph] = None

    @classmethod
    def from_dict(cls, data: Dict) -> "Scene":
        """Create a Scene from a dictionary (JSON response).

        Args:
            data: Dictionary containing scene data.

        Returns:
            A Scene object.
        """
        scene_data = SceneData.model_validate(data)
        return cls(scene_data)

    @property
    def scene_type(self) -> str:
        """Get the scene type ('composite' or 'self_contained')."""
        return self._scene_data.type

    @property
    def world_convention(self):
        """Get the world coordinate convention."""
        return self._scene_data.worldConvention

    @property
    def camera_convention(self):
        """Get the camera coordinate convention."""
        return self._scene_data.cameraConvention

    @property
    def default_ground_height(self) -> Optional[float]:
        """Get the default ground height, if specified."""
        return self._scene_data.defaultGroundHeight

    @overload
    def get_streams(self, kind: Literal["point_cloud"]) -> List[PointCloudStreamInfo]: ...

    @overload
    def get_streams(self, kind: Literal["image"]) -> List[ImageStreamInfo]: ...

    def get_streams(
        self, kind: Literal["point_cloud", "image"]
    ) -> Union[List[PointCloudStreamInfo], List[ImageStreamInfo]]:
        if kind == "point_cloud":
            pc_streams = self._scene_data.get_streams("point_cloud")
            return [PointCloudStreamInfo(stream_id=sid, stream=s) for sid, s in pc_streams.items()]
        elif kind == "image":
            img_streams = self._scene_data.get_streams("image")
            return [ImageStreamInfo(stream_id=sid, stream=s) for sid, s in img_streams.items()]
        else:
            raise ValueError(f"Unknown stream kind: {kind}")

    def get_for_graph(self) -> FORGraph:
        """Build and return the frame of reference graph.

        The graph is cached after the first call.

        Returns:
            FORGraph containing all frames of reference in the scene.
        """
        if self._for_graph is None:
            self._for_graph = FORGraph.from_scene_data(self._scene_data)
        return self._for_graph

    def load_point_cloud(
        self,
        stream_id: str,
        event_index: int = 0,
        timeout: float = 30.0,
        use_cache: bool = False,
    ) -> PointCloud:
        """Load a point cloud from a stream (synchronous).

        Args:
            stream_id: ID of the point cloud stream.
            event_index: Index of the event (frame) to load.
            timeout: Download timeout in seconds.
            use_cache: If True, cache downloaded files locally for faster reloading.

        Returns:
            A PointCloud object with the loaded data.

        Raises:
            KeyError: If the stream ID is not found.
            IndexError: If the event index is out of range.
            ValueError: If the stream is not a point cloud stream.
        """
        stream_info = self._get_point_cloud_stream(stream_id)
        download_url = stream_info.get_event_url(event_index)
        cache_key = stream_info.get_event_stable_url(event_index) if use_cache else None
        return PointCloud.from_url(download_url, timeout=timeout, cache_key=cache_key)

    async def load_point_cloud_async(
        self,
        stream_id: str,
        event_index: int = 0,
        timeout: float = 30.0,
        use_cache: bool = False,
    ) -> PointCloud:
        """Load a point cloud from a stream (asynchronous).

        Args:
            stream_id: ID of the point cloud stream.
            event_index: Index of the event (frame) to load.
            timeout: Download timeout in seconds.
            use_cache: If True, cache downloaded files locally for faster reloading.

        Returns:
            A PointCloud object with the loaded data.

        Raises:
            KeyError: If the stream ID is not found.
            IndexError: If the event index is out of range.
            ValueError: If the stream is not a point cloud stream.
        """
        stream_info = self._get_point_cloud_stream(stream_id)
        download_url = stream_info.get_event_url(event_index)
        cache_key = stream_info.get_event_stable_url(event_index) if use_cache else None
        return await PointCloud.from_url_async(download_url, timeout=timeout, cache_key=cache_key)

    async def load_all_point_clouds_async(
        self,
        stream_id: str,
        timeout: float = 60.0,
        max_concurrent: int = 10,
        use_cache: bool = False,
    ) -> List[PointCloud]:
        """Load all point clouds from a stream in parallel (asynchronous).

        Args:
            stream_id: ID of the point cloud stream.
            timeout: Download timeout in seconds for each file.
            max_concurrent: Maximum number of concurrent downloads.
            use_cache: If True, cache downloaded files locally for faster reloading.

        Returns:
            List of PointCloud objects, one for each event in the stream.

        Raises:
            KeyError: If the stream ID is not found.
            ValueError: If the stream is not a point cloud stream.
        """
        stream_info = self._get_point_cloud_stream(stream_id)
        num_events = stream_info.num_events

        semaphore = asyncio.Semaphore(max_concurrent)

        async def load_with_limit(index: int) -> PointCloud:
            async with semaphore:
                download_url = stream_info.get_event_url(index)
                cache_key = stream_info.get_event_stable_url(index) if use_cache else None
                return await PointCloud.from_url_async(download_url, timeout=timeout, cache_key=cache_key)

        tasks = [load_with_limit(i) for i in range(num_events)]
        return await asyncio.gather(*tasks)

    def load_point_cloud_in_world_coordinates(
        self,
        stream_id: str,
        event_index: int = 0,
        timeout: float = 30.0,
        use_cache: bool = False,
    ) -> PointCloud:
        """Load a point cloud and transform it to world coordinates.

        Args:
            stream_id: ID of the point cloud stream.
            event_index: Index of the event (frame) to load.
            timeout: Download timeout in seconds.
            use_cache: If True, cache downloaded files locally for faster reloading.

        Returns:
            A PointCloud object with points in world coordinates.
        """
        import numpy as np

        point_cloud = self.load_point_cloud(stream_id, event_index, timeout, use_cache=use_cache)

        # Get transform for this specific frame
        transform = self.get_sensor_to_world_transform(stream_id, event_index)
        if transform is not None:
            return point_cloud.transform(transform)

        return point_cloud

    def get_sensor_to_world_transform(
        self,
        stream_id: str,
        event_index: int,
    ) -> Optional["np.ndarray"]:
        """Get the 4x4 transform matrix from sensor to world coordinates for a specific frame.

        This combines:
        - Static sensor calibration (e.g., LIDAR_TOP-calibration)
        - Frame-specific ego vehicle pose

        Args:
            stream_id: ID of the sensor stream.
            event_index: Index of the event (frame).

        Returns:
            4x4 transformation matrix, or None if no transform is available.
        """
        import numpy as np

        stream_info = self._get_point_cloud_stream(stream_id)
        sensor_for_id = stream_info.frame_of_reference_id
        if sensor_for_id is None:
            return None

        # Get FOR streams
        for_streams = self._scene_data.get_streams("frame_of_reference")

        # Build sensor calibration transform (static)
        sensor_transform = np.eye(4, dtype=np.float64)
        sensor_calib_stream = for_streams.get(sensor_for_id)
        if sensor_calib_stream and len(sensor_calib_stream.events) > 0:
            # Calibration is usually static (one event), but use first
            event = sensor_calib_stream.events[0]
            rotation = np.array(event.rotation, dtype=np.float64).reshape(3, 3)
            position = np.array(event.position, dtype=np.float64)
            sensor_transform[:3, :3] = rotation
            sensor_transform[:3, 3] = position

        # Build ego vehicle transform for this specific frame
        ego_transform = np.eye(4, dtype=np.float64)
        ego_stream = for_streams.get("ego_vehicle")
        if ego_stream and event_index < len(ego_stream.events):
            event = ego_stream.events[event_index]
            rotation = np.array(event.rotation, dtype=np.float64).reshape(3, 3)
            position = np.array(event.position, dtype=np.float64)
            ego_transform[:3, :3] = rotation
            ego_transform[:3, 3] = position

        # Combined transform: sensor -> ego -> world
        # Points in sensor coords -> multiply by sensor_calib -> ego coords
        # Points in ego coords -> multiply by ego_pose -> world coords
        return ego_transform @ sensor_transform

    def _get_point_cloud_stream(self, stream_id: str) -> "PointCloudStreamInfo":
        """Get a point cloud stream by ID."""
        pc_streams = self._scene_data.get_streams("point_cloud")
        if stream_id not in pc_streams:
            raise KeyError(f"Point cloud stream '{stream_id}' not found")
        return PointCloudStreamInfo(stream_id=stream_id, stream=pc_streams[stream_id])


class PointCloudStreamInfo:
    """Information about a point cloud stream in a scene."""

    def __init__(self, stream_id: str, stream: PointCloudStream):
        """Initialize point cloud stream info.

        Args:
            stream_id: The stream identifier.
            stream: The PointCloudStream data.
        """
        self._stream_id = stream_id
        self._stream = stream

    @property
    def stream_id(self) -> str:
        """Get the stream ID."""
        return self._stream_id

    @property
    def frame_of_reference_id(self) -> Optional[str]:
        """Get the frame of reference ID for this stream."""
        return self._stream.frameOfReferenceId

    @property
    def num_events(self) -> int:
        """Get the number of events (frames) in this stream."""
        return len(self._stream.events)

    def get_event_url(self, index: int) -> str:
        """Get the download URL for a specific event.

        Args:
            index: The event index.

        Returns:
            The signed URL for downloading the point cloud file.

        Raises:
            IndexError: If the index is out of range.
        """
        if index < 0 or index >= len(self._stream.events):
            raise IndexError(f"Event index {index} out of range (0-{len(self._stream.events) - 1})")
        return self._stream.events[index].download_url

    def get_event_stable_url(self, index: int) -> str:
        """Get the stable (unsigned) URL for a specific event.

        This URL is suitable for use as a cache key since it doesn't change
        when signed URLs are regenerated.

        Args:
            index: The event index.

        Returns:
            The stable/unsigned URL for the point cloud file.

        Raises:
            IndexError: If the index is out of range.
        """
        if index < 0 or index >= len(self._stream.events):
            raise IndexError(f"Event index {index} out of range (0-{len(self._stream.events) - 1})")
        return self._stream.events[index].stable_url

    def get_event_timestamp(self, index: int) -> float:
        """Get the timestamp for a specific event.

        Args:
            index: The event index.

        Returns:
            The timestamp value.

        Raises:
            IndexError: If the index is out of range.
        """
        if index < 0 or index >= len(self._stream.events):
            raise IndexError(f"Event index {index} out of range (0-{len(self._stream.events) - 1})")
        return self._stream.events[index].timestamp

    def get_all_urls(self) -> List[str]:
        """Get all event download URLs in order."""
        return [event.download_url for event in self._stream.events]

    def get_all_timestamps(self) -> List[float]:
        """Get all event timestamps in order."""
        return [event.timestamp for event in self._stream.events]

    def __repr__(self) -> str:
        return f"PointCloudStreamInfo(stream_id={self._stream_id!r}, num_events={self.num_events})"


class ImageStreamInfo:
    """Information about an image stream in a scene."""

    def __init__(self, stream_id: str, stream: ImageStream):
        """Initialize image stream info.

        Args:
            stream_id: The stream identifier.
            stream: The ImageStream data.
        """
        self._stream_id = stream_id
        self._stream = stream

    @property
    def stream_id(self) -> str:
        """Get the stream ID."""
        return self._stream_id

    @property
    def camera_id(self) -> Optional[str]:
        """Get the camera ID for this stream."""
        return self._stream.cameraId

    @property
    def num_events(self) -> int:
        """Get the number of events (frames) in this stream."""
        return len(self._stream.events)

    def get_event_url(self, index: int) -> str:
        """Get the download URL for a specific event.

        Args:
            index: The event index.

        Returns:
            The signed URL for downloading the image file.

        Raises:
            IndexError: If the index is out of range.
        """
        if index < 0 or index >= len(self._stream.events):
            raise IndexError(f"Event index {index} out of range (0-{len(self._stream.events) - 1})")
        return self._stream.events[index].download_url

    def get_event_stable_url(self, index: int) -> str:
        """Get the stable (unsigned) URL for a specific event.

        This URL is suitable for use as a cache key since it doesn't change
        when signed URLs are regenerated.

        Args:
            index: The event index.

        Returns:
            The stable/unsigned URL for the image file.

        Raises:
            IndexError: If the index is out of range.
        """
        if index < 0 or index >= len(self._stream.events):
            raise IndexError(f"Event index {index} out of range (0-{len(self._stream.events) - 1})")
        return self._stream.events[index].stable_url

    def get_event_timestamp(self, index: int) -> float:
        """Get the timestamp for a specific event.

        Args:
            index: The event index.

        Returns:
            The timestamp value.

        Raises:
            IndexError: If the index is out of range.
        """
        if index < 0 or index >= len(self._stream.events):
            raise IndexError(f"Event index {index} out of range (0-{len(self._stream.events) - 1})")
        return self._stream.events[index].timestamp

    def get_all_urls(self) -> List[str]:
        """Get all event download URLs in order."""
        return [event.download_url for event in self._stream.events]

    def get_all_timestamps(self) -> List[float]:
        """Get all event timestamps in order."""
        return [event.timestamp for event in self._stream.events]

    def __repr__(self) -> str:
        return f"ImageStreamInfo(stream_id={self._stream_id!r}, num_events={self.num_events})"
