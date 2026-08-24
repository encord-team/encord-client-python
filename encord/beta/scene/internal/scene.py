"""Read-side composite scene models returned by GET /v2/public/scene/{scene_uuid}.

These mirror the backend's external API models from ml-utils and are used to
deserialize the response for :class:`encord.beta.scene.SceneReader`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, List, Literal, Optional, Tuple, Union

from pydantic import Field, field_validator

from encord.beta.scene.internal.common import (
    DEFAULT_CONVENTION,
    CamelModelApi,
    Convention,
    SelfContainedFormat,
)
from encord.beta.scene.internal.upload import (
    CameraIntrinsics,
    CameraIntrinsicsAdvanced,
    CameraIntrinsicsSimple,
    InputCameraParams,
)
from encord.beta.scene.layout import SceneLayout
from encord.beta.scene.settings import SceneViewSettings
from encord.orm.base_dto import RootModelDTO

__all__ = [
    "DEFAULT_CONVENTION",
    "CameraIntrinsics",
    "CameraIntrinsicsAdvanced",
    "CameraIntrinsicsSimple",
    "CameraParamsEvent",
    "CameraStream",
    "CompositeScene",
    "Convention",
    "EventStream",
    "FOREvent",
    "FORStream",
    "FrameOfReference",
    "ImageStream",
    "ModelEvent",
    "ModelStream",
    "PCDStream",
    "Scene",
    "SelfContainedScene",
    "SelfContainedStream",
    "URIEvent",
]

RotationMatrix = Tuple[float, float, float, float, float, float, float, float, float]
Position = Tuple[float, float, float]


# ---------------------------------------------------------------------------
# Event models
# ---------------------------------------------------------------------------


@dataclass
class URIEvent:
    """An event with both the raw URI and a signed download URL."""

    url: str
    signed_url: str
    timestamp: Optional[float] = None


@dataclass
class CameraParamsEvent(InputCameraParams):
    timestamp: Optional[float] = None


@dataclass
class FrameOfReference:
    id: str
    rotation: RotationMatrix
    position: Position
    parent_for: Optional[str] = None


@dataclass
class FOREvent:
    id: str
    rotation: RotationMatrix
    position: Position
    timestamp: Optional[float] = None
    parent_for: Optional[str] = None


@dataclass
class ModelEvent:
    timestamp: Optional[float] = None
    geometries: Optional[list] = None


# ---------------------------------------------------------------------------
# Stream models
# ---------------------------------------------------------------------------


class PCDStream(CamelModelApi):
    entity_type: Literal["point_cloud"] = "point_cloud"
    frame_of_reference_id: Optional[str] = None
    events: Annotated[List[URIEvent], Field(description="List of point cloud events")]


class ImageStream(CamelModelApi):
    entity_type: Literal["image"] = "image"
    camera_id: Optional[str] = None
    events: List[URIEvent]


class ModelStream(CamelModelApi):
    entity_type: Literal["model"] = "model"
    events: List[URIEvent]


class CameraStream(CamelModelApi):
    entity_type: Literal["camera_parameters"] = "camera_parameters"
    frame_of_reference_id: Optional[str] = None
    events: List[CameraParamsEvent]


class FORStream(CamelModelApi):
    entity_type: Literal["frame_of_reference"] = "frame_of_reference"
    events: Annotated[List[FOREvent], Field(description="List of frame of reference events")]


class EventStream(CamelModelApi):
    type: Literal["event"] = "event"
    id: str
    stream: Annotated[
        Union[PCDStream, CameraStream, FORStream, ImageStream, ModelStream],
        Field(discriminator="entity_type"),
    ]


class SelfContainedStream(CamelModelApi):
    type: Literal["self_contained"] = "self_contained"
    id: str
    entity_type: Literal["time_series"] = "time_series"
    url: str
    signed_url: str


Stream = Annotated[Union[SelfContainedStream, EventStream], Field(discriminator="type")]


# ---------------------------------------------------------------------------
# Scene models
# ---------------------------------------------------------------------------


class _SceneConfig(CamelModelApi):
    default_ground_height: Optional[float] = None
    world_convention: Convention = DEFAULT_CONVENTION
    camera_convention: Convention = DEFAULT_CONVENTION
    view_settings: Optional[SceneViewSettings] = None
    layout: Optional[SceneLayout] = None

    @field_validator("world_convention", "camera_convention", mode="before")
    @classmethod
    def coerce_none_to_default(cls, v: object) -> object:
        if v is None:
            return DEFAULT_CONVENTION
        return v


class CompositeScene(_SceneConfig):
    type: Literal["composite"] = "composite"
    streams: dict[str, Stream]


class SelfContainedScene(_SceneConfig):
    type: Literal["self_contained"] = "self_contained"
    url: str
    signed_url: str
    format: SelfContainedFormat


Scene = Annotated[Union[SelfContainedScene, CompositeScene], Field(discriminator="type")]


class SceneResponse(RootModelDTO[Scene]):
    """Wrapper so the API client can deserialize the discriminated Scene union."""

    pass
