"""Public SDK scene read types.

These are stable SDK types that insulate users from the internal wire format.
They are constructed from the internal types in ``beta/scene/internal/scene.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, cast, overload

from encord.beta.scene.internal.scene import (
    EventStream as _EventStream,
)
from encord.beta.scene.internal.scene import (
    ImageStream as _ImageStream,
)
from encord.beta.scene.internal.scene import (
    PCDStream as _PCDStream,
)
from encord.beta.scene.internal.scene import (
    Scene as _Scene,
)
from encord.beta.scene.internal.scene import (
    SceneResponse as _SceneResponse,
)
from encord.beta.scene.internal.scene import (
    SelfContainedScene as _SelfContainedScene,
)
from encord.orm.storage import StorageItemType

if TYPE_CHECKING:
    from encord.storage import StorageItem


@dataclass
class SceneEvent:
    """A single event in a stream, with its signed download URL and timestamp."""

    timestamp: float
    """Timestamp of the event."""
    url: str
    """Raw unsigned URI as stored in the scene definition."""
    signed_url: str
    """Time-limited signed URL for downloading the file."""


@dataclass
class PointCloudStream:
    """A stream of lidar point cloud events."""

    stream_id: str
    events: list[SceneEvent]

    @property
    def num_events(self) -> int:
        return len(self.events)

    def find_event(self, timestamp: float) -> SceneEvent | None:
        """Return the event with the given timestamp, or ``None`` if not present."""
        for event in self.events:
            if event.timestamp == timestamp:
                return event
        return None

    def get_event(self, timestamp: float) -> SceneEvent:
        """Return the event with the given timestamp.

        Raises:
            KeyError: If no event with that timestamp exists.
        """
        event = self.find_event(timestamp)
        if event is None:
            raise KeyError(f"No event with timestamp {timestamp} for stream '{self.stream_id}'")
        return event


@dataclass
class ImageStream:
    """A stream of camera image events."""

    stream_id: str
    events: list[SceneEvent]

    @property
    def num_events(self) -> int:
        return len(self.events)

    def find_event(self, timestamp: float) -> SceneEvent | None:
        """Return the event with the given timestamp, or ``None`` if not present."""
        for event in self.events:
            if event.timestamp == timestamp:
                return event
        return None

    def get_event(self, timestamp: float) -> SceneEvent:
        """Return the event with the given timestamp.

        Raises:
            KeyError: If no event with that timestamp exists.
        """
        event = self.find_event(timestamp)
        if event is None:
            raise KeyError(f"No event with timestamp {timestamp} for stream '{self.stream_id}'")
        return event


@dataclass
class CompositeScene:
    """A scene composed of multiple named streams (lidar + cameras)."""

    point_cloud_streams: list[PointCloudStream]
    image_streams: list[ImageStream]

    @overload
    def find_stream(self, stream_id: str, *, kind: Literal["point_cloud"]) -> PointCloudStream | None: ...

    @overload
    def find_stream(self, stream_id: str, *, kind: Literal["image"]) -> ImageStream | None: ...

    def find_stream(
        self, stream_id: str, *, kind: Literal["point_cloud", "image"]
    ) -> PointCloudStream | ImageStream | None:
        """Return the stream with the given ID and kind, or ``None`` if not present."""
        if kind == "point_cloud":
            for pcd_stream in self.point_cloud_streams:
                if pcd_stream.stream_id == stream_id:
                    return pcd_stream
            return None
        if kind == "image":
            for image_stream in self.image_streams:
                if image_stream.stream_id == stream_id:
                    return image_stream
            return None
        raise ValueError(f"Unsupported stream kind '{kind}'")

    @overload
    def get_stream(self, stream_id: str, *, kind: Literal["point_cloud"]) -> PointCloudStream: ...

    @overload
    def get_stream(self, stream_id: str, *, kind: Literal["image"]) -> ImageStream: ...

    def get_stream(self, stream_id: str, *, kind: Literal["point_cloud", "image"]) -> PointCloudStream | ImageStream:
        """Return the stream with the given ID and kind.

        Raises:
            KeyError: If no stream with that ID and kind exists.
        """
        stream = self.find_stream(stream_id, kind=kind)
        if stream is None:
            available = [
                s.stream_id for s in (self.point_cloud_streams if kind == "point_cloud" else self.image_streams)
            ]
            kind_name = "point cloud" if kind == "point_cloud" else "image"
            raise KeyError(f"No {kind_name} stream with id '{stream_id}'. Available: {available}")
        return stream

    def get_images_at_timestamp(self, timestamp: float) -> list[tuple[str, SceneEvent]]:
        """Return camera image events at the given timestamp across image streams.

        Streams without a matching event are skipped.
        """
        results = []
        for s in self.image_streams:
            event = s.find_event(timestamp)
            if event is not None:
                results.append((s.stream_id, event))
        return results


Scene = CompositeScene


class SceneRead:
    """Read scene structure and signed URLs from a scene storage item."""

    def __init__(self, item: "StorageItem") -> None:
        if item.item_type != StorageItemType.SCENE:
            raise ValueError(f"Storage item {item.uuid} is not a scene (item_type={item.item_type})")
        self._item = item

    def read(self) -> Scene:
        """Fetch the scene structure with signed download URLs for all constituent files."""
        internal = self._item._api_client.get(
            f"scene/{self._item.uuid}",
            params=None,
            result_type=_SceneResponse,
        ).root
        return scene_from_internal(cast(_Scene, internal))


def scene_from_internal(internal: _Scene) -> Scene:
    if isinstance(internal, _SelfContainedScene):
        raise ValueError("Single-file scenes are not supported in the SDK yet")

    point_cloud_streams: list[PointCloudStream] = []
    image_streams: list[ImageStream] = []
    for stream_id, stream in internal.streams.items():
        if not isinstance(stream, _EventStream):
            continue
        inner = stream.stream
        if isinstance(inner, _PCDStream):
            point_cloud_streams.append(
                PointCloudStream(
                    stream_id=stream_id,
                    events=[_scene_event(stream_id, e.timestamp, e.url, e.signed_url) for e in inner.events],
                )
            )
        elif isinstance(inner, _ImageStream):
            image_streams.append(
                ImageStream(
                    stream_id=stream_id,
                    events=[_scene_event(stream_id, e.timestamp, e.url, e.signed_url) for e in inner.events],
                )
            )
    return CompositeScene(point_cloud_streams=point_cloud_streams, image_streams=image_streams)


def _scene_event(stream_id: str, timestamp: float | None, url: str, signed_url: str) -> SceneEvent:
    if timestamp is None:
        raise ValueError(f"Scene stream '{stream_id}' contains an event without a timestamp")
    return SceneEvent(timestamp=timestamp, url=url, signed_url=signed_url)
