"""Public read API for Encord scenes.

Provides read-only wrappers around internal DB models, matching the style
of ``builder.py`` (which wraps ``internal/upload.py``).
"""

from __future__ import annotations

from encord.scene.internal.common import Convention, SelfContainedFormat
from encord.scene.internal.read import (
    CameraIntrinsics,
    CameraParamsEvent as _CameraParamsEvent,
    CameraStream as _CameraStream,
    DbCompositeScene as _DbCompositeScene,
    DbEventStream as _DbEventStream,
    DbImageStream as _DbImageStream,
    DbPCDStream as _DbPCDStream,
    DbSceneAdapter as _DbSceneAdapter,
    DbSelfContainedScene as _DbSelfContainedScene,
    DbURIEvent as _DbURIEvent,
    FOREvent as _FOREvent,
    FORStream as _FORStream,
    Position,
    RotationMatrix,
)

__all__ = [
    "CameraChannel",
    "CameraEvent",
    "CameraIntrinsics",
    "Convention",
    "FoRChannel",
    "FoREvent",
    "ImageChannel",
    "ImageEvent",
    "PCDChannel",
    "PCDEvent",
    "Position",
    "RotationMatrix",
    "Scene",
    "SelfContainedFormat",
]

# ---------------------------------------------------------------------------
# Event classes
# ---------------------------------------------------------------------------


class PCDEvent:
    """A single point-cloud frame."""

    def __init__(self, scene: Scene, inner: _DbURIEvent) -> None:
        self._scene = scene
        self._inner = inner

    @property
    def uri(self) -> str:
        return self._inner.uri

    @property
    def timestamp(self) -> float | None:
        return self._inner.timestamp

    def __repr__(self) -> str:
        return f"PCDEvent(uri={self._inner.uri!r}, timestamp={self._inner.timestamp!r})"


class ImageEvent:
    """A single image frame."""

    def __init__(self, scene: Scene, inner: _DbURIEvent) -> None:
        self._scene = scene
        self._inner = inner

    @property
    def uri(self) -> str:
        return self._inner.uri

    @property
    def timestamp(self) -> float | None:
        return self._inner.timestamp

    def __repr__(self) -> str:
        return f"ImageEvent(uri={self._inner.uri!r}, timestamp={self._inner.timestamp!r})"


class CameraEvent:
    """Camera parameters at a point in time."""

    def __init__(self, scene: Scene, inner: _CameraParamsEvent) -> None:
        self._scene = scene
        self._inner = inner

    @property
    def width_px(self) -> int:
        return self._inner.width_px

    @property
    def height_px(self) -> int:
        return self._inner.height_px

    @property
    def intrinsics(self) -> CameraIntrinsics:
        return self._inner.intrinsics

    @property
    def timestamp(self) -> float | None:
        return self._inner.timestamp

    def __repr__(self) -> str:
        return (
            f"CameraEvent(width_px={self._inner.width_px}, "
            f"height_px={self._inner.height_px}, timestamp={self._inner.timestamp!r})"
        )


class FoREvent:
    """Frame-of-reference pose at a point in time."""

    def __init__(self, scene: Scene, inner: _FOREvent) -> None:
        self._scene = scene
        self._inner = inner

    @property
    def id(self) -> str:
        return self._inner.id

    @property
    def parent_for_id(self) -> str | None:
        return self._inner.parent_FOR

    @property
    def rotation(self) -> RotationMatrix:
        return self._inner.rotation

    @property
    def position(self) -> Position:
        return self._inner.position

    @property
    def timestamp(self) -> float | None:
        return self._inner.timestamp

    def __repr__(self) -> str:
        return f"FoREvent(id={self._inner.id!r}, timestamp={self._inner.timestamp!r})"


# ---------------------------------------------------------------------------
# Channel classes
# ---------------------------------------------------------------------------


class PCDChannel:
    """Read-only view of a point-cloud stream."""

    def __init__(self, scene: Scene, name: str, inner: _DbPCDStream) -> None:
        self._scene = scene
        self._name = name
        self._inner = inner

    @property
    def name(self) -> str:
        return self._name

    @property
    def frame_of_reference_id(self) -> str | None:
        return self._inner.frame_of_reference_id

    @property
    def events(self) -> list[PCDEvent]:
        return [PCDEvent(self._scene, e) for e in self._inner.events]

    def __repr__(self) -> str:
        return f"PCDChannel(name={self._name!r}, events={len(self._inner.events)})"


class ImageChannel:
    """Read-only view of an image stream."""

    def __init__(self, scene: Scene, name: str, inner: _DbImageStream) -> None:
        self._scene = scene
        self._name = name
        self._inner = inner

    @property
    def name(self) -> str:
        return self._name

    @property
    def camera_id(self) -> str | None:
        return self._inner.camera_id

    @property
    def events(self) -> list[ImageEvent]:
        return [ImageEvent(self._scene, e) for e in self._inner.events]

    def __repr__(self) -> str:
        return f"ImageChannel(name={self._name!r}, events={len(self._inner.events)})"


