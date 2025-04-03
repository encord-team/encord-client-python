"""---
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

import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Type, Union

from encord.exceptions import LabelRowError
from encord.objects.bitmask import BitmaskCoordinates
from encord.objects.common import Shape
from encord.objects.frames import Ranges
from encord.objects.html_node import HtmlRange
from encord.orm.analytics import CamelStrEnum
from encord.orm.base_dto import BaseDTO

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BoundingBoxCoordinates:
    """Represents bounding box coordinates, where all values are percentages relative to the total image size.

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
        """Create a BoundingBoxCoordinates instance from a dictionary.

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
        """Convert the BoundingBoxCoordinates instance to a dictionary.

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
    """Represents rotatable bounding box coordinates, where all values are percentages relative to the total image size.

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
        """Create a RotatableBoundingBoxCoordinates instance from a dictionary.

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
        """Convert the RotatableBoundingBoxCoordinates instance to a dictionary.

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
    """Represents a point coordinate, where all coordinates are a percentage relative to the total image size.

    Attributes:
        x (float): The x-coordinate of the point.
        y (float): The y-coordinate of the point.
    """

    x: float
    y: float

    @staticmethod
    def from_dict(d: dict) -> PointCoordinate:
        """Create a PointCoordinate instance from a dictionary.

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
        """Convert the PointCoordinate instance to a dictionary.

        Returns:
            dict: A dictionary representation of the point coordinate.
        """
        return {"0": {"x": self.x, "y": self.y}}


class PolygonCoordsToDict(str, Enum):
    single_polygon = "single_polygon"
    multiple_polygons = "multiple_polygons"


class PolygonCoordinates:
    """Represents polygon coordinates"""

    def __init__(
        self, values: list[PointCoordinate] | None = None, polygons: list[list[list[PointCoordinate]]] | None = None
    ):
        """
        Args:
            values (List[PointCoordinate]): A list of PointCoordinate objects defining the polygon.
            polygons (List[List[List[PointCoordinate]]]): A list of polygons, where each polygon is a list of contours, where each contour is a list of points.
        """
        if not values and not polygons:
            raise LabelRowError("Either `values` or `polygons` must be provided")
        elif values and not polygons:
            self._values = values
            self._polygons = [[list(values)]]
        elif polygons and not values:
            self._polygons = polygons
            self._values = [point for point in self._polygons[0][0]]
        elif polygons and values:
            if polygons[0][0] != values:
                self._polygons = polygons
                self._values = [point for point in self._polygons[0][0]]  # We default to polygons values
                logger.warning("`values` and `polygons` are not consistent, defaulting to polygons value")
            else:
                self._values = values
                self._polygons = polygons

    @property
    def values(self) -> list[PointCoordinate]:
        return self._values

    @property
    def polygons(self) -> list[list[list[PointCoordinate]]]:
        return self._polygons

    @staticmethod
    def from_dict(d: dict) -> "PolygonCoordinates":
        """Create a PolygonCoordinates instance from a dictionary.

        Supports both legacy format (single polygon with one contour) and new complex format.

        Args:
            d (dict): A dictionary containing polygon coordinates information.
                Legacy format: {"polygon": {str(idx): {"x": x, "y": y}} or {"polygon": [{"x": x, "y": y}]}
                New format: {"polygons": [[[{"x": x, "y": y}]]]}

        Returns:
            PolygonCoordinates: An instance of PolygonCoordinates.
        """
        polygon_dict = d.get("polygon")
        values: List[PointCoordinate] = []

        if isinstance(polygon_dict, dict):
            sorted_dict_value_tuples = sorted((int(key), value) for key, value in polygon_dict.items())
            sorted_dict_values = [item[1] for item in sorted_dict_value_tuples]
        elif isinstance(polygon_dict, list):
            sorted_dict_values = list(polygon_dict)
        elif not polygon_dict:  # Empty dict case
            sorted_dict_values = []
        else:
            raise LabelRowError(f"Invalid format for polygon coordinates: {polygon_dict}")

        for value in sorted_dict_values:
            point_coordinate = PointCoordinate(
                x=value["x"],
                y=value["y"],
            )
            values.append(point_coordinate)

        # Parse new format if present
        polygons = []
        for polygon in d.get("polygons", []):
            contours = [flat_to_pnt_coordinates(contour) for contour in polygon]
            polygons.append(contours)

        return PolygonCoordinates(values=values, polygons=polygons)

    @staticmethod
    def from_polygons_list(flat_polygons: list[list[list[float]]]) -> "PolygonCoordinates":
        polygons: list[list[list[PointCoordinate]]] = []
        for polygon in flat_polygons:
            contours: list[list[PointCoordinate]] = []
            for contour in polygon:
                contours.append(flat_to_pnt_coordinates(contour))
            polygons.append(contours)

        return PolygonCoordinates(polygons=polygons)

    def to_dict(
        self, kind: PolygonCoordsToDict | str = PolygonCoordsToDict.single_polygon
    ) -> dict | list[list[list[float]]]:
        """Convert the PolygonCoordinates instance to a dictionary.

        Returns:
            dict: A dictionary representation of the polygon coordinates.
        """
        if kind == PolygonCoordsToDict.single_polygon:
            return {str(idx): {"x": value.x, "y": value.y} for idx, value in enumerate(self._values)}
        elif kind == PolygonCoordsToDict.multiple_polygons:
            return [[pnt_coordinates_to_flat(contour) for contour in polygon] for polygon in self._polygons]
        else:
            raise LabelRowError(f"Invalid argument: {kind}")


