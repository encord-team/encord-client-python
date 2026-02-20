"""Public read API for Encord scenes.

Provides read-only wrappers around internal DB models, matching the style
of ``builder.py`` (which wraps ``internal/upload.py``).
"""

from __future__ import annotations

from typing import TypeVar, Union

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
    "SceneSnapshot",
    "SelfContainedFormat",
    "Transform",
]

_ROOT_FOR = "root"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_E = TypeVar("_E")


def _resolve_at(events: list[_E], timestamp: float) -> _E | None:
    """Return the latest event whose timestamp <= *timestamp*, or ``None``."""
    best: _E | None = None
    best_ts: float = -float("inf")
    for e in events:
        ts = e.timestamp  # type: ignore[attr-defined]
        if ts is not None and ts <= timestamp and ts > best_ts:
            best = e
            best_ts = ts
    return best


def _mat_mul(a: RotationMatrix, b: RotationMatrix) -> RotationMatrix:
    """Multiply two 3x3 rotation matrices stored as column-major 9-tuples.

    Column-major layout::

        | m[0]  m[3]  m[6] |
        | m[1]  m[4]  m[7] |
        | m[2]  m[5]  m[8] |

    Element access: matrix[row][col] = flat[col * 3 + row]
    """
    return (
        a[0] * b[0] + a[3] * b[1] + a[6] * b[2],
        a[1] * b[0] + a[4] * b[1] + a[7] * b[2],
        a[2] * b[0] + a[5] * b[1] + a[8] * b[2],
        a[0] * b[3] + a[3] * b[4] + a[6] * b[5],
        a[1] * b[3] + a[4] * b[4] + a[7] * b[5],
        a[2] * b[3] + a[5] * b[4] + a[8] * b[5],
        a[0] * b[6] + a[3] * b[7] + a[6] * b[8],
        a[1] * b[6] + a[4] * b[7] + a[7] * b[8],
        a[2] * b[6] + a[5] * b[7] + a[8] * b[8],
    )


def _mat_vec(r: RotationMatrix, v: Position) -> Position:
    """Multiply a column-major 3x3 matrix by a 3-vector."""
    return (
        r[0] * v[0] + r[3] * v[1] + r[6] * v[2],
        r[1] * v[0] + r[4] * v[1] + r[7] * v[2],
        r[2] * v[0] + r[5] * v[1] + r[8] * v[2],
    )


_IDENTITY_ROTATION: RotationMatrix = (1, 0, 0, 0, 1, 0, 0, 0, 1)
_ZERO_POSITION: Position = (0.0, 0.0, 0.0)


# ---------------------------------------------------------------------------
# Shared FoR resolution
# ---------------------------------------------------------------------------


def _build_for_index(
    inner: _DbCompositeScene, timestamp: float
) -> tuple[dict[str, _FOREvent], dict[str, _FOREvent]]:
    """Resolve FoR events at *timestamp*.  Returns ``(by_channel_name, by_event_id)``."""
    by_name: dict[str, _FOREvent] = {}
    by_id: dict[str, _FOREvent] = {}
    for name, db_stream in inner.streams.items():
        if not isinstance(db_stream, _DbEventStream):
            continue
        if not isinstance(db_stream.stream, _FORStream):
            continue
        raw = _resolve_at(db_stream.stream.events, timestamp)
        if raw is not None:
            by_name[name] = raw
            by_id[raw.id] = raw
    return by_name, by_id


def _compose_for_chain(
    start_ref: str,
    for_by_name: dict[str, _FOREvent],
    for_by_id: dict[str, _FOREvent],
    timestamp: float,
) -> Transform:
    """Walk the FoR parent chain from *start_ref* to root, composing transforms."""
    event = for_by_name.get(start_ref) or for_by_id.get(start_ref)
    if event is None:
        raise KeyError(f"No resolved FoR event for {start_ref!r} at timestamp {timestamp}")

    chain: list[Transform] = []
    current: str | None = event.id
    visited: set[str] = set()

    while current is not None and current != _ROOT_FOR:
        if current in visited:
            raise ValueError(f"Circular FoR reference: {current}")
        visited.add(current)

        ev = for_by_name.get(current) or for_by_id.get(current)
        if ev is None:
            raise KeyError(f"No resolved FoR event for {current!r} at timestamp {timestamp}")

        chain.append(Transform(ev.rotation, ev.position))
        current = ev.parent_FOR

    result = Transform.identity()
    for t in reversed(chain):
        result = result.compose(t)
    return result


