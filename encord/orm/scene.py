"""ORM models for Scene data structures.

These models represent the scene JSON structure returned by the backend API
for composite and self-contained scenes with point clouds, cameras, and
frame of reference (FOR) hierarchies.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, Union, overload

from pydantic import BaseModel, ConfigDict, Field


class AxisDirection(str, Enum):
    """Direction that an axis points in world or camera coordinates."""

    FORWARD = "forward"
    BACKWARD = "backward"
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"


class Convention(BaseModel):
    """Axis direction convention for world or camera coordinates."""

    model_config = ConfigDict(populate_by_name=True)

    x: AxisDirection
    y: AxisDirection
    z: AxisDirection


class SceneType(str, Enum):
    """Type of scene - composite (multiple assets) or self-contained."""

    COMPOSITE = "composite"
    SELF_CONTAINED = "self_contained"


class StreamEntityType(str, Enum):
    """Type of entity in a stream."""

    IMAGE = "image"
    POINT_CLOUD = "point_cloud"
    FRAME_OF_REFERENCE = "frame_of_reference"
    CAMERA_PARAMETERS = "camera_parameters"


# --- Event Types ---


class URIEvent(BaseModel):
    """Event with a URL and timestamp, used for images and point clouds.

    Attributes:
        url: The unsigned URL as given in the cloud upload JSON when creating the scene.
        signed_url: The signed URL for downloading the resource.
        uri: Deprecated, use `url` or `signed_url` instead.
        timestamp: The timestamp of this event.
    """

    model_config = ConfigDict(populate_by_name=True)

    url: Optional[str] = None
    signed_url: Optional[str] = Field(default=None, alias="signedUrl")
    uri: Optional[str] = None  # Deprecated
    timestamp: float

    @property
    def download_url(self) -> str:
        """Get the URL to use for downloading (signed_url preferred, falls back to uri)."""
        return self.signed_url or self.uri or ""

    @property
    def stable_url(self) -> str:
        """Get the stable/unsigned URL for caching (url preferred, falls back to uri)."""
        return self.url or self.uri or ""


class FrameOfReferenceEvent(BaseModel):
    """Event representing a frame of reference at a specific timestamp.

    The rotation is a 9-element array representing a 3x3 rotation matrix
    in row-major order.

    The position is a 3-element array [x, y, z].
    """

    model_config = ConfigDict(populate_by_name=True)

    id: str
    parent_FOR: Optional[str] = Field(default=None, alias="parentFOR")
    rotation: List[float]  # 9 elements (3x3 rotation matrix, row-major)
    position: List[float]  # 3 elements [x, y, z]
    timestamp: Optional[float] = None


class RadialDistortionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["radial"]
    k1: float
    k2: float
    k3: float


class PlumbBobDistortionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["plumb_bob"]
    k1: float
    k2: float
    k3: float
    t1: float
    t2: float


class FishEyeDistortionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["fisheye"]
    k1: float
    k2: float
    k3: float
    k4: float


class RationalPolynomialDistortionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["rational_polynomial"]
    k1: float
    k2: float
    k3: float
    k4: float
    k5: float
    k6: float
    t1: float
    t2: float


class EquidistantDistortionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["equidistant"]
    k1: float
    k2: float
    k3: float
    k4: float


class PinholeDistortionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["pinhole"]


class DivisionDistortionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["division"]
    k: float


class UCMDistortionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["ucm"]
    xi: float
    k1: float
    k2: float
    k3: float


DistortionModel = Annotated[
    Union[
        RadialDistortionModel,
        PlumbBobDistortionModel,
        FishEyeDistortionModel,
        RationalPolynomialDistortionModel,
        EquidistantDistortionModel,
        PinholeDistortionModel,
        DivisionDistortionModel,
        UCMDistortionModel,
    ],
    Field(discriminator="type"),
]


class CameraIntrinsics(BaseModel):
    """Camera intrinsic parameters."""

    model_config = ConfigDict(populate_by_name=True)

    type: str = "simple"
    model: Optional[DistortionModel] = None
    fx: float
    fy: float
    ox: float
    oy: float
    dfx: Optional[float] = None
    dfy: Optional[float] = None
    dox: Optional[float] = None
    doy: Optional[float] = None
    skew: float = 0.0


class CameraExtrinsics(BaseModel):
    """DEPRECATED: Camera extrinsic parameters (rotation and position)."""

    model_config = ConfigDict(populate_by_name=True)

    rotation: List[float]  # 9 elements (3x3 rotation matrix, row-major)
    position: List[float]  # 3 elements [x, y, z]


class CameraParametersEvent(BaseModel):
    """Event with camera parameters (intrinsics and extrinsics)."""

    model_config = ConfigDict(populate_by_name=True)

    timestamp: float
    widthPx: int = Field(alias="widthPx")
    heightPx: int = Field(alias="heightPx")
    intrinsics: CameraIntrinsics

    """Deprecated legacy stuff: all transforms should use frame of reference ID"""
    extrinsics: Optional[CameraExtrinsics] = None

    frameOfReferenceId: Optional[str] = Field(default=None, alias="frameOfReferenceId")


# --- Stream Types ---


class ImageStream(BaseModel):
    """Stream containing image events."""

    model_config = ConfigDict(populate_by_name=True)

    entityType: Literal["image"] = Field(alias="entityType")
    events: List[URIEvent]
    cameraId: Optional[str] = Field(default=None, alias="cameraId")


class PointCloudStream(BaseModel):
    """Stream containing point cloud events."""

    model_config = ConfigDict(populate_by_name=True)

    entityType: Literal["point_cloud"] = Field(alias="entityType")
    events: List[URIEvent]
    frameOfReferenceId: Optional[str] = Field(default=None, alias="frameOfReferenceId")


class FrameOfReferenceStream(BaseModel):
    """Stream containing frame of reference events."""

    model_config = ConfigDict(populate_by_name=True)

    entityType: Literal["frame_of_reference"] = Field(alias="entityType")
    events: List[FrameOfReferenceEvent]


class CameraParametersStream(BaseModel):
    """Stream containing camera parameter events."""

    model_config = ConfigDict(populate_by_name=True)

    entityType: Literal["camera_parameters"] = Field(alias="entityType")
    events: List[CameraParametersEvent]
    frameOfReferenceId: Optional[str] = Field(default=None, alias="frameOfReferenceId")


# Union of all stream types
StreamData = Union[ImageStream, PointCloudStream, FrameOfReferenceStream, CameraParametersStream]

# Stream kind literals
StreamKind = Literal["image", "point_cloud", "frame_of_reference", "camera_parameters"]


class StreamWrapper(BaseModel):
    """Wrapper around a stream with metadata."""

    model_config = ConfigDict(populate_by_name=True)

    type: str  # "event"
    id: str
    stream: Dict[str, Any]  # Parsed dynamically based on entityType

    def get_stream_data(self) -> StreamData:
        """Parse and return the typed stream data."""
        entity_type = self.stream.get("entityType")
        if entity_type == "image":
            return ImageStream.model_validate(self.stream)
        elif entity_type == "point_cloud":
            return PointCloudStream.model_validate(self.stream)
        elif entity_type == "frame_of_reference":
            return FrameOfReferenceStream.model_validate(self.stream)
        elif entity_type == "camera_parameters":
            return CameraParametersStream.model_validate(self.stream)
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")


class SceneData(BaseModel):
    """Scene data model representing the full scene structure.

    This matches the JSON structure returned by the backend's GET /scene/{uuid} endpoint.
    """

    model_config = ConfigDict(populate_by_name=True)

    type: str  # "composite" or "self_contained"
    worldConvention: Convention = Field(alias="worldConvention")
    cameraConvention: Convention = Field(alias="cameraConvention")
    defaultGroundHeight: Optional[float] = Field(default=None, alias="defaultGroundHeight")
    streams: Dict[str, StreamWrapper]

    @overload
    def get_streams(self, kind: Literal["image"]) -> Dict[str, ImageStream]: ...

    @overload
    def get_streams(self, kind: Literal["point_cloud"]) -> Dict[str, PointCloudStream]: ...

    @overload
    def get_streams(self, kind: Literal["frame_of_reference"]) -> Dict[str, FrameOfReferenceStream]: ...

    @overload
    def get_streams(self, kind: Literal["camera_parameters"]) -> Dict[str, CameraParametersStream]: ...

    def get_streams(self, kind: StreamKind) -> Dict[str, StreamData]:  # type: ignore[misc]
        result: Dict[str, Any] = {}
        for stream_id, wrapper in self.streams.items():
            if wrapper.stream.get("entityType") == kind:
                if kind == "image":
                    result[stream_id] = ImageStream.model_validate(wrapper.stream)
                elif kind == "point_cloud":
                    result[stream_id] = PointCloudStream.model_validate(wrapper.stream)
                elif kind == "frame_of_reference":
                    result[stream_id] = FrameOfReferenceStream.model_validate(wrapper.stream)
                elif kind == "camera_parameters":
                    result[stream_id] = CameraParametersStream.model_validate(wrapper.stream)
        return result
