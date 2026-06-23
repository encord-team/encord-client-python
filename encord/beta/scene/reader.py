"""Public SDK scene read types.

These are stable SDK types that insulate users from the internal wire format.
They are constructed from the internal types in ``beta/scene/internal/scene.py``.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, cast, overload

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
from encord.beta.scene.scene_to_upload_playload import scene_to_upload_payload
from encord.common.deprecated import deprecated
from encord.orm import storage as orm_storage
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


class SceneReader:
    """Read scene structure and signed URLs from a scene storage item."""

    def __init__(self, item: "StorageItem") -> None:
        if item.item_type != StorageItemType.SCENE:
            raise ValueError(f"Storage item {item.uuid} is not a scene (item_type={item.item_type})")
        self._item = item
        self._internal_scene: _Scene | None = None

    def _read_internal_scene(self) -> _Scene:
        if self._internal_scene is None:
            self._internal_scene = cast(
                _Scene,
                self._item._api_client.get(
                    f"scene/{self._item.uuid}",
                    params=None,
                    result_type=_SceneResponse,
                ).root,
            )
        return self._internal_scene

    def read(self) -> Scene:
        """Fetch the scene structure with signed download URLs for all constituent files."""
        return scene_from_internal(self._read_internal_scene())

    def to_upload_payload(
        self,
        title: str | None = None,
        *,
        client_metadata: dict[str, Any] | None = None,
        uri_mapper: Callable[[str], str] | Mapping[str, str] | None = None,
    ) -> orm_storage.DataUploadScene:
        """Fetch this scene and convert it to a ``DataUploadScene`` for re-upload.

        Args:
            title: Title to use for the uploaded scene. Defaults to the source storage item name.
            client_metadata: Metadata for the uploaded scene. Defaults to the source item metadata.
            uri_mapper: Optional callable or mapping used to rewrite each stored URI before upload.

        Returns:
            A scene upload payload suitable for ``DataUploadItems(scenes=[...])``.
        """
        metadata = self._item.client_metadata if client_metadata is None else client_metadata
        return orm_storage.DataUploadScene(
            title=title or self._item.name,
            scene=scene_to_upload_payload(self._read_internal_scene(), uri_mapper=uri_mapper),
            client_metadata=metadata or {},
        )


@deprecated(version="0.1.198", alternative="SceneReader")
class SceneRead(SceneReader):
    """Deprecated alias for :class:`SceneReader`."""


def scene_from_internal(internal: _Scene) -> Scene:
    if isinstance(internal, _SelfContainedScene):
        raise ValueError("Single-file scenes are not supported in the SDK yet")

    min_timestamp = min(
        (
            event.timestamp
            for stream in internal.streams.values()
            if isinstance(stream, _EventStream)
            for event in stream.stream.events
            if event.timestamp is not None
        ),
        default=0,
    )
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
                    events=[
                        SceneEvent(
                            timestamp=e.timestamp if e.timestamp is not None else min_timestamp + index,
                            url=e.url,
                            signed_url=e.signed_url,
                        )
                        for index, e in enumerate(inner.events)
                    ],
                )
            )
        elif isinstance(inner, _ImageStream):
            image_streams.append(
                ImageStream(
                    stream_id=stream_id,
                    events=[
                        SceneEvent(
                            timestamp=e.timestamp if e.timestamp is not None else min_timestamp + index,
                            url=e.url,
                            signed_url=e.signed_url,
                        )
                        for index, e in enumerate(inner.events)
                    ],
                )
            )
    return CompositeScene(point_cloud_streams=point_cloud_streams, image_streams=image_streams)