def _find_camera_for_ref(inner: _DbCompositeScene, camera_ref: str) -> str | None:
    """Find a camera stream's ``frame_of_reference_id`` by channel name or stream id."""
    for name, db_stream in inner.streams.items():
        if not isinstance(db_stream, _DbEventStream):
            continue
        if not isinstance(db_stream.stream, _CameraStream):
            continue
        if name == camera_ref or db_stream.id == camera_ref:
            return db_stream.stream.frame_of_reference_id
    return None


def _get_for_transform(
    inner: _DbCompositeScene, for_ref: str | None, timestamp: float
) -> Transform:
    """Compute composite world transform for a FoR reference.  Identity if *for_ref* is ``None``."""
    if for_ref is None:
        return Transform.identity()
    by_name, by_id = _build_for_index(inner, timestamp)
    return _compose_for_chain(for_ref, by_name, by_id, timestamp)


def _require_composite(scene: Scene) -> _DbCompositeScene:
    inner = scene._inner
    if not isinstance(inner, _DbCompositeScene):
        raise TypeError("Transforms are only available on composite scenes")
    return inner


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------


class Transform:
    """A 3-D rigid transform (rotation matrix + translation).

    The rotation is a column-major 9-tuple representing a 3x3 matrix
    (same layout as the builder's :class:`MatrixRotation`).
    """

    def __init__(self, rotation: RotationMatrix, position: Position) -> None:
        self._rotation = rotation
        self._position = position

    @property
    def rotation(self) -> RotationMatrix:
        return self._rotation

    @property
    def position(self) -> Position:
        return self._position

    def compose(self, child: Transform) -> Transform:
        """Compose ``self @ child``.

        If *self* maps frame A -> B and *child* maps B -> C, the result
        maps A -> C.  In concrete terms::

            R_out = R_self @ R_child
            t_out = R_self @ t_child + t_self
        """
        r = _mat_mul(self._rotation, child._rotation)
        rv = _mat_vec(self._rotation, child._position)
        p: Position = (
            rv[0] + self._position[0],
            rv[1] + self._position[1],
            rv[2] + self._position[2],
        )
        return Transform(r, p)

    @staticmethod
    def identity() -> Transform:
        return Transform(_IDENTITY_ROTATION, _ZERO_POSITION)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transform):
            return NotImplemented
        return self._rotation == other._rotation and self._position == other._position


# ---------------------------------------------------------------------------
# Event classes
# ---------------------------------------------------------------------------


class PCDEvent:
    """A single point-cloud frame."""

    def __init__(self, scene: Scene, inner: _DbURIEvent, channel: PCDChannel) -> None:
        self._scene = scene
        self._inner = inner
        self._channel = channel

    @property
    def uri(self) -> str:
        return self._inner.uri

    @property
    def timestamp(self) -> float | None:
        return self._inner.timestamp

    @property
    def frame_of_reference_id(self) -> str | None:
        return self._channel.frame_of_reference_id

    def get_transform(self) -> Transform:
        """Composite world transform for this event (via FoR chain from root)."""
        inner = _require_composite(self._scene)
        if self.timestamp is None:
            raise ValueError("Cannot compute transform: event has no timestamp")
        return _get_for_transform(inner, self.frame_of_reference_id, self.timestamp)


class ImageEvent:
    """A single image frame."""

    def __init__(self, scene: Scene, inner: _DbURIEvent, channel: ImageChannel) -> None:
        self._scene = scene
        self._inner = inner
        self._channel = channel

    @property
    def uri(self) -> str:
        return self._inner.uri

    @property
    def timestamp(self) -> float | None:
        return self._inner.timestamp

    @property
    def camera_id(self) -> str | None:
        return self._channel.camera_id

    def get_transform(self) -> Transform:
        """Composite world transform for this event (image -> camera -> FoR chain)."""
        inner = _require_composite(self._scene)
        if self.timestamp is None:
            raise ValueError("Cannot compute transform: event has no timestamp")
        camera_id = self.camera_id
        if camera_id is None:
            return Transform.identity()
        for_ref = _find_camera_for_ref(inner, camera_id)
        return _get_for_transform(inner, for_ref, self.timestamp)


