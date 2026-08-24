"""Public SDK scene read types.

These are stable SDK types that insulate users from the internal wire format.
They are constructed from the internal types in ``beta/scene/internal/scene.py``.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, is_dataclass
from typing import Any, cast

from encord.beta.scene.internal.scene import (
    CameraStream as _CameraStream,
)
from encord.beta.scene.internal.scene import (
    CompositeScene as _CompositeScene,
)
from encord.beta.scene.internal.scene import (
    EventStream as _EventStream,
)
from encord.beta.scene.internal.scene import (
    FOREvent as _FOREvent,
)
from encord.beta.scene.internal.scene import (
    FORStream as _FORStream,
)
from encord.beta.scene.internal.scene import (
    ImageStream as _ImageStream,
)
from encord.beta.scene.internal.scene import (
    ModelStream as _ModelStream,
)
from encord.beta.scene.internal.scene import (
    PCDStream as _PCDStream,
)
from encord.beta.scene.internal.scene import (
    Scene as _Scene,
)
from encord.beta.scene.internal.scene import (
    SelfContainedScene as _SelfContainedScene,
)
from encord.beta.scene.internal.scene import (
    SelfContainedStream as _SelfContainedStream,
)


def scene_to_upload_payload(
    internal: _Scene,
    *,
    uri_mapper: Callable[[str], str] | Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Convert an internal signed scene response into scene upload JSON."""
    if isinstance(internal, _SelfContainedScene):
        return _scene_with_config(
            internal,
            {
                "url": _map_uri(internal.url, uri_mapper),
                "format": _enum_value(internal.format),
            },
        )

    return _scene_with_config(
        internal,
        {stream_id: _stream_to_upload(stream_id, stream, uri_mapper) for stream_id, stream in internal.streams.items()},
    )


def _scene_with_config(internal: _SelfContainedScene | _CompositeScene, content: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": content,
        "default_ground_height": internal.default_ground_height,
        "world_convention": _dump_model(internal.world_convention),
        "camera_convention": _dump_model(internal.camera_convention),
    }


def _stream_to_upload(
    stream_id: str,
    stream: _EventStream | _SelfContainedStream,
    uri_mapper: Callable[[str], str] | Mapping[str, str] | None,
) -> dict[str, Any]:
    if isinstance(stream, _SelfContainedStream):
        return {
            "type": "time_series",
            "uri": _map_uri(stream.url, uri_mapper),
        }

    inner = stream.stream
    if isinstance(inner, _PCDStream):
        return {
            "type": "point_cloud",
            "events": [_uri_event_to_upload(event, uri_mapper) for event in inner.events],
            "frame_of_reference": inner.frame_of_reference_id,
            "pose": None,
        }
    if isinstance(inner, _ImageStream):
        if inner.camera_id is None:
            raise ValueError(f"Image stream '{stream_id}' cannot be re-uploaded because it has no camera_id")
        return {
            "type": "image",
            "camera": inner.camera_id,
            "events": [_uri_event_to_upload(event, uri_mapper) for event in inner.events],
        }
    if isinstance(inner, _CameraStream):
        return {
            "type": "camera_parameters",
            "events": [_camera_event_to_upload(event) for event in inner.events],
            "frame_of_reference": inner.frame_of_reference_id,
            "pose": None,
        }
    if isinstance(inner, _FORStream):
        return {
            "type": "frame_of_reference",
            "id": inner.events[0].id if inner.events else stream_id,
            "parent_FoR_id": inner.events[0].parent_for if inner.events else None,
            "events": [_for_event_to_upload(event) for event in inner.events],
        }
    if isinstance(inner, _ModelStream):
        return {
            "type": "model",
            "events": [_model_event_to_upload(event, uri_mapper) for event in inner.events],
            "frame_of_reference": None,
            "pose": None,
        }
    raise ValueError(f"Unsupported scene stream type for stream '{stream_id}': {type(inner).__name__}")


def _uri_event_to_upload(event: Any, uri_mapper: Callable[[str], str] | Mapping[str, str] | None) -> dict[str, Any]:
    return {
        "timestamp": event.timestamp,
        "uri": _map_uri(event.url, uri_mapper),
    }


def _camera_event_to_upload(event: Any) -> dict[str, Any]:
    payload = {
        "timestamp": event.timestamp,
        "width_px": event.width_px,
        "height_px": event.height_px,
        "intrinsics": _dump_model(event.intrinsics),
    }
    if getattr(event, "extrinsics", None) is not None:
        payload["extrinsics"] = _extrinsics_to_pose(event.extrinsics)
    return payload


def _for_event_to_upload(event: _FOREvent) -> dict[str, Any]:
    return {
        "timestamp": event.timestamp,
        "pose": _rotation_position_to_pose(event.rotation, event.position),
    }


def _model_event_to_upload(event: Any, uri_mapper: Callable[[str], str] | Mapping[str, str] | None) -> dict[str, Any]:
    if hasattr(event, "url"):
        return _uri_event_to_upload(event, uri_mapper)

    payload = _dump_model(event)
    for geometry in payload.get("geometries") or []:
        if "url" in geometry:
            geometry["url"] = _map_uri(geometry["url"], uri_mapper)
    return payload


def _extrinsics_to_pose(extrinsics: Any) -> dict[str, Any]:
    if hasattr(extrinsics, "rotation") and hasattr(extrinsics, "position"):
        return _rotation_position_to_pose(extrinsics.rotation, extrinsics.position)
    return _dump_model(extrinsics)


def _rotation_position_to_pose(rotation: Any, position: Any) -> dict[str, Any]:
    return {
        "rotation": tuple(rotation),
        "position": {
            "x": position[0],
            "y": position[1],
            "z": position[2],
        },
    }


def _map_uri(uri: str, uri_mapper: Callable[[str], str] | Mapping[str, str] | None) -> str:
    if uri_mapper is None:
        return uri
    if callable(uri_mapper):
        return uri_mapper(uri)
    return uri_mapper.get(uri, uri)


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _dump_model(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(cast(Any, value))
    return value
