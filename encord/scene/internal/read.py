"""Pydantic models for DbScene (the scene definition stored in the DB) with mixins flattened.

This mirrors the backend's scene_models.py / stream_models.py / event_models.py / entities.py / mixins.py
but flattens all mixins (_MixinSceneConfig, _FORIdMixin, _EventMixin, _URIMixin, CameraParams, FrameOfReference)
directly into the models that use them.

Shared types (Convention, Direction, distortion models) are re-used from import_internal.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    field_validator,
    model_validator,
)

from encord.scene.internal.common import DEFAULT_CONVENTION as DEFAULT_CONVENTION
from encord.scene.internal.common import CamelModelApi
from encord.scene.internal.common import Convention as Convention
from encord.scene.internal.common import Direction as Direction
from encord.scene.internal.common import DistortionModel as DistortionModel
from encord.scene.internal.common import SelfContainedFormat as SelfContainedFormat

# ---------------------------------------------------------------------------
# SceneType
# ---------------------------------------------------------------------------


class SceneType(str, Enum):
    SELF_CONTAINED = "self_contained"
    COMPOSITE = "composite"


# ---------------------------------------------------------------------------
# EntityType / StreamType
# ---------------------------------------------------------------------------


class EntityType(str, Enum):
    POINT_CLOUD = "point_cloud"
    FRAME_OF_REFERENCE = "frame_of_reference"
    IMAGE = "image"
    CAMERA_PARAMETERS = "camera_parameters"


class StreamType(str, Enum):
    SELF_CONTAINED = "self_contained"
    EVENT = "event"


class CameraIntrinsicsSimple(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Annotated[Literal["simple"], Field(default="simple")]
    model: Annotated[DistortionModel | None, Field(description="Distortion Model")] = None
    fx: Annotated[float, Field(description="Focal length x")]
    fy: Annotated[float, Field(description="Focal length y")]
    ox: Annotated[float, Field(description="Principal point offset x")]
    oy: Annotated[float, Field(description="Principal point offset y")]
    dfx: Annotated[float | None, Field(description="Distorted Focal length x")] = None
    dfy: Annotated[float | None, Field(description="Distorted Focal length y")] = None
    dox: Annotated[float | None, Field(description="Distorted Principal point offset x")] = None
    doy: Annotated[float | None, Field(description="Distorted Principal point offset y")] = None
    skew: Annotated[float | None, Field(description="Axis skew", validation_alias=AliasChoices("skew", "s"))] = None


class CameraIntrinsicsAdvanced(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["advanced"]
    model: Annotated[DistortionModel | None, Field(default=None, description="Distortion Model")]
    k: Annotated[
        list[float] | None,
        Field(default=None, description="Intrinsic Camera Matrix for Distorted Images", min_length=9, max_length=9),
    ]
    r: Annotated[
        list[float] | None, Field(default=None, description="Rectification Matrix", min_length=9, max_length=9)
    ]
    p: Annotated[
        list[float] | None, Field(default=None, description="Projection Camera Matrix", min_length=12, max_length=12)
    ]
    skew: Annotated[float | None, Field(description="Axis skew", validation_alias=AliasChoices("skew", "s"))] = None


CameraIntrinsics = Annotated[Union[CameraIntrinsicsSimple, CameraIntrinsicsAdvanced], Field(discriminator="type")]


# ---------------------------------------------------------------------------
# CameraExtrinsics (deprecated) & primitive type aliases
# ---------------------------------------------------------------------------

# fmt: off
RotationMatrix = tuple[
    float, float, float,
    float, float, float,
    float, float, float,
]
# fmt: on
Position = tuple[float, float, float]
EulerOrientation = tuple[float, float, float]
Size = tuple[float, float, float]


class CameraExtrinsics(BaseModel):
    """@deprecated - this should not be used"""

    rotation: Annotated[RotationMatrix, Field(description="Rotation matrix R")]
    position: Annotated[Position, Field(description="Translation vector T")]


# ---------------------------------------------------------------------------
# Geometry types (for ModelEvent)
# ---------------------------------------------------------------------------


class Pose(CamelModelApi):
    position: Position
    orientation: EulerOrientation


# ---------------------------------------------------------------------------
# Event types (mixins flattened)
# ---------------------------------------------------------------------------


@dataclass
class DbURIEvent:
    """Flattened from _EventMixin + _URIMixin."""

    uri: str
    timestamp: float | None = None


@dataclass
class CameraParamsEvent:
    """Flattened from CameraParams + _EventMixin."""

    width_px: Annotated[int, Field(description="The width in px of images produced by this camera")]
    height_px: Annotated[int, Field(description="The height in px of images produced by this camera")]
    intrinsics: Annotated[CameraIntrinsics, Field(description="Camera intrinsics")]
    extrinsics: Annotated[CameraExtrinsics | None, Field(description="Camera extrinsics", default=None)] = None
    timestamp: float | None = None

    @model_validator(mode="before")
    @classmethod
    def add_type_is_missing(cls, data: object | dict) -> object | dict:
        if isinstance(data, dict) and "intrinsics" in data and "type" not in data["intrinsics"]:
            data["intrinsics"]["type"] = "simple"
        return data


@dataclass
class FOREvent:
    """Flattened from FrameOfReference + _EventMixin."""

    id: Annotated[str, Field(description="ID of this frame of reference")]
    parent_FOR: Annotated[str | None, Field(description="ID of a parent frame of reference")]
    rotation: RotationMatrix
    position: Position
    timestamp: float | None = None


# ---------------------------------------------------------------------------
# Stream types (mixins flattened)
# ---------------------------------------------------------------------------


class DbPCDStream(CamelModelApi):
    """Point cloud stream. Flattened from _FORIdMixin."""

    entity_type: Literal[EntityType.POINT_CLOUD] = EntityType.POINT_CLOUD
    events: Annotated[list[DbURIEvent], Field(description="List of point cloud events")]
    frame_of_reference_id: Annotated[str | None, Field(description="ID of the frame of reference the entity is in")] = (
        None
    )


class CameraStream(CamelModelApi):
    """Camera parameters stream. Flattened from _FORIdMixin."""

    entity_type: Literal[EntityType.CAMERA_PARAMETERS] = EntityType.CAMERA_PARAMETERS
    events: list[CameraParamsEvent]
    frame_of_reference_id: Annotated[str | None, Field(description="ID of the frame of reference the entity is in")] = (
        None
    )


class FORStream(CamelModelApi):
    entity_type: Literal[EntityType.FRAME_OF_REFERENCE] = EntityType.FRAME_OF_REFERENCE
    events: Annotated[list[FOREvent], Field(description="List of frame of reference events")]


class DbImageStream(CamelModelApi):
    entity_type: Literal[EntityType.IMAGE] = EntityType.IMAGE
    events: list[DbURIEvent]
    camera_id: Annotated[
        str | None, Field(description="ID of the camera associated with the image. Used to position the image in-scene")
    ]


class DbEventStream(CamelModelApi):
    type: Literal[StreamType.EVENT] = StreamType.EVENT
    id: str
    stream: Annotated[
        DbPCDStream | CameraStream | FORStream | DbImageStream,
        Field(discriminator="entity_type"),
    ]


class DbSelfContainedStream(CamelModelApi):
    type: Literal[StreamType.SELF_CONTAINED] = StreamType.SELF_CONTAINED
    id: str
    entity_type: EntityType
    uri: str


DbStream = Annotated[Union[DbSelfContainedStream, DbEventStream], Field(discriminator="type")]


# ---------------------------------------------------------------------------
# Scene types (flattened from _MixinSceneConfig)
# ---------------------------------------------------------------------------


class DbSelfContainedScene(CamelModelApi):
    type: Literal[SceneType.SELF_CONTAINED] = SceneType.SELF_CONTAINED
    uri: str
    format: SelfContainedFormat
    default_ground_height: Annotated[
        float | None,
        Field(description="The default ground height of the scene, value in the UP axis"),
    ] = None
    world_convention: Annotated[
        Convention,
        Field(
            examples=[Convention(x=Direction.LEFT, y=Direction.UP, z=Direction.BACKWARD)],
            description="How the scene's coordinate system is related to data dimensions",
        ),
    ] = DEFAULT_CONVENTION
    camera_convention: Annotated[
        Convention,
        Field(
            examples=[Convention(x=Direction.LEFT, y=Direction.UP, z=Direction.BACKWARD)],
            description="How the camera's coordinate system is oriented relative to the scene",
        ),
    ] = DEFAULT_CONVENTION

    @field_validator("world_convention", "camera_convention", mode="before")
    @classmethod
    def coerce_none_to_default(cls, v: Convention | None) -> Convention:
        if v is None:
            return DEFAULT_CONVENTION
        return v


class DbCompositeScene(CamelModelApi):
    type: Literal[SceneType.COMPOSITE] = SceneType.COMPOSITE
    streams: dict[str, DbStream]
    default_ground_height: Annotated[
        float | None,
        Field(description="The default ground height of the scene, value in the UP axis"),
    ] = None
    world_convention: Annotated[
        Convention,
        Field(
            examples=[Convention(x=Direction.LEFT, y=Direction.UP, z=Direction.BACKWARD)],
            description="How the scene's coordinate system is related to data dimensions",
        ),
    ] = DEFAULT_CONVENTION
    camera_convention: Annotated[
        Convention,
        Field(
            examples=[Convention(x=Direction.LEFT, y=Direction.UP, z=Direction.BACKWARD)],
            description="How the camera's coordinate system is oriented relative to the scene",
        ),
    ] = DEFAULT_CONVENTION

    @field_validator("world_convention", "camera_convention", mode="before")
    @classmethod
    def coerce_none_to_default(cls, v: Convention | None) -> Convention:
        if v is None:
            return DEFAULT_CONVENTION
        return v


DbScene = Annotated[Union[DbSelfContainedScene, DbCompositeScene], Field(discriminator="type")]

DbSceneAdapter: TypeAdapter[DbScene] = TypeAdapter(DbScene)
