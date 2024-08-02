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
    """
    Represents bounding box coordinates, where all values are percentages relative to the total image size.

    Attributes:
        height (float): The height of the bounding box.
        width (float): The width of the bounding box.
        top_left_x (float): The x-coordinate of the top-left corner.
        top_left_y (float): The y-coordinate of the top-left corner.
    """

    height: float
    width: float
    top_left_x: float
    top_left_y: float

    @staticmethod
    def from_dict(d: dict) -> BoundingBoxCoordinates:
        """
        Create a BoundingBoxCoordinates instance from a dictionary.

        Args:
            d (dict): A dictionary containing bounding box information.

        Returns:
            BoundingBoxCoordinates: An instance of BoundingBoxCoordinates.
        """
        bounding_box_dict = d["boundingBox"]
        return BoundingBoxCoordinates(
            height=bounding_box_dict["h"],
            width=bounding_box_dict["w"],
            top_left_x=bounding_box_dict["x"],
            top_left_y=bounding_box_dict["y"],
        )

    def to_dict(self) -> dict:
        """
        Convert the BoundingBoxCoordinates instance to a dictionary.

        Returns:
            dict: A dictionary representation of the bounding box coordinates.
        """
        return {
            "h": self.height,
            "w": self.width,
            "x": self.top_left_x,
            "y": self.top_left_y,
        }


@dataclass(frozen=True)
class RotatableBoundingBoxCoordinates:
    """
    Represents rotatable bounding box coordinates, where all values are percentages relative to the total image size.

    Attributes:
        height (float): The height of the bounding box.
        width (float): The width of the bounding box.
        top_left_x (float): The x-coordinate of the top-left corner.
        top_left_y (float): The y-coordinate of the top-left corner.
        theta (float): The angle of rotation originating at the center of the box.
    """

    height: float
    width: float
    top_left_x: float
    top_left_y: float
    theta: float  # angle of rotation originating at center of box

    @staticmethod
    def from_dict(d: dict) -> RotatableBoundingBoxCoordinates:
        """
        Create a RotatableBoundingBoxCoordinates instance from a dictionary.

        Args:
            d (dict): A dictionary containing rotatable bounding box information.

        Returns:
            RotatableBoundingBoxCoordinates: An instance of RotatableBoundingBoxCoordinates.
        """
        rotatable_bounding_box_dict = d["rotatableBoundingBox"]
        return RotatableBoundingBoxCoordinates(
            height=rotatable_bounding_box_dict["h"],
            width=rotatable_bounding_box_dict["w"],
            top_left_x=rotatable_bounding_box_dict["x"],
            top_left_y=rotatable_bounding_box_dict["y"],
            theta=rotatable_bounding_box_dict["theta"],
        )

    def to_dict(self) -> dict:
        """
        Convert the RotatableBoundingBoxCoordinates instance to a dictionary.

        Returns:
            dict: A dictionary representation of the rotatable bounding box coordinates.
        """
        return {
            "h": self.height,
            "w": self.width,
            "x": self.top_left_x,
            "y": self.top_left_y,
            "theta": self.theta,
        }


@dataclass(frozen=True)
class PointCoordinate:
    """
    Represents a point coordinate, where all coordinates are a percentage relative to the total image size.

    Attributes:
        x (float): The x-coordinate of the point.
        y (float): The y-coordinate of the point.
    """

    x: float
    y: float

    @staticmethod
    def from_dict(d: dict) -> PointCoordinate:
        """
        Create a PointCoordinate instance from a dictionary.

        Args:
            d (dict): A dictionary containing point coordinate information.

        Returns:
            PointCoordinate: An instance of PointCoordinate.
        """
        first_item = d["point"]["0"]
        return PointCoordinate(
            x=first_item["x"],
            y=first_item["y"],
        )

    def to_dict(self) -> dict:
        """
        Convert the PointCoordinate instance to a dictionary.

        Returns:
            dict: A dictionary representation of the point coordinate.
        """
        return {"0": {"x": self.x, "y": self.y}}


@dataclass(frozen=True)
class PolygonCoordinates:
    """
    Represents polygon coordinates as a list of point coordinates.

    Attributes:
        values (List[PointCoordinate]): A list of PointCoordinate objects defining the polygon.
    """

    values: List[PointCoordinate]

    @staticmethod
    def from_dict(d: dict) -> PolygonCoordinates:
        """
        Create a PolygonCoordinates instance from a dictionary.

        Args:
            d (dict): A dictionary containing polygon coordinates information.

        Returns:
            PolygonCoordinates: An instance of PolygonCoordinates.
        """
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
        """
        Convert the PolygonCoordinates instance to a dictionary.

        Returns:
            dict: A dictionary representation of the polygon coordinates.
        """
        return {str(idx): {"x": value.x, "y": value.y} for idx, value in enumerate(self.values)}


@dataclass(frozen=True)
class PolylineCoordinates:
    """
    Represents polyline coordinates as a list of point coordinates.

    Attributes:
        values (List[PointCoordinate]): A list of PointCoordinate objects defining the polyline.
    """

    values: List[PointCoordinate]

    @staticmethod
    def from_dict(d: dict) -> PolylineCoordinates:
        """
        Create a PolylineCoordinates instance from a dictionary.

        Args:
            d (dict): A dictionary containing polyline coordinates information.

        Returns:
            PolylineCoordinates: An instance of PolylineCoordinates.
        """
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
        """
        Convert the PolylineCoordinates instance to a dictionary.

        Returns:
            dict: A dictionary representation of the polyline coordinates.
        """
        return {str(idx): {"x": value.x, "y": value.y} for idx, value in enumerate(self.values)}


class Visibility(Flag):
    """
    An enumeration to represent the visibility state of an item.

    Attributes:
        VISIBLE: The item is visible within the frame.
        INVISIBLE: The item is outside the frame and thus invisible.
        OCCLUDED: The item is within the frame but occluded by something else.
    """

    VISIBLE = auto()
    INVISIBLE = auto()
    OCCLUDED = auto()


class SkeletonCoordinate(BaseDTO):
    """
    Represents a coordinate for a skeleton structure in an image.

    Attributes:
        x (float): The x-coordinate of the skeleton point.
        y (float): The y-coordinate of the skeleton point.
        name (str): The name of the skeleton point.
        color (Optional[str]): The color associated with the skeleton point.
        feature_hash (Optional[str]): A unique hash for the feature.
        value (Optional[str]): An optional value associated with the skeleton point.
        visibility (Optional[Visibility]): The visibility state of the skeleton point.
    """

    x: float
    y: float
    name: str
    color: Optional[str] = None
    feature_hash: Optional[str] = None
    value: Optional[str] = None

    visibility: Optional[Visibility] = None


class SkeletonCoordinates(BaseDTO):
    """
    Represents a collection of skeleton coordinates.

    Attributes:
        values (List[SkeletonCoordinate]): A list of SkeletonCoordinate objects.
        name (str): The name of the skeleton structure.
    """

    values: List[SkeletonCoordinate]
    name: str

    def to_dict(self, by_alias=True, exclude_none=True) -> Dict[str, Any]:
        """
        Convert the SkeletonCoordinates instance to a dictionary.

        Args:
            by_alias (bool): Whether to use alias for the field names.
            exclude_none (bool): Whether to exclude fields with None values.

        Returns:
            Dict[str, Any]: A dictionary representation of the skeleton coordinates.
        """
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
