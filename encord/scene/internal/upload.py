"""Pydantic models for InputScene with all dependencies inlined.

Shared types (Convention, Direction, distortion models, SelfContainedFormat) live in common_internal.
"""

from __future__ import annotations

import datetime
import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Annotated, Literal, Optional, Union

from pydantic import (
    AliasChoices,
    AnyUrl,
    BaseModel,
    ConfigDict,
    Discriminator,
    Field,
    RootModel,
    Tag,
    field_validator,
    model_validator,
)
from typing_extensions import TypeAlias

from encord.scene.internal.common import DEFAULT_CONVENTION as DEFAULT_CONVENTION
from encord.scene.internal.common import DIRECTION_TO_VECTOR as DIRECTION_TO_VECTOR
from encord.scene.internal.common import CamelModel as CamelModel
from encord.scene.internal.common import CamelModelApi as CamelModelApi
from encord.scene.internal.common import Convention as Convention
from encord.scene.internal.common import Direction as Direction
from encord.scene.internal.common import DistortionModel as DistortionModel
from encord.scene.internal.common import DivisionDistortionModel as DivisionDistortionModel
from encord.scene.internal.common import FishEyeDistortionModel as FishEyeDistortionModel
from encord.scene.internal.common import PinholeDistortionModel as PinholeDistortionModel
from encord.scene.internal.common import PlumbBobDistortionModel as PlumbBobDistortionModel
from encord.scene.internal.common import RadialDistortionModel as RadialDistortionModel
from encord.scene.internal.common import RationalPolynomialDistortionModel as RationalPolynomialDistortionModel
from encord.scene.internal.common import SelfContainedFormat as SelfContainedFormat
from encord.scene.internal.common import UCMDistortionModel as UCMDistortionModel


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
# Geometry types (for ModelEvent)
# ---------------------------------------------------------------------------

Position = tuple[float, float, float]
EulerOrientation = tuple[float, float, float]
Size = tuple[float, float, float]


class GeometryType(str, Enum):
    CUBOID = "cuboid"
    ELLIPSOID = "ellipsoid"
    LINE = "line"
    MODEL = "model"


class Pose(CamelModelApi):
    position: Position
    orientation: EulerOrientation


class CuboidGeometry(CamelModelApi):
    type: Literal[GeometryType.CUBOID] = GeometryType.CUBOID
    pose: Pose
    size: Size


class EllipsoidGeometry(CamelModelApi):
    type: Literal[GeometryType.ELLIPSOID] = GeometryType.ELLIPSOID
    pose: Pose
    size: Size


class LineGeometry(CamelModelApi):
    type: Literal[GeometryType.LINE] = GeometryType.LINE
    pose: Pose
    points: list[Position]


class ModelGeometry(CamelModelApi):
    type: Literal[GeometryType.MODEL] = GeometryType.MODEL
    pose: Pose
    scale: Size
    url: str


Geometry = Annotated[
    Union[CuboidGeometry, EllipsoidGeometry, LineGeometry, ModelGeometry],
    Field(discriminator="type"),
]

# ---------------------------------------------------------------------------
# Format mapping for URL extension validation
# ---------------------------------------------------------------------------

_FORMAT_MAPPING = {
    "pcd": SelfContainedFormat.PCD,
    "ply": SelfContainedFormat.PLY,
    "las": SelfContainedFormat.LAS,
    "laz": SelfContainedFormat.LAZ,
    "e57": SelfContainedFormat.E57,
    "mcap": SelfContainedFormat.MCAP,
    "bag": SelfContainedFormat.BAG,
    "db3": SelfContainedFormat.DB3,
}


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class ValidatedSceneUrlWithExtension(RootModel):
    root: AnyUrl

    @field_validator("root")
    @classmethod
    def validate_format(cls, v: AnyUrl) -> AnyUrl:
        url_str = str(v)
        extension = Path(url_str).suffix.lower().lstrip(".")
        if extension not in _FORMAT_MAPPING:
            raise ValueError(
                f"Unsupported scene file format: {extension}. Supported formats: {list(_FORMAT_MAPPING.keys())}"
            )
        return v

    def __str__(self) -> str:
        return str(self.root)


class ValidatedSceneUrlWithFormat(BaseModel):
    url: AnyUrl
    format: str

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        if v not in _FORMAT_MAPPING:
            raise ValueError(f"Unsupported scene file format: {v}. Supported formats: {list(_FORMAT_MAPPING.keys())}")
        return v