class CameraEvent:
    """Camera parameters at a point in time."""

    def __init__(self, scene: Scene, inner: _CameraParamsEvent, channel: CameraChannel) -> None:
        self._scene = scene
        self._inner = inner
        self._channel = channel

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

    @property
    def frame_of_reference_id(self) -> str | None:
        return self._channel.frame_of_reference_id

    def get_transform(self) -> Transform:
        """Composite world transform for this event (via FoR chain from root)."""
        inner = _require_composite(self._scene)
        if self.timestamp is None:
            raise ValueError("Cannot compute transform: event has no timestamp")
        return _get_for_transform(inner, self.frame_of_reference_id, self.timestamp)


class FoREvent:
    """Frame-of-reference pose at a point in time."""

    def __init__(self, scene: Scene, inner: _FOREvent, channel: FoRChannel) -> None:
        self._scene = scene
        self._inner = inner
        self._channel = channel

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

    def get_transform(self) -> Transform:
        """Composite world transform for this FoR (walks parent chain to root)."""
        inner = _require_composite(self._scene)
        if self.timestamp is None:
            raise ValueError("Cannot compute transform: event has no timestamp")
        by_name, by_id = _build_for_index(inner, self.timestamp)
        return _compose_for_chain(self.id, by_name, by_id, self.timestamp)


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
        return [PCDEvent(self._scene, e, self) for e in self._inner.events]


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
        return [ImageEvent(self._scene, e, self) for e in self._inner.events]


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
        return [CameraEvent(self._scene, e, self) for e in self._inner.events]


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
        return [FoREvent(self._scene, e, self) for e in self._inner.events]


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

    # -- Snapshot ---------------------------------------------------------

    def snapshot(self, timestamp: float) -> SceneSnapshot:
        """Resolve this scene at the given timestamp.

        Returns a :class:`SceneSnapshot` containing the latest event
        at or before *timestamp* for every channel, plus methods to
        compute composite FoR transforms.
        """
        if not isinstance(self._inner, _DbCompositeScene):
            raise TypeError("Snapshots are only available on composite scenes")
        return SceneSnapshot(self, timestamp)

    # -- Factory ----------------------------------------------------------

    @staticmethod
    def from_dict(data: dict) -> Scene:
        """Parse a scene from a raw dictionary via the internal adapter."""
        parsed = _DbSceneAdapter.validate_python(data)
        return Scene(parsed)


# ---------------------------------------------------------------------------
# SceneSnapshot
# ---------------------------------------------------------------------------