def flat_to_pnt_coordinates(ring: list[float]) -> list[PointCoordinate]:
    return [PointCoordinate(x=ring[idx], y=ring[idx + 1]) for idx in range(0, len(ring), 2)]


def pnt_coordinates_to_flat(coordinates: list[PointCoordinate]) -> list[float]:
    return [coord for point in coordinates for coord in [point.x, point.y]]


@dataclass(frozen=True)
class PolylineCoordinates:
    """Represents polyline coordinates as a list of point coordinates.

    Attributes:
        values (List[PointCoordinate]): A list of PointCoordinate objects defining the polyline.
    """

    values: List[PointCoordinate]

    @staticmethod
    def from_dict(d: dict) -> PolylineCoordinates:
        """Create a PolylineCoordinates instance from a dictionary.

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
        """Convert the PolylineCoordinates instance to a dictionary.

        Returns:
            dict: A dictionary representation of the polyline coordinates.
        """
        return {str(idx): {"x": value.x, "y": value.y} for idx, value in enumerate(self.values)}


class Visibility(CamelStrEnum):
    """An enumeration to represent the visibility state of an item.

    Attributes:
        VISIBLE: The item is visible within the frame.
        INVISIBLE: The item is outside the frame and thus invisible.
        OCCLUDED: The item is within the frame but occluded by something else.
    """

    VISIBLE = auto()
    INVISIBLE = auto()
    OCCLUDED = auto()


class SkeletonCoordinate(BaseDTO):
    """Represents a coordinate for a skeleton structure in an image.

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
    """Represents a collection of skeleton coordinates.

    Attributes:
        values (List[SkeletonCoordinate]): A list of SkeletonCoordinate objects.
        name (str): The name of the skeleton structure.
    """

    values: List[SkeletonCoordinate]
    name: str

    def to_dict(self, by_alias=True, exclude_none=True) -> Dict[str, Any]:
        """Convert the SkeletonCoordinates instance to a dictionary.

        Args:
            by_alias (bool): Whether to use alias for the field names.
            exclude_none (bool): Whether to exclude fields with None values.

        Returns:
            Dict[str, Any]: A dictionary representation of the skeleton coordinates.
        """
        return {str(i): x.to_dict() for i, x in enumerate(self.values)}


class AudioCoordinates(BaseDTO):
    """Represents coordinates for an audio file

    Attributes:
        range (Ranges): Ranges in milliseconds for audio files
    """

    range: Ranges

    def __post_init__(self):
        if len(self.range) == 0:
            raise ValueError("Range list must contain at least one range.")


class TextCoordinates(BaseDTO):
    """Represents coordinates for a text file

    Attributes:
        range (Ranges): Ranges of chars for simple text files
    """

    range: Ranges


class HtmlCoordinates(BaseDTO):
    """Represents coordinates for a html file

    Attributes:
        range (List[HtmlRange]): A list of HtmlRange objects
    """

    range: List[HtmlRange]


NON_GEOMETRIC_COORDINATES = {AudioCoordinates, TextCoordinates, HtmlCoordinates}


Coordinates = Union[
    AudioCoordinates,
    TextCoordinates,
    HtmlCoordinates,
    BoundingBoxCoordinates,
    RotatableBoundingBoxCoordinates,
    PointCoordinate,
    PolygonCoordinates,
    PolylineCoordinates,
    SkeletonCoordinates,
    BitmaskCoordinates,
]

ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS: Dict[Shape, List[Type[Coordinates]]] = {
    Shape.BOUNDING_BOX: [BoundingBoxCoordinates],
    Shape.ROTATABLE_BOUNDING_BOX: [RotatableBoundingBoxCoordinates],
    Shape.POINT: [PointCoordinate],
    Shape.POLYGON: [PolygonCoordinates],
    Shape.POLYLINE: [PolylineCoordinates],
    Shape.SKELETON: [SkeletonCoordinates],
    Shape.BITMASK: [BitmaskCoordinates],
    Shape.AUDIO: [AudioCoordinates],
    Shape.TEXT: [TextCoordinates, HtmlCoordinates],
}