class InputPosition(BaseModel):
    x: float
    y: float
    z: float


class InputRotationMatrix(RootModel[tuple[float, float, float, float, float, float, float, float, float]]):
    @model_validator(mode="after")
    def validate_rotation_matrix(self) -> InputRotationMatrix:
        m00, m01, m02, m10, m11, m12, m20, m21, m22 = self.root
        tolerance = 1e-2

        row0_mag = math.sqrt(m00**2 + m01**2 + m02**2)
        row1_mag = math.sqrt(m10**2 + m11**2 + m12**2)
        row2_mag = math.sqrt(m20**2 + m21**2 + m22**2)

        if abs(row0_mag - 1.0) > tolerance:
            raise ValueError(f"Row 0 is not a unit vector (magnitude: {row0_mag})")
        if abs(row1_mag - 1.0) > tolerance:
            raise ValueError(f"Row 1 is not a unit vector (magnitude: {row1_mag})")
        if abs(row2_mag - 1.0) > tolerance:
            raise ValueError(f"Row 2 is not a unit vector (magnitude: {row2_mag})")

        dot_01 = m00 * m10 + m01 * m11 + m02 * m12
        dot_02 = m00 * m20 + m01 * m21 + m02 * m22
        dot_12 = m10 * m20 + m11 * m21 + m12 * m22

        if abs(dot_01) > tolerance:
            raise ValueError(f"Rows 0 and 1 are not orthogonal (dot product: {dot_01})")
        if abs(dot_02) > tolerance:
            raise ValueError(f"Rows 0 and 2 are not orthogonal (dot product: {dot_02})")
        if abs(dot_12) > tolerance:
            raise ValueError(f"Rows 1 and 2 are not orthogonal (dot product: {dot_12})")

        det = m00 * (m11 * m22 - m12 * m21) - m01 * (m10 * m22 - m12 * m20) + m02 * (m10 * m21 - m11 * m20)
        if abs(det - 1.0) > tolerance:
            raise ValueError(f"Determinant is not 1 (det: {det}). This is not a proper rotation matrix.")

        return self


class InputQuaternion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    x: Annotated[float, Field(ge=-1.0, le=1.0)]
    y: Annotated[float, Field(ge=-1.0, le=1.0)]
    z: Annotated[float, Field(ge=-1.0, le=1.0)]
    w: Annotated[float, Field(ge=-1.0, le=1.0)]

    @model_validator(mode="after")
    def validate_unit_quaternion(self) -> InputQuaternion:
        magnitude = math.sqrt(self.x**2 + self.y**2 + self.z**2 + self.w**2)
        tolerance = 1e-2
        if abs(magnitude - 1.0) > tolerance:
            raise ValueError(
                f"Quaternion must have unit length. "
                f"Current magnitude: {magnitude}. "
                f"Consider normalizing: ({self.x / magnitude}, {self.y / magnitude}, "
                f"{self.z / magnitude}, {self.w / magnitude})"
            )
        return self


class InputEulerRotation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    x: Annotated[float, Field(ge=-2.1 * math.pi, le=2.1 * math.pi, description="Rotation around x-axis in radians")]
    y: Annotated[float, Field(ge=-2.1 * math.pi, le=2.1 * math.pi, description="Rotation around y-axis in radians")]
    z: Annotated[float, Field(ge=-2.1 * math.pi, le=2.1 * math.pi, description="Rotation around z-axis in radians")]


def discriminate_rotation(arg: dict | tuple | list | object) -> str:
    if isinstance(arg, (list, tuple, InputRotationMatrix)):
        return "matrix"
    elif isinstance(arg, dict):
        return "quaternion" if "w" in arg else "euler"
    elif isinstance(arg, InputEulerRotation):
        return "euler"
    elif isinstance(arg, InputQuaternion):
        return "quaternion"
    return "quaternion" if hasattr(arg, "w") else "euler"


class InputRotation(RootModel):
    root: Annotated[
        Annotated[InputRotationMatrix, Tag("matrix")]
        | Annotated[InputEulerRotation, Tag("euler")]
        | Annotated[InputQuaternion, Tag("quaternion")],
        Field(
            description="Rotation component of pose. If provided as a matrix it must be in column major order.",
            examples=[
                InputEulerRotation(x=0, y=0, z=0),
                InputQuaternion(x=0, y=0, z=0, w=1),
                (1, 0, 0, 0, 1, 0, 0, 0, 1),
            ],
            discriminator=Discriminator(discriminate_rotation),
        ),
    ]