class SceneSnapshot:
    """Resolved scene state at a specific timestamp.

    Created via :meth:`Scene.snapshot`.  Holds the latest event at or
    before the requested timestamp for every channel, and provides
    composite FoR transform calculation.
    """

    def __init__(self, scene: Scene, timestamp: float) -> None:
        self._scene = scene
        self._timestamp = timestamp

        self._pcd: dict[str, PCDEvent] = {}
        self._image: dict[str, ImageEvent] = {}
        self._camera: dict[str, CameraEvent] = {}
        self._for: dict[str, FoREvent] = {}

        # Raw FoR indices for shared chain resolution.
        self._for_by_name: dict[str, _FOREvent] = {}
        self._for_by_id: dict[str, _FOREvent] = {}

        self._resolve()

    def _resolve(self) -> None:
        inner = self._scene._inner
        if not isinstance(inner, _DbCompositeScene):
            return

        # Build raw FoR index via shared helper.
        self._for_by_name, self._for_by_id = _build_for_index(inner, self._timestamp)

        for name, db_stream in inner.streams.items():
            if not isinstance(db_stream, _DbEventStream):
                continue
            stream = db_stream.stream

            if isinstance(stream, _DbPCDStream):
                raw = _resolve_at(stream.events, self._timestamp)
                if raw is not None:
                    channel = PCDChannel(self._scene, name, stream)
                    self._pcd[name] = PCDEvent(self._scene, raw, channel)

            elif isinstance(stream, _DbImageStream):
                raw = _resolve_at(stream.events, self._timestamp)
                if raw is not None:
                    channel = ImageChannel(self._scene, name, stream)
                    self._image[name] = ImageEvent(self._scene, raw, channel)

            elif isinstance(stream, _CameraStream):
                raw = _resolve_at(stream.events, self._timestamp)
                if raw is not None:
                    channel = CameraChannel(self._scene, name, stream)
                    self._camera[name] = CameraEvent(self._scene, raw, channel)

            elif isinstance(stream, _FORStream):
                raw_ev = self._for_by_name.get(name)
                if raw_ev is not None:
                    channel = FoRChannel(self._scene, name, stream)
                    self._for[name] = FoREvent(self._scene, raw_ev, channel)

    # -- Accessors --------------------------------------------------------

    @property
    def timestamp(self) -> float:
        return self._timestamp

    @property
    def pcd_events(self) -> dict[str, PCDEvent]:
        return dict(self._pcd)

    @property
    def image_events(self) -> dict[str, ImageEvent]:
        return dict(self._image)

    @property
    def camera_events(self) -> dict[str, CameraEvent]:
        return dict(self._camera)

    @property
    def for_events(self) -> dict[str, FoREvent]:
        return dict(self._for)

    # -- Named channel transforms -----------------------------------------

    def get_for_transform(self, for_channel_name: str) -> Transform:
        """Composite world transform for a FoR channel."""
        event = self._for.get(for_channel_name)
        if event is None:
            raise KeyError(f"No resolved FoR event for channel {for_channel_name!r}")
        return _compose_for_chain(event.id, self._for_by_name, self._for_by_id, self._timestamp)

    def get_pcd_transform(self, pcd_channel_name: str) -> Transform:
        """World transform for a PCD channel (via its FoR reference)."""
        event = self._pcd.get(pcd_channel_name)
        if event is None:
            raise KeyError(f"No resolved PCD event for channel {pcd_channel_name!r}")
        for_id = event.frame_of_reference_id
        if for_id is None:
            return Transform.identity()
        return _compose_for_chain(for_id, self._for_by_name, self._for_by_id, self._timestamp)

    def get_camera_transform(self, camera_channel_name: str) -> Transform:
        """World transform for a camera channel (via its FoR reference)."""
        event = self._camera.get(camera_channel_name)
        if event is None:
            raise KeyError(f"No resolved camera event for channel {camera_channel_name!r}")
        for_id = event.frame_of_reference_id
        if for_id is None:
            return Transform.identity()
        return _compose_for_chain(for_id, self._for_by_name, self._for_by_id, self._timestamp)

    def get_image_transform(self, image_channel_name: str) -> Transform:
        """World transform for an image channel (image -> camera -> FoR)."""
        event = self._image.get(image_channel_name)
        if event is None:
            raise KeyError(f"No resolved image event for channel {image_channel_name!r}")
        camera_id = event.camera_id
        if camera_id is None:
            return Transform.identity()
        inner = self._scene._inner
        assert isinstance(inner, _DbCompositeScene)
        for_ref = _find_camera_for_ref(inner, camera_id)
        if for_ref is None:
            return Transform.identity()
        return _compose_for_chain(for_ref, self._for_by_name, self._for_by_id, self._timestamp)

    # -- Event-based transforms -------------------------------------------

    def get_transform(self, event: Union[PCDEvent, CameraEvent, FoREvent, ImageEvent]) -> Transform:
        """Composite world transform for the given event.

        * :class:`FoREvent` -- walks the parent chain from this event.
        * :class:`PCDEvent` / :class:`CameraEvent` -- resolves via the
          channel's ``frame_of_reference_id``.
        * :class:`ImageEvent` -- resolves via camera -> FoR chain.
        """
        if isinstance(event, FoREvent):
            return _compose_for_chain(event.id, self._for_by_name, self._for_by_id, self._timestamp)

        if isinstance(event, (PCDEvent, CameraEvent)):
            for_id = event.frame_of_reference_id
            if for_id is None:
                return Transform.identity()
            return _compose_for_chain(for_id, self._for_by_name, self._for_by_id, self._timestamp)

        if isinstance(event, ImageEvent):
            camera_id = event.camera_id
            if camera_id is None:
                return Transform.identity()
            inner = self._scene._inner
            assert isinstance(inner, _DbCompositeScene)
            for_ref = _find_camera_for_ref(inner, camera_id)
            if for_ref is None:
                return Transform.identity()
            return _compose_for_chain(for_ref, self._for_by_name, self._for_by_id, self._timestamp)

        raise TypeError(f"Unsupported event type: {type(event)}")
