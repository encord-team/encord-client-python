"""Stream builder classes for constructing scene streams.

Each stream type has a dedicated builder returned by the corresponding
``add_*_stream`` method on :class:`~encord.beta.scene.builder.SceneBuilder`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from encord.beta.scene.builder import SceneBuilder

from encord.beta.scene.internal.upload import (
    InputCameraParamsEvent as _InputCameraParamsEvent,
)
from encord.beta.scene.internal.upload import (
    InputCameraStream as _InputCameraStream,
)
from encord.beta.scene.internal.upload import (
    InputEntityType as _InputEntityType,
)
from encord.beta.scene.internal.upload import (
    InputFoREvent as _InputFoREvent,
)
from encord.beta.scene.internal.upload import (
    InputFoRStream as _InputFoRStream,
)
from encord.beta.scene.internal.upload import (
    InputImageStream as _InputImageStream,
)
from encord.beta.scene.internal.upload import (
    InputPCDStream as _InputPCDStream,
)
from encord.beta.scene.internal.upload import (
    InputPose as _InputPose,
)
from encord.beta.scene.internal.upload import (
    InputTimeSeriesStream as _InputTimeSeriesStream,
)
from encord.beta.scene.internal.upload import (
    InputURIEvent as _InputURIEvent,
)
from encord.beta.scene.intrinsics import (
    AdvancedIntrinsics,
    Intrinsics,
)
from encord.beta.scene.pose import (
    Pose,
)
from encord.exceptions import EncordException

# ===================================================================
# Internal event types
# ===================================================================


@dataclass
class _URIEvent:
    uri: str
    timestamp: float


@dataclass
class _CameraEvent:
    width_px: int
    height_px: int
    intrinsics: Intrinsics
    timestamp: float


@dataclass
class _FoREvent:
    pose: Pose
    timestamp: float


# ===================================================================
# Helpers
# ===================================================================


def _resolve_for_ref(ref: str | FoRStreamBuilder | None) -> str | None:
    """Extract the stream name from a FoR reference (string or builder)."""
    if ref is None or isinstance(ref, str):
        return ref
    return ref._name


def _pose_to_internal(pose: Pose) -> _InputPose:
    return _InputPose.model_construct(root=pose._to_internal())


# ===================================================================
# Stream builders
# ===================================================================


class _StreamBuilderBase:
    """Internal base -- not part of the public API."""

    def __init__(self, name: str, scene: SceneBuilder) -> None:
        self._name = name
        self._scene = scene

    @property
    def _event_count(self) -> int:
        raise NotImplementedError

    def _to_internal(self) -> Any:
        raise NotImplementedError

    @property
    def name(self) -> str:
        """The stream name used to register this stream in the :class:`SceneBuilder`."""
        return self._name


# -------------------------------------------------------------------
# Time-series stream
# -------------------------------------------------------------------


class TimeSeriesStreamBuilder(_StreamBuilderBase):
    """Builder for a self-contained CSV time-series stream.

    Returned by :meth:`SceneBuilder.add_time_series_stream`.
    """

    def __init__(self, name: str, scene: SceneBuilder, *, uri: str) -> None:
        super().__init__(name, scene)
        if not uri:
            raise EncordException(f"Time-series stream '{name}' has an empty URI")
        self._uri = uri

    @property
    def _event_count(self) -> int:
        return 1

    def _to_internal(self) -> _InputTimeSeriesStream:
        return _InputTimeSeriesStream.model_construct(uri=self._uri)


# -------------------------------------------------------------------
# Point-cloud stream
# -------------------------------------------------------------------


class PCDStreamBuilder(_StreamBuilderBase):
    """Builder for a point-cloud stream.

    Returned by :meth:`SceneBuilder.add_pcd_stream`.
    """

    def __init__(
        self,
        name: str,
        scene: SceneBuilder,
        *,
        frame_of_reference: str | FoRStreamBuilder | None = None,
        pose: Pose | None = None,
    ) -> None:
        super().__init__(name, scene)
        self._events: list[_URIEvent] = []
        self._frame_of_reference = _resolve_for_ref(frame_of_reference)
        self._pose = pose

    @property
    def _event_count(self) -> int:
        return len(self._events)

    def add_pcd(self, *, uri: str, timestamp: float) -> PCDStreamBuilder:
        """Append a single point-cloud event.

        Args:
            uri: Non-empty URI pointing to the point-cloud file.
            timestamp: Scene timestamp for this event.
        """
        if not uri:
            raise EncordException(f"PCD stream '{self._name}' event has an empty URI")
        self._events.append(_URIEvent(uri=uri, timestamp=timestamp))
        return self

    def set_frame_of_reference(self, for_id: str | FoRStreamBuilder) -> PCDStreamBuilder:
        """Link this stream to a frame-of-reference stream.

        Args:
            for_id: The **stream name** of a FoR stream, or a
                :class:`FoRStreamBuilder` instance.
        """
        self._frame_of_reference = _resolve_for_ref(for_id)
        return self

    def set_pose(self, pose: Pose) -> PCDStreamBuilder:
        """Set a static pose for this stream."""
        self._pose = pose
        return self

    def _to_internal(self) -> _InputPCDStream:
        return _InputPCDStream.model_construct(
            type=_InputEntityType.POINT_CLOUD,
            events=[_InputURIEvent.model_construct(uri=e.uri, timestamp=e.timestamp) for e in self._events],
            frame_of_reference=self._frame_of_reference,
            pose=_pose_to_internal(self._pose) if self._pose is not None else None,
        )


# -------------------------------------------------------------------
# Camera-parameters stream
# -------------------------------------------------------------------


class CameraStreamBuilder(_StreamBuilderBase):
    """Builder for a camera-parameters stream.

    Returned by :meth:`SceneBuilder.add_camera_stream`.
    """

    def __init__(
        self,
        name: str,
        scene: SceneBuilder,
        *,
        frame_of_reference: str | FoRStreamBuilder | None = None,
        pose: Pose | None = None,
    ) -> None:
        super().__init__(name, scene)
        self._events: list[_CameraEvent] = []
        self._frame_of_reference = _resolve_for_ref(frame_of_reference)
        self._pose = pose

    @property
    def _event_count(self) -> int:
        return len(self._events)

    def add_camera_params(
        self,
        width: int,
        height: int,
        intrinsics: Intrinsics,
        *,
        timestamp: float,
    ) -> CameraStreamBuilder:
        """Append a camera-parameters event.

        Args:
            width: Image width in pixels (must be >= 0).
            height: Image height in pixels (must be >= 0).
            intrinsics: Camera intrinsics (:class:`SimpleIntrinsics` or
                :class:`AdvancedIntrinsics`).
            timestamp: Scene timestamp for this event.
        """
        if isinstance(intrinsics, AdvancedIntrinsics):
            errors: list[str] = []
            if intrinsics.k is not None and len(intrinsics.k) != 9:
                errors.append(f"'k' must have 9 elements, got {len(intrinsics.k)}")
            if intrinsics.r is not None and len(intrinsics.r) != 9:
                errors.append(f"'r' must have 9 elements, got {len(intrinsics.r)}")
            if intrinsics.p is not None and len(intrinsics.p) != 12:
                errors.append(f"'p' must have 12 elements, got {len(intrinsics.p)}")
            if errors:
                raise EncordException(f"Camera stream '{self._name}' has invalid intrinsics: " + "; ".join(errors))
        self._events.append(
            _CameraEvent(
                width_px=width,
                height_px=height,
                intrinsics=intrinsics,
                timestamp=timestamp,
            )
        )
        return self

    def set_frame_of_reference(self, for_id: str | FoRStreamBuilder) -> CameraStreamBuilder:
        """Link this stream to a frame-of-reference stream.

        Args:
            for_id: The **stream name** of a FoR stream, or a
                :class:`FoRStreamBuilder` instance.
        """
        self._frame_of_reference = _resolve_for_ref(for_id)
        return self

    def set_pose(self, pose: Pose) -> CameraStreamBuilder:
        """Set a static pose for this stream."""
        self._pose = pose
        return self

    def _to_internal(self) -> _InputCameraStream:
        return _InputCameraStream.model_construct(
            type=_InputEntityType.CAMERA_PARAMETERS,
            events=[
                _InputCameraParamsEvent.model_construct(
                    width_px=e.width_px,
                    height_px=e.height_px,
                    intrinsics=e.intrinsics._to_internal(),
                    timestamp=e.timestamp,
                )
                for e in self._events
            ],
            frame_of_reference=self._frame_of_reference,
            pose=_pose_to_internal(self._pose) if self._pose is not None else None,
        )


# -------------------------------------------------------------------
# Frame-of-reference stream
# -------------------------------------------------------------------


class FoRStreamBuilder(_StreamBuilderBase):
    """Builder for a frame-of-reference (FoR) stream.

    Returned by :meth:`SceneBuilder.add_for_stream`.
    """

    def __init__(
        self,
        name: str,
        scene: SceneBuilder,
        *,
        parent_for_id: str | FoRStreamBuilder | None = None,
    ) -> None:
        super().__init__(name, scene)
        self._events: list[_FoREvent] = []
        self._parent_for_id = _resolve_for_ref(parent_for_id)

    @property
    def _event_count(self) -> int:
        return len(self._events)

    def add_pose(self, pose: Pose, *, timestamp: float) -> FoRStreamBuilder:
        """Append a frame-of-reference event.

        Args:
            pose: The pose for this event (any supported rotation
                encoding).
            timestamp: Scene timestamp for this event.
        """
        self._events.append(_FoREvent(pose=pose, timestamp=timestamp))
        return self

    def _to_internal(self) -> _InputFoRStream:
        return _InputFoRStream.model_construct(
            type=_InputEntityType.FRAME_OF_REFERENCE,
            id=self._name,
            parent_FoR_id=self._parent_for_id,
            events=[
                _InputFoREvent.model_construct(
                    timestamp=e.timestamp,
                    pose=_pose_to_internal(e.pose),
                )
                for e in self._events
            ],
        )


# -------------------------------------------------------------------
# Image stream
# -------------------------------------------------------------------


class ImageStreamBuilder(_StreamBuilderBase):
    """Builder for an image stream linked to a camera.

    Returned by :meth:`SceneBuilder.add_image_stream`.
    """

    def __init__(
        self,
        name: str,
        scene: SceneBuilder,
        *,
        camera: str,
    ) -> None:
        super().__init__(name, scene)
        self._events: list[_URIEvent] = []
        self._camera = camera

    @property
    def _event_count(self) -> int:
        return len(self._events)

    def add_image(self, *, uri: str, timestamp: float) -> ImageStreamBuilder:
        """Append an image event.

        Args:
            uri: Non-empty URI pointing to the image file.
            timestamp: Scene timestamp for this event.
        """
        if not uri:
            raise EncordException(f"Image stream '{self._name}' event has an empty URI")
        self._events.append(_URIEvent(uri=uri, timestamp=timestamp))
        return self

    def _to_internal(self) -> _InputImageStream:
        return _InputImageStream.model_construct(
            type=_InputEntityType.IMAGE,
            camera=self._camera,
            events=[_InputURIEvent.model_construct(uri=e.uri, timestamp=e.timestamp) for e in self._events],
        )