class InputCompositePose(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rotation: Annotated[
        InputRotation,
        Field(
            description="Rotation component of pose",
            examples=[InputRotation(root=InputQuaternion(x=1, y=0, z=0, w=0))],
        ),
    ]
    position: Annotated[
        InputPosition,
        Field(description="Position component of pose", examples=[InputPosition(x=0, y=0, z=0)]),
    ]


class InputAffineTransform(
    RootModel[
        tuple[
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
        ]
    ]
):
    @model_validator(mode="after")
    def validate_affine_matrix(self) -> InputAffineTransform:
        """Validate that the matrix is a proper affine matrix (orthogonal with det=1) & only translation"""
        m00, m01, m02, m03, m10, m11, m12, m13, m20, m21, m22, m23, m30, m31, m32, m33 = self.root
        _rot = InputRotationMatrix(root=(m00, m01, m02, m10, m11, m12, m20, m21, m22))
        if m03 != 0.0 or m13 != 0.0 or m23 != 0.0:
            raise ValueError(f"Affine non translate values are not 0.0: {m03},{m13},{m23}")
        if m33 != 1.0:
            raise ValueError(f"Affine matrix value m33 is not 1.0: {m33}")
        return self


def discriminate_pose(arg: list | tuple | dict | InputCompositePose | InputAffineTransform) -> str:
    return "affine" if isinstance(arg, (list, tuple, InputAffineTransform)) else "pose"


class InputPose(RootModel):
    root: Annotated[
        Annotated[InputCompositePose, Tag("pose")] | Annotated[InputAffineTransform, Tag("affine")],
        Field(
            description="Position and orientation for an object or reference frame in 3D space",
            examples=[
                InputCompositePose(
                    rotation=InputRotation(root=InputEulerRotation(x=0, y=0, z=0)),
                    position=InputPosition(x=0, y=0, z=0),
                )
            ],
            discriminator=Discriminator(discriminate_pose),
        ),
    ]


FrameOfReferenceId = str
CameraId = str

FrameOfReferenceType: TypeAlias = Annotated[
    Optional[FrameOfReferenceId],
    Field(
        description="A frame of reference to use as a base",
        examples=["ego_vehicle", "camera-left"],
        validation_alias=AliasChoices("frameOfReference", "frame_of_reference", "referenceFrame"),
    ),
]

PoseType: TypeAlias = Annotated[
    Optional[InputPose],
    Field(
        description="A static transformation to apply the the chosen frame of reference",
        examples=[
            InputCompositePose(
                rotation=InputRotation(root=InputQuaternion(x=0, y=0, z=0, w=1)), position=InputPosition(x=0, y=0, z=0)
            ),
        ],
        validation_alias=AliasChoices("pose", "transform"),
    ),
]

Timestamp: TypeAlias = Annotated[
    Union[int, float, datetime.datetime, datetime.time, None],
    Field(validation_alias=AliasChoices("timestamp", "time"), default=None),
]


# ---------------------------------------------------------------------------
# Camera intrinsics for input
# ---------------------------------------------------------------------------


class InputCameraParams(BaseModel):
    width_px: Annotated[int, Field(ge=0, validation_alias=AliasChoices("widthPx", "width_px", "width"))]
    height_px: Annotated[int, Field(ge=0, validation_alias=AliasChoices("heightPx", "height_px", "height"))]
    intrinsics: Annotated[CameraIntrinsics, Field(description="Camera intrinsics")]
    extrinsics: Annotated[InputPose | None, Field(description="Camera exterinsics (deprecated)")] = None

    @model_validator(mode="before")
    @classmethod
    def add_type_is_missing(cls, data: object | dict) -> object | dict:
        if (
            isinstance(data, dict)
            and "intrinsics" in data
            and isinstance(data["intrinsics"], dict)
            and "type" not in data["intrinsics"]
        ):
            data["intrinsics"]["type"] = "simple"
        return data


# ---------------------------------------------------------------------------
# Stream event types
# ---------------------------------------------------------------------------


class InputFoREvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    timestamp: Timestamp = None
    pose: Annotated[InputPose, Field(description="Pose of the frame of reference")]


class InputCameraParamsEvent(InputCameraParams):
    model_config = ConfigDict(extra="forbid")
    timestamp: Timestamp = None


class InputURIEvent(BaseModel):
    timestamp: Timestamp = None
    uri: str


# ---------------------------------------------------------------------------
# Entity / stream types
# ---------------------------------------------------------------------------


class InputEntityType(str, Enum):
    POINT_CLOUD = "point_cloud"
    FRAME_OF_REFERENCE = "frame_of_reference"
    IMAGE = "image"
    CAMERA_PARAMETERS = "camera_parameters"

    @classmethod
    def _missing_(cls, value: object) -> InputEntityType:
        if not isinstance(value, str):
            raise ValueError(f"Unknown entity type: {value} is not a string")
        if value == "camera":
            return cls.CAMERA_PARAMETERS
        raise ValueError(f"Unknown entity type: {value}")


class InputCameraStream(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["camera_parameters"] = "camera_parameters"
    events: list[InputCameraParamsEvent]
    frame_of_reference: FrameOfReferenceType = None
    pose: PoseType = None


class InputImageStream(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["image"] = "image"
    camera: Annotated[CameraId, Field(description="ID or params of the camera associated with the image")]
    events: list[InputURIEvent]


class InputPCDStream(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["point_cloud"] = "point_cloud"
    events: Annotated[list[InputURIEvent], Field(description="List of point clouds")]
    frame_of_reference: FrameOfReferenceType = None
    pose: PoseType = None


class InputFoRStream(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["frame_of_reference"] = "frame_of_reference"
    id: Annotated[str, Field(description="ID of this frame of reference")]
    parent_FoR_id: Annotated[
        str | None,
        Field(
            description="ID of a parent frame of reference",
            validation_alias=AliasChoices("parentForId", "parent_FoR_id", "parent_for_id", "parent", "parentId"),
        ),
    ]
    events: Annotated[list[InputFoREvent], Field(description="List of frame of reference")]


InputStream: TypeAlias = Annotated[
    Union[InputPCDStream, InputCameraStream, InputFoRStream, InputImageStream],
    Field(discriminator="type"),
]


class Streams(RootModel):
    root: Annotated[
        dict[str, InputStream],
        Field(description="A collection of streams of messages describing the entities in the scene over time"),
    ]
    model_config = ConfigDict(json_schema_extra={"not": {"required": ["content", "type"]}})


# ---------------------------------------------------------------------------
# Scene content discriminators
# ---------------------------------------------------------------------------


def discriminate_content(arg: dict | str | InputPCDStream | Streams | object) -> str:
    if isinstance(arg, (str, ValidatedSceneUrlWithExtension)):
        return "urlWithExtension"
    if isinstance(arg, ValidatedSceneUrlWithFormat):
        return "urlWithFormat"
    if isinstance(arg, dict) and "url" in arg and "format" in arg:
        return "urlWithFormat"
    if hasattr(arg, "url") and hasattr(arg, "format"):
        return "urlWithFormat"
    if isinstance(arg, InputPCDStream):
        return "pcd"
    if isinstance(arg, Streams):
        return "streams"
    if isinstance(arg, dict) and arg.get("type") in ("point_cloud", InputEntityType.POINT_CLOUD):
        return "pcd"
    if hasattr(arg, "type") and getattr(arg, "type", None) in ("point_cloud", InputEntityType.POINT_CLOUD):
        return "pcd"
    return "streams"


class SceneContent(
    RootModel[
        Annotated[
            Union[
                Annotated[Streams, Tag("streams")],
                Annotated[InputPCDStream, Tag("pcd")],
                Annotated[ValidatedSceneUrlWithExtension, Tag("urlWithExtension")],
                Annotated[ValidatedSceneUrlWithFormat, Tag("urlWithFormat")],
            ],
            Field(discriminator=Discriminator(discriminate_content)),
        ]
    ]
):
    model_config = ConfigDict(json_schema_extra={"not": {"required": ["content"]}})


class SceneWithConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: Annotated[SceneContent, Field(description="Content in the scene")]
    default_ground_height: Annotated[
        float | None,
        Field(
            description="The default ground height of the scene, value in the UP axis",
            validation_alias=AliasChoices("defaultGroundHeight", "defaultGround", "default_ground_height"),
        ),
    ] = None
    world_convention: Annotated[
        Convention | None,
        Field(
            examples=[Convention(x=Direction.LEFT, y=Direction.UP, z=Direction.BACKWARD)],
            description="How the scene's coordinate system is related to data dimensions",
            validation_alias=AliasChoices("worldConvention", "world_convention", "world"),
        ),
    ] = None
    camera_convention: Annotated[
        Convention | None,
        Field(
            examples=[Convention(x=Direction.LEFT, y=Direction.UP, z=Direction.BACKWARD)],
            description="How the camera's coordinate system is oriented relative to the scene",
            validation_alias=AliasChoices("cameraConvention", "camera_convention", "camera"),
        ),
    ] = None

    @model_validator(mode="after")
    def check_valid_convention(self) -> SceneWithConfig:
        world_convention = self.world_convention or DEFAULT_CONVENTION
        camera_convention = self.camera_convention or DEFAULT_CONVENTION
        if world_convention.right_handed() != camera_convention.right_handed():
            raise ValueError(
                "Camera and world convention use different handedness, please ensure that "
                "one is a valid rotation of the other: "
                f"world:{'right' if world_convention.right_handed() else 'left'} != "
                f"camera:{'right' if camera_convention.right_handed() else 'left'}"
            )
        return self


def discriminate_config(arg: dict | SceneContent | SceneWithConfig) -> str:
    if isinstance(arg, dict):
        if arg.get("content") is not None:
            return "config"
    return "config" if getattr(arg, "content", None) is not None else "raw"


class SceneOrSceneWithConfig(
    RootModel[
        Annotated[
            Union[Annotated[SceneContent, Tag("raw")], Annotated[SceneWithConfig, Tag("config")]],
            Field(discriminator=Discriminator(discriminate_config)),
        ]
    ]
):
    pass


# ---------------------------------------------------------------------------
# collect_stream_ids (used by InputScene validation)
# ---------------------------------------------------------------------------


@dataclass
class StreamIds:
    image_ids: set[str]
    camera_ids: set[str]
    pcd_ids: set[str]
    for_ids: set[str]


def collect_stream_ids(streams: dict[str, InputStream]) -> StreamIds:
    camera_ids: set[str] = set()
    for_ids: set[str] = set()
    image_ids: set[str] = set()
    pcd_ids: set[str] = set()

    for stream_id, stream in streams.items():
        if isinstance(stream, InputCameraStream):
            camera_ids.add(stream_id)
        if isinstance(stream, InputFoRStream):
            for_ids.add(stream.id)
        if isinstance(stream, InputImageStream):
            image_ids.add(stream_id)
        if isinstance(stream, InputPCDStream):
            pcd_ids.add(stream_id)

    return StreamIds(camera_ids=camera_ids, for_ids=for_ids, image_ids=image_ids, pcd_ids=pcd_ids)


# ---------------------------------------------------------------------------
# InputScene
# ---------------------------------------------------------------------------


class InputScene(SceneOrSceneWithConfig):
    @model_validator(mode="after")
    def validate_scene_structure(self) -> InputScene:
        content = self.root.content.root if isinstance(self.root, SceneWithConfig) else self.root.root

        if isinstance(content, Streams):
            validate_streams(content)

        return self


def validate_streams(content: Streams) -> None:
    stream_ids = collect_stream_ids(content.root)

    if not stream_ids.image_ids and not stream_ids.pcd_ids:
        raise ValueError("Scene must contain at least one point cloud or image stream")

    for stream_id, stream in content.root.items():
        if isinstance(stream, InputImageStream):
            if isinstance(stream.camera, str):
                if stream.camera not in stream_ids.camera_ids:
                    raise ValueError(
                        f"Image stream '{stream_id}' references non-existent camera ID: '{stream.camera}'. "
                        f"Available camera IDs: {stream_ids.camera_ids}"
                    )

        # for stream_id, stream in content.root.items():
        #    if hasattr(stream, "frame_of_reference") and isinstance(stream.frame_of_reference, str):
        #        if stream.frame_of_reference not in stream_ids.for_ids and stream.frame_of_reference != "root":
        #            raise ValueError(
        #                f"Stream '{stream_id}' references non-existent frame of reference ID: "
        #                f"'{stream.frame_of_reference}'. Available FoR IDs: {stream_ids.for_ids}"
        #            )

        if isinstance(stream, InputFoRStream) and stream.parent_FoR_id is not None:
            if stream.parent_FoR_id not in stream_ids.for_ids and stream.parent_FoR_id != "root":
                raise ValueError(
                    f"Frame of reference '{stream.id}' references non-existent parent FoR ID: "
                    f"'{stream.parent_FoR_id}'. Available FoR IDs: {stream_ids.for_ids}"
                )
