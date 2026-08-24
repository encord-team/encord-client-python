"""Builder API for constructing Encord scene payloads.

Provides a multi-stage builder pattern for assembling scene data. Each stream
type has its own nested builder, and event timestamps are assigned sequentially.

**Stages:**

1. Create a :class:`SceneBuilder` and (optionally) configure global settings.
2. Add one or more streams -- each ``add_*_stream`` call returns a nested
   stream builder.
3. Populate event streams via the stream-specific method
   (``add_pcd``, ``add_image``, ``add_camera_params``, ``add_pose``), or
   provide the CSV URI when creating a time-series stream.
4. Pass the builder to SDK upload/create methods, which validates and
   serializes internally.

Every mutator returns ``self``, so stream-local calls can be chained fluently::

    scene = SceneBuilder()
    scene.add_pcd_stream("lidar").add_pcd(uri="s3://bucket/frame0.pcd")
"""

from __future__ import annotations

from typing import Any, overload

from encord.beta.scene.internal.upload import (
    Convention as _Convention,
)
from encord.beta.scene.internal.upload import (
    Direction,  # public enum, re-exported
)
from encord.beta.scene.internal.upload import (
    SceneContent as _SceneContent,
)
from encord.beta.scene.internal.upload import (
    SceneWithConfig as _SceneWithConfig,
)
from encord.beta.scene.internal.upload import (
    Streams as _Streams,
)
from encord.beta.scene.intrinsics import AdvancedIntrinsics, Intrinsics
from encord.beta.scene.layout import SceneImageTile, SceneLayout, SceneTimeSeriesTile
from encord.beta.scene.pose import Pose
from encord.beta.scene.settings import SceneViewSettings
from encord.beta.scene.stream import (
    CameraStreamBuilder,
    FoRStreamBuilder,
    ImageStreamBuilder,
    PCDStreamBuilder,
    TimeSeriesStreamBuilder,
    _StreamBuilderBase,
)
from encord.exceptions import EncordException

ROOT_FOR: str = "root"


