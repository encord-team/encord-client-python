"""
---
title: "Objects - Coordinates"
slug: "sdk-ref-objects-coordinates"
hidden: false
metadata:
  title: "Objects - Coordinates"
  description: "Encord SDK Objects - Coordinates."
category: "64e481b57b6027003f20aaa0"
---
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Flag, auto
from typing import Any, Dict, List, Optional, Type, Union

from encord.exceptions import LabelRowError
from encord.objects.bitmask import BitmaskCoordinates
from encord.objects.common import Shape
from encord.orm.base_dto import BaseDTO


@dataclass(frozen=True)
class BoundingBoxCoordinates:
    """All the values are percentages relative to the total image size."""

    height: float
    width: float
    top_left_x: float
    top_left_y: float

    @staticmethod
    def from_dict(d: dict) -> BoundingBoxCoordinates:
        """Get BoundingBoxCoordinates from an encord dict"""
        bounding_box_dict = d["boundingBox"]
        return BoundingBoxCoordinates(
            height=bounding_box_dict["h"],
            width=bounding_box_dict["w"],
            top_left_x=bounding_box_dict["x"],
            top_left_y=bounding_box_dict["y"],
        )

    def to_dict(self) -> dict:
        return {
            "h": self.height,
            "w": self.width,
            "x": self.top_left_x,
            "y": self.top_left_y,
        }


@dataclass(frozen=True)
class RotatableBoundingBoxCoordinates:
    """All the values are percentages relative to the total image size."""

    height: float
    width: float
    top_left_x: float
    top_left_y: float
    theta: float  # angle of rotation originating at center of box

    @staticmethod
    def from_dict(d: dict) -> RotatableBoundingBoxCoordinates:
        """Get RotatableBoundingBoxCoordinates from an encord dict"""
        rotatable_bounding_box_dict = d["rotatableBoundingBox"]
        return RotatableBoundingBoxCoordinates(
            height=rotatable_bounding_box_dict["h"],
            width=rotatable_bounding_box_dict["w"],
            top_left_x=rotatable_bounding_box_dict["x"],
            top_left_y=rotatable_bounding_box_dict["y"],
            theta=rotatable_bounding_box_dict["theta"],
        )

    def to_dict(self) -> dict:
        return {
            "h": self.height,
            "w": self.width,
            "x": self.top_left_x,
            "y": self.top_left_y,
            "theta": self.theta,
        }


@dataclass(frozen=True)
class PointCoordinate:
    """All coordinates are a percentage relative to the total image size."""

    x: float
    y: float

    @staticmethod
    def from_dict(d: dict) -> PointCoordinate:
        first_item = d["point"]["0"]
        return PointCoordinate(
            x=first_item["x"],
            y=first_item["y"],
        )

    def to_dict(self) -> dict:
        return {"0": {"x": self.x, "y": self.y}}


@dataclass(frozen=True)
class PolygonCoordinates:
    values: List[PointCoordinate]

    @staticmethod
    def from_dict(d: dict) -> PolygonCoordinates:
        polygon_dict = d["polygon"]
        values: List[PointCoordinate] = []

        if isinstance(polygon_dict, dict):
            sorted_dict_value_tuples = sorted((int(key), value) for key, value in polygon_dict.items())
            sorted_dict_values = [item[1] for item in sorted_dict_value_tuples]
        elif isinstance(polygon_dict, list):
            sorted_dict_values = list(polygon_dict)
        else:
            raise LabelRowError(f"Invalid format for polygon coordinates: {polygon_dict}")

        for value in sorted_dict_values:
            point_coordinate = PointCoordinate(
                x=value["x"],
                y=value["y"],
            )
            values.append(point_coordinate)

        return PolygonCoordinates(values=values)

    def to_dict(self) -> dict:
        return {str(idx): {"x": value.x, "y": value.y} for idx, value in enumerate(self.values)}


@dataclass(frozen=True)
class PolylineCoordinates:
    values: List[PointCoordinate]

    @staticmethod
    def from_dict(d: dict) -> PolylineCoordinates:
        polyline = d["polyline"]
        values: List[PointCoordinate] = []

        if isinstance(polyline, dict):
            sorted_dict_value_tuples = sorted((int(key), value) for key, value in polyline.items())
            sorted_dict_values = [item[1] for item in sorted_dict_value_tuples]
        elif isinstance(polyline, list):
            sorted_dict_values = list(polyline)
        else:
            raise LabelRowError(f"Invalid format for polyline coordinates: {polyline}")

        for value in sorted_dict_values:
            point_coordinate = PointCoordinate(
                x=value["x"],
                y=value["y"],
            )
            values.append(point_coordinate)

        return PolylineCoordinates(values=values)

    def to_dict(self) -> dict:
        return {str(idx): {"x": value.x, "y": value.y} for idx, value in enumerate(self.values)}


class Visibility(Flag):
    """
    An item is invisible if it is outside the frame. It is occluded
    if it is covered by something in the frame, but it would otherwise
    be in the frame. Else it is visible.
    """

    VISIBLE = auto()
    INVISIBLE = auto()
    OCCLUDED = auto()


class SkeletonCoordinate(BaseDTO):
    x: float
    y: float
    name: str
    color: Optional[str] = None
    feature_hash: Optional[str] = None
    value: Optional[str] = None

    visibility: Optional[Visibility] = None


class SkeletonCoordinates(BaseDTO):
    values: List[SkeletonCoordinate]
    name: str

    def to_dict(self, by_alias=True, exclude_none=True) -> Dict[str, Any]:
        return {str(i): x.to_dict() for i, x in enumerate(self.values)}


Coordinates = Union[
    BoundingBoxCoordinates,
    RotatableBoundingBoxCoordinates,
    PointCoordinate,
    PolygonCoordinates,
    PolylineCoordinates,
    SkeletonCoordinates,
    BitmaskCoordinates,
]
ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS: Dict[Shape, Type[Coordinates]] = {
    Shape.BOUNDING_BOX: BoundingBoxCoordinates,
    Shape.ROTATABLE_BOUNDING_BOX: RotatableBoundingBoxCoordinates,
    Shape.POINT: PointCoordinate,
    Shape.POLYGON: PolygonCoordinates,
    Shape.POLYLINE: PolylineCoordinates,
    Shape.SKELETON: SkeletonCoordinates,
    Shape.BITMASK: BitmaskCoordinates,
}