class CameraChannel:
    """Read-only view of a camera-parameters stream."""

    def __init__(self, scene: Scene, name: str, inner: _CameraStream) -> None:
        self._scene = scene
        self._name = name
        self._inner = inner

    @property
    def name(self) -> str:
        return self._name

    @property
    def frame_of_reference_id(self) -> str | None:
        return self._inner.frame_of_reference_id

    @property
    def events(self) -> list[CameraEvent]:
        return [CameraEvent(self._scene, e) for e in self._inner.events]

    def __repr__(self) -> str:
        return f"CameraChannel(name={self._name!r}, events={len(self._inner.events)})"


class FoRChannel:
    """Read-only view of a frame-of-reference stream."""

    def __init__(self, scene: Scene, name: str, inner: _FORStream) -> None:
        self._scene = scene
        self._name = name
        self._inner = inner

    @property
    def name(self) -> str:
        return self._name

    @property
    def events(self) -> list[FoREvent]:
        return [FoREvent(self._scene, e) for e in self._inner.events]

    def __repr__(self) -> str:
        return f"FoRChannel(name={self._name!r}, events={len(self._inner.events)})"


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------


class Scene:
    """Read-only view of an Encord scene.

    Wraps both self-contained and composite scene types.
    Use :meth:`from_dict` to parse a scene from a raw dictionary.
    """

    def __init__(self, inner: _DbSelfContainedScene | _DbCompositeScene) -> None:
        self._inner = inner

    # -- Config properties ------------------------------------------------

    @property
    def ground_height(self) -> float | None:
        return self._inner.default_ground_height

    @property
    def world_convention(self) -> Convention:
        return self._inner.world_convention

    @property
    def camera_convention(self) -> Convention:
        return self._inner.camera_convention

    # -- Self-contained properties ----------------------------------------

    @property
    def uri(self) -> str | None:
        if isinstance(self._inner, _DbSelfContainedScene):
            return self._inner.uri
        return None

    @property
    def format(self) -> SelfContainedFormat | None:
        if isinstance(self._inner, _DbSelfContainedScene):
            return self._inner.format
        return None

    # -- Channel accessors (composite only) -------------------------------

    def _get_event_stream(self, name: str) -> _DbEventStream:
        if not isinstance(self._inner, _DbCompositeScene):
            raise TypeError("Channel accessors are only available on composite scenes")
        stream = self._inner.streams.get(name)
        if stream is None:
            raise KeyError(f"No stream named {name!r}")
        if not isinstance(stream, _DbEventStream):
            raise TypeError(f"Stream {name!r} is not an event stream")
        return stream

    def get_pcd_channel(self, name: str) -> PCDChannel:
        stream = self._get_event_stream(name)
        if not isinstance(stream.stream, _DbPCDStream):
            raise TypeError(f"Stream {name!r} is not a point-cloud stream")
        return PCDChannel(self, name, stream.stream)

    def get_image_channel(self, name: str) -> ImageChannel:
        stream = self._get_event_stream(name)
        if not isinstance(stream.stream, _DbImageStream):
            raise TypeError(f"Stream {name!r} is not an image stream")
        return ImageChannel(self, name, stream.stream)

    def get_camera_channel(self, name: str) -> CameraChannel:
        stream = self._get_event_stream(name)
        if not isinstance(stream.stream, _CameraStream):
            raise TypeError(f"Stream {name!r} is not a camera-parameters stream")
        return CameraChannel(self, name, stream.stream)

    def get_for_channel(self, name: str) -> FoRChannel:
        stream = self._get_event_stream(name)
        if not isinstance(stream.stream, _FORStream):
            raise TypeError(f"Stream {name!r} is not a frame-of-reference stream")
        return FoRChannel(self, name, stream.stream)

    # -- Discovery properties ---------------------------------------------

    def _iter_event_streams(self) -> dict[str, _DbEventStream]:
        if not isinstance(self._inner, _DbCompositeScene):
            return {}
        return {
            name: stream
            for name, stream in self._inner.streams.items()
            if isinstance(stream, _DbEventStream)
        }

    @property
    def pcd_channels(self) -> dict[str, PCDChannel]:
        return {
            name: PCDChannel(self, name, stream.stream)
            for name, stream in self._iter_event_streams().items()
            if isinstance(stream.stream, _DbPCDStream)
        }

    @property
    def image_channels(self) -> dict[str, ImageChannel]:
        return {
            name: ImageChannel(self, name, stream.stream)
            for name, stream in self._iter_event_streams().items()
            if isinstance(stream.stream, _DbImageStream)
        }

    @property
    def camera_channels(self) -> dict[str, CameraChannel]:
        return {
            name: CameraChannel(self, name, stream.stream)
            for name, stream in self._iter_event_streams().items()
            if isinstance(stream.stream, _CameraStream)
        }

    @property
    def for_channels(self) -> dict[str, FoRChannel]:
        return {
            name: FoRChannel(self, name, stream.stream)
            for name, stream in self._iter_event_streams().items()
            if isinstance(stream.stream, _FORStream)
        }

    # -- Factory ----------------------------------------------------------

    @staticmethod
    def from_dict(data: dict) -> Scene:
        """Parse a scene from a raw dictionary via the internal adapter."""
        parsed = _DbSceneAdapter.validate_python(data)
        return Scene(parsed)

    def __repr__(self) -> str:
        if isinstance(self._inner, _DbSelfContainedScene):
            return f"Scene(type='self_contained', uri={self._inner.uri!r})"
        stream_count = len(self._inner.streams)
        return f"Scene(type='composite', streams={stream_count})"