class SceneBuilder:
    """Top-level builder for constructing an Encord scene payload.

    Supported stream types:
        * **Point cloud** -- :meth:`add_pcd_stream`
        * **Camera parameters** -- :meth:`add_camera_stream`
        * **Frame of reference** -- :meth:`add_for_stream`
        * **Image** -- :meth:`add_image_stream`
        * **Time series** -- :meth:`add_time_series_stream`

    Stream names must be unique.  Re-using a name raises an error.

    The scene must contain at least one point-cloud or image stream, and every
    event stream must have at least one event. ``_build`` validates and
    serializes builders internally for SDK upload/create methods.
    """

    def __init__(self) -> None:
        self._streams: dict[str, _StreamBuilderBase] = {}
        self._world_convention: _Convention | None = None
        self._camera_convention: _Convention | None = None
        self.settings: SceneViewSettings | None = None
        self.layout: SceneLayout | None = None

    # -- global configuration ---------------------------------------------

    def set_world_convention(self, *, x: Direction, y: Direction, z: Direction) -> SceneBuilder:
        """Set the world coordinate-system convention.

        The three directions must map to three distinct spatial axes,
        forming a valid orthogonal coordinate system.  The convention's
        handedness (right-handed when ``cross(x, y) == z``) **must match**
        the camera convention.

        Available directions: ``Direction.UP``, ``Direction.DOWN``,
        ``Direction.LEFT``, ``Direction.RIGHT``, ``Direction.FORWARD``,
        ``Direction.BACKWARD``.
        """
        self._world_convention = _Convention(x=x, y=y, z=z)
        return self

    def set_camera_convention(self, *, x: Direction, y: Direction, z: Direction) -> SceneBuilder:
        """Set the camera coordinate-system convention.

        The three directions must map to three distinct spatial axes,
        forming a valid orthogonal coordinate system.  The convention's
        handedness **must match** the world convention.

        Available directions: ``Direction.UP``, ``Direction.DOWN``,
        ``Direction.LEFT``, ``Direction.RIGHT``, ``Direction.FORWARD``,
        ``Direction.BACKWARD``.
        """
        self._camera_convention = _Convention(x=x, y=y, z=z)
        return self

    # -- stream factories -------------------------------------------------

    def add_time_series_stream(self, name: str, *, uri: str) -> TimeSeriesStreamBuilder:
        """Add a self-contained CSV time-series stream.

        Args:
            name: Unique stream name.
            uri: Non-empty URI pointing to the CSV file.
        """
        sb = TimeSeriesStreamBuilder(name, self, uri=uri)
        if name in self._streams:
            raise RuntimeError(f"stream {name} is already defined")
        self._streams[name] = sb
        return sb

    def add_pcd_stream(
        self,
        name: str,
        *,
        frame_of_reference: str | FoRStreamBuilder | None = None,
        pose: Pose | None = None,
    ) -> PCDStreamBuilder:
        """Add a point-cloud stream.

        Args:
            name: Unique stream name.
            frame_of_reference: Optional FoR stream to link to.
            pose: Optional static pose for the sensor mount.
        """
        sb = PCDStreamBuilder(name, self, frame_of_reference=frame_of_reference, pose=pose)
        if name in self._streams:
            raise RuntimeError(f"stream {name} is already defined")
        self._streams[name] = sb
        return sb

    def add_camera_stream(
        self,
        name: str,
        *,
        frame_of_reference: str | FoRStreamBuilder | None = None,
        pose: Pose | None = None,
    ) -> CameraStreamBuilder:
        """Add a camera-parameters stream.

        Args:
            name: Unique stream name.
            frame_of_reference: Optional FoR stream to link to.
            pose: Optional static pose for the sensor mount.
        """
        sb = CameraStreamBuilder(name, self, frame_of_reference=frame_of_reference, pose=pose)
        if name in self._streams:
            raise RuntimeError(f"stream {name} is already defined")
        self._streams[name] = sb
        return sb

    def add_for_stream(
        self,
        name: str,
        *,
        parent_for_id: str | FoRStreamBuilder | None = None,
    ) -> FoRStreamBuilder:
        """Add a frame-of-reference stream.

        Args:
            name: Unique stream name.  Other streams reference this
                stream via this name.
            parent_for_id: Optional parent FoR -- either the **stream name**
                or a :class:`FoRStreamBuilder`. If omitted, the stream is
                attached to the scene root.
        """
        if name == ROOT_FOR:
            raise EncordException(f"'{ROOT_FOR}' is reserved and cannot be used as a for_id")
        sb = FoRStreamBuilder(name, self, parent_for_id=parent_for_id or ROOT_FOR)
        if name in self._streams:
            raise RuntimeError(f"stream {name} is already defined")
        self._streams[name] = sb
        return sb

    @overload
    def add_image_stream(
        self,
        name: str,
        *,
        camera: str,
    ) -> ImageStreamBuilder: ...

    @overload
    def add_image_stream(
        self,
        name: str,
        *,
        width: int,
        height: int,
        intrinsics: Intrinsics,
        timestamp: float,
        frame_of_reference: str | FoRStreamBuilder | None = ...,
        pose: Pose | None = ...,
    ) -> ImageStreamBuilder: ...

    def add_image_stream(
        self,
        name: str,
        *,
        camera: str | None = None,
        width: int | None = None,
        height: int | None = None,
        intrinsics: Intrinsics | None = None,
        timestamp: float | None = None,
        frame_of_reference: str | FoRStreamBuilder | None = None,
        pose: Pose | None = None,
    ) -> ImageStreamBuilder:
        """Add an image stream.

        There are two modes:

        1. **Existing camera**: pass ``camera="cam_stream_name"`` to link
           to an already-registered camera stream.
        2. **Inline camera**: pass ``width``, ``height``, and ``intrinsics``
           to auto-create a camera stream named ``{name}/camera``.

        Args:
            name: Unique stream name.
            camera: The **stream name** of a camera-parameters stream.
                Mutually exclusive with ``width``/``height``/``intrinsics``.
            width: Image width in pixels (inline camera mode).
            height: Image height in pixels (inline camera mode).
            intrinsics: Camera intrinsics (inline camera mode).
            timestamp: Camera-parameters event timestamp (inline camera mode).
            frame_of_reference: Optional FoR linkage for the auto-created
                camera stream (only used in inline camera mode).
            pose: Optional static pose for the auto-created camera stream
                (only used in inline camera mode).
        """
        has_inline = width is not None or height is not None or intrinsics is not None
        has_camera = camera is not None

        if has_camera and has_inline:
            raise EncordException(
                "Cannot specify both 'camera' and inline camera parameters "
                "(width/height/intrinsics) for add_image_stream"
            )
        if not has_camera and not has_inline:
            raise EncordException(
                "Must specify either 'camera' or inline camera parameters "
                "(width/height/intrinsics) for add_image_stream"
            )

        if has_camera:
            if frame_of_reference is not None or pose is not None:
                raise EncordException(
                    "Cannot specify 'frame_of_reference' or 'pose' when using "
                    "an existing camera stream. Set these on the camera stream directly."
                )

        if has_inline:
            if width is None or height is None or intrinsics is None or timestamp is None:
                raise EncordException(
                    "All of width, height, intrinsics, and timestamp must be provided when using inline camera parameters"
                )
            camera_name = f"{name}/camera"
            self.add_camera_stream(
                camera_name,
                frame_of_reference=frame_of_reference,
                pose=pose,
            ).add_camera_params(width, height, intrinsics, timestamp=timestamp)
            camera = camera_name

        assert camera is not None
        sb = ImageStreamBuilder(name, self, camera=camera)
        if name in self._streams:
            raise RuntimeError(f"stream {name} is already defined")
        self._streams[name] = sb
        return sb

    # -- build & validate -------------------------------------------------

    def _build(self) -> dict[str, Any]:
        """Validate and serialize the scene for SDK internals.

        **Client-side validation** (checked here):

        1. At least one point-cloud or image stream is present.
        2. Every event stream has at least one event.
        3. PCD / image event URIs are non-empty.
        4. Advanced intrinsics matrix sizes (``k``: 9, ``r``: 9,
           ``p``: 12).
        5. Image stream -> camera stream reference exists.
        6. PCD / camera ``frame_of_reference`` references an existing
           FoR stream name.
        7. FoR ``parent_for_id`` references an existing FoR stream name or the
           implicit scene root.
        8. FoR parent chain is acyclic (no circular references).
        9. Radius indicators reference an existing FoR stream or the implicit
           scene root.

        Raises:
            EncordException: When validation fails.
        """
        if not any(isinstance(sb, (PCDStreamBuilder, ImageStreamBuilder)) for sb in self._streams.values()):
            raise EncordException("Scene must contain at least one point cloud or image stream")

        errors: list[str] = []

        # Collect cross-reference sets.
        camera_names: set[str] = set()
        for_stream_names: set[str] = set()
        for name, sb in self._streams.items():
            if isinstance(sb, CameraStreamBuilder):
                camera_names.add(name)
            if isinstance(sb, FoRStreamBuilder):
                for_stream_names.add(name)

        # Per-stream validation.
        stream_models: dict[str, Any] = {}
        for name, sb in self._streams.items():
            # 1. Must have events.
            if sb._event_count == 0:
                errors.append(f"Stream '{name}' has no events")

            # 2. URI must not be empty.
            if isinstance(sb, (PCDStreamBuilder, ImageStreamBuilder)):
                for idx, event in enumerate(sb._events):
                    if not event.uri:
                        errors.append(f"Stream '{name}' event {idx} has an empty URI")

            # 3. Advanced intrinsics matrix-length checks.
            if isinstance(sb, CameraStreamBuilder):
                for idx, cam_event in enumerate(sb._events):
                    intr = cam_event.intrinsics
                    if isinstance(intr, AdvancedIntrinsics):
                        if intr.k is not None and len(intr.k) != 9:
                            errors.append(f"Camera '{name}' event {idx}: 'k' must have 9 elements, got {len(intr.k)}")
                        if intr.r is not None and len(intr.r) != 9:
                            errors.append(f"Camera '{name}' event {idx}: 'r' must have 9 elements, got {len(intr.r)}")
                        if intr.p is not None and len(intr.p) != 12:
                            errors.append(f"Camera '{name}' event {idx}: 'p' must have 12 elements, got {len(intr.p)}")

            # 4. Image -> camera reference.
            if isinstance(sb, ImageStreamBuilder):
                if sb._camera not in camera_names:
                    errors.append(
                        f"Image stream '{name}' references camera "
                        f"'{sb._camera}' which does not exist. "
                        f"Available cameras: {camera_names or '{}'}"
                    )

            # 5. Frame-of-reference linkage.
            if isinstance(sb, (PCDStreamBuilder, CameraStreamBuilder)):
                ref = sb._frame_of_reference
                if ref is not None and ref not in for_stream_names:
                    errors.append(
                        f"Stream '{name}' references frame of reference "
                        f"'{ref}' which does not exist. "
                        f"Available FoR streams: {for_stream_names or '{}'}"
                    )

            # 6. FoR parent reference.
            if isinstance(sb, FoRStreamBuilder) and sb._parent_for_id is not None:
                if sb._parent_for_id != ROOT_FOR and sb._parent_for_id not in for_stream_names:
                    errors.append(
                        f"FoR stream '{name}' references parent "
                        f"'{sb._parent_for_id}' which does not exist. "
                        f"Available FoR streams: {for_stream_names or '{}'}"
                    )

            stream_models[name] = sb._to_internal()

        # 7. FoR parent chain must be acyclic.
        parent_of: dict[str, str | None] = {}
        for fname in for_stream_names:
            fsb = self._streams[fname]
            assert isinstance(fsb, FoRStreamBuilder)
            pid = fsb._parent_for_id
            parent_of[fname] = pid if pid != ROOT_FOR else None

        for start in parent_of:
            visited: set[str] = set()
            cur: str | None = start
            while cur is not None and cur in parent_of:
                if cur in visited:
                    errors.append(f"FoR parent chain contains a cycle: {' -> '.join([*visited, cur])}")
                    break
                visited.add(cur)
                cur = parent_of[cur]

        if self.settings is not None and self.settings.radius_indicators is not None:
            for indicator in self.settings.radius_indicators:
                if (
                    indicator.frame_of_reference_id != ROOT_FOR
                    and indicator.frame_of_reference_id not in for_stream_names
                ):
                    errors.append(
                        f"Radius indicator references frame of reference '{indicator.frame_of_reference_id}' "
                        "which does not exist. "
                        f"Available FoR streams: {for_stream_names or '{}'}"
                    )

        if self.layout is not None:
            for tile_id, tile in self.layout.tiles.items():
                expected_stream_type: type[ImageStreamBuilder] | type[TimeSeriesStreamBuilder]
                if isinstance(tile, SceneImageTile):
                    expected_stream_type = ImageStreamBuilder
                    expected_type_name = "image"
                elif isinstance(tile, SceneTimeSeriesTile):
                    expected_stream_type = TimeSeriesStreamBuilder
                    expected_type_name = "time_series"
                else:
                    continue

                if not isinstance(self._streams.get(tile.stream_name), expected_stream_type):
                    available_streams = sorted(
                        stream_name
                        for stream_name, stream in self._streams.items()
                        if isinstance(stream, expected_stream_type)
                    )
                    errors.append(
                        f"Scene {tile.type} tile '{tile_id}' references non-existent {expected_type_name} "
                        f"stream '{tile.stream_name}'. Available streams: {available_streams}"
                    )

        if errors:
            raise EncordException("Scene validation failed:\n- " + "\n- ".join(errors))

        # Serialize via Pydantic models from internal.py.
        streams = _Streams.model_construct(root=stream_models)

        has_settings = self.settings is not None
        has_layout = self.layout is not None
        has_config = (
            self._world_convention is not None or self._camera_convention is not None or has_settings or has_layout
        )
        if has_config:
            scene_content = _SceneContent.model_construct(root=streams)
            config = _SceneWithConfig.model_construct(
                content=scene_content,
                world_convention=self._world_convention,
                camera_convention=self._camera_convention,
            )
            result = config.model_dump()
            if self.settings is not None:
                result["view_settings"] = self.settings.to_dict(by_alias=False)
            if self.layout is not None:
                result["layout"] = self.layout.to_dict(by_alias=False)
            return result

        return streams.model_dump()
