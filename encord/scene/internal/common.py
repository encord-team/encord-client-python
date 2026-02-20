"""Shared types used by both import_internal and read_internal.

Contains: snake2camel, CamelModelApi, Direction, Convention, SelfContainedFormat, and all distortion models.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# snake2camel utility
# ---------------------------------------------------------------------------


def snake2camel(snake: str, start_lower: bool = False) -> str:
    camel = snake.title()
    camel = re.sub("([0-9A-Za-z])_(?=[0-9A-Z])", lambda m: m.group(1), camel)
    if start_lower:
        camel = re.sub("(^_*[A-Z])", lambda m: m.group(1).lower(), camel)
    return camel


def _snake2camel_api(x: str) -> str:
    return snake2camel(x, start_lower=True)


# ---------------------------------------------------------------------------
# CamelModel / CamelModelApi base classes
# ---------------------------------------------------------------------------


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=_snake2camel_api, populate_by_name=True)


class CamelModelApi(BaseModel):
    model_config = ConfigDict(alias_generator=_snake2camel_api, populate_by_name=True)


# ---------------------------------------------------------------------------
# Direction / Convention
# ---------------------------------------------------------------------------


class Direction(str, Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    FORWARD = "forward"
    BACKWARD = "backward"


DIRECTION_TO_VECTOR: dict[Direction, tuple[int, int, int]] = {
    Direction.RIGHT: (1, 0, 0),
    Direction.LEFT: (-1, 0, 0),
    Direction.UP: (0, 1, 0),
    Direction.DOWN: (0, -1, 0),
    Direction.FORWARD: (0, 0, 1),
    Direction.BACKWARD: (0, 0, -1),
}


class Convention(BaseModel):
    x: Annotated[Direction, Field(examples=["left"])]
    y: Annotated[Direction, Field(examples=["up"])]
    z: Annotated[Direction, Field(examples=["backward"])]

    @model_validator(mode="after")
    def check_valid_convention(self) -> Convention:
        x_vec = DIRECTION_TO_VECTOR[self.x]
        y_vec = DIRECTION_TO_VECTOR[self.y]
        z_vec = DIRECTION_TO_VECTOR[self.z]
        for axis in range(3):
            non_zero_count = sum([x_vec[axis] != 0, y_vec[axis] != 0, z_vec[axis] != 0])
            if non_zero_count != 1:
                raise ValueError(
                    f"Invalid coordinate system: x={self.x}, y={self.y}, z={self.z}. "
                    "Each axis must be used by exactly one direction."
                )
        return self

    def right_handed(self) -> bool:
        x_vec = DIRECTION_TO_VECTOR[self.x]
        y_vec = DIRECTION_TO_VECTOR[self.y]
        z_vec = DIRECTION_TO_VECTOR[self.z]
        cross: tuple[int, int, int] = (
            x_vec[1] * y_vec[2] - x_vec[2] * y_vec[1],
            x_vec[2] * y_vec[0] - x_vec[0] * y_vec[2],
            x_vec[0] * y_vec[1] - x_vec[1] * y_vec[0],
        )
        return cross == z_vec


DEFAULT_CONVENTION: Convention = Convention(x=Direction.FORWARD, y=Direction.LEFT, z=Direction.UP)


# ---------------------------------------------------------------------------
# SelfContainedFormat
# ---------------------------------------------------------------------------


class SelfContainedFormat(str, Enum):
    PCD = "pcd"
    PLY = "ply"
    LAS = "las"
    LAZ = "laz"
    E57 = "e57"
    MCAP = "mcap"
    BAG = "bag"  # ROS 1
    DB3 = "db3"  # ROS 2


# ---------------------------------------------------------------------------
# Distortion models
# ---------------------------------------------------------------------------


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
        PinholeDistortionModel,
        DivisionDistortionModel,
        UCMDistortionModel,
    ],
    Field(discriminator="type"),
]
