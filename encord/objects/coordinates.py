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
from typing import Any, Dict, List, Optional, Type, TypedDict, Union, cast

from encord.exceptions import LabelRowError
from encord.objects.bitmask import BitmaskCoordinates
from encord.objects.common import Shape
from encord.objects.frames import Ranges
from encord.objects.html_node import HtmlRange
from encord.objects.types import (
    BaseFrameObject,
    BoundingBoxDict,
    BoundingBoxFrameCoordinatesDict,
    FrameObject,
    Point3DFrameCoordinatesDict,
    PointDict,
    PointDict3D,
    PointFrameCoordinatesDict,
    PolygonFrameCoordinatesDict,
    PolylineFrameCoordinatesDict,
    RotatableBoundingBoxDict,
    RotatableBoundingBoxFrameCoordinatesDict,
)
from encord.orm.analytics import CamelStrEnum
from encord.orm.base_dto import BaseDTO

logger = logging.getLogger(__name__)


class BoundingBoxDict(TypedDict):
    h: float
    w: float
    x: float
    y: float


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
    def from_dict(d: BoundingBoxFrameCoordinatesDict) -> BoundingBoxCoordinates:
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

    def to_dict(self) -> BoundingBoxDict:
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


class RotatableBoundingBoxDict(BoundingBoxDict):
    theta: float


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
    def from_dict(d: RotatableBoundingBoxFrameCoordinatesDict) -> RotatableBoundingBoxCoordinates:
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

    def to_dict(self) -> RotatableBoundingBoxDict:
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
class CuboidCoordinates:
    """Represents a cuboid.

    Attributes:
        position (tuple[float, float, float]): The (x, y, z) coordinates of the center of the cuboid in the 3D space.
        orientation (tuple[float, float, float]): The (alpha, beta, gamma) Euler angles of the cuboid, in radians.
        size (tuple[float, float, float]): The size of the cuboid along its (x, y, z) axes.
    """

    position: tuple[float, float, float]
    orientation: tuple[float, float, float]
    size: tuple[float, float, float]

    @staticmethod
    def from_dict(d: Dict) -> CuboidCoordinates:
        cuboid_dict = d["cuboid"]
        return CuboidCoordinates(
            position=cuboid_dict["position"],
            orientation=cuboid_dict["orientation"],
            size=cuboid_dict["size"],
        )

    def to_dict(self) -> Dict:
        return {
            "position": self.position,
            "orientation": self.orientation,
            "size": self.size,
        }


class PointDict(TypedDict):
    x: float
    y: float


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
    def from_dict(d: PointFrameCoordinatesDict) -> PointCoordinate:
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

    def to_dict(self) -> Dict[str, PointDict]:
        """Convert the PointCoordinate instance to a dictionary.

        Returns:
            dict: A dictionary representation of the point coordinate.
        """
        return {"0": {"x": self.x, "y": self.y}}


class PointDict3D(PointDict):
    z: float


@dataclass(frozen=True)
class PointCoordinate3D:
    """Represents a 3D point coordinate, where all coordinates are a percentage relative to the total image size.

    Attributes:
        x (float): The x-coordinate of the point.
        y (float): The y-coordinate of the point.
        z (float): The z-coordinate of the point.
    """

    x: float
    y: float
    z: float

    @staticmethod
    def from_dict(d: Point3DFrameCoordinatesDict) -> PointCoordinate3D:
        """Create a PointCoordinate3D instance from a dictionary.

        Args:
            d (dict): A dictionary containing point coordinate information.

        Returns:
            PointCoordinate3D: An instance of PointCoordinate3D.
        """
        first_item = d["point"]["0"]
        return PointCoordinate3D(x=first_item["x"], y=first_item["y"], z=first_item["z"])

    def to_dict(self) -> dict[str, PointDict3D]:
        """Convert the PointCoordinate instance to a dictionary.

        Returns:
            dict: A dictionary representation of the point coordinate.
        """
        return {"0": {"x": self.x, "y": self.y, "z": self.z}}


class PolygonCoordsToDict(str, Enum):
    single_polygon = "single_polygon"
    multiple_polygons = "multiple_polygons"


LegacyPolygonDict = Union[Dict[str, PointDict], list[PointDict]]
PolygonDict = List[List[List[float]]]


class PolygonCoordinates:
    """Represents polygon coordinates"""

    def __init__(
        self,
        values: Optional[List[PointCoordinate]] = None,
        polygons: Optional[List[List[List[PointCoordinate]]]] = None,
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
    def values(self) -> List[PointCoordinate]:
        return self._values

    @property
    def polygons(self) -> List[List[List[PointCoordinate]]]:
        return self._polygons

    @staticmethod
    def from_dict(d: PolygonFrameCoordinatesDict) -> "PolygonCoordinates":
        """Create a PolygonCoordinates instance from a dictionary.

        Supports both legacy format (single polygon with one contour) and the new complex format (multiple polygons and contours).

        Args:
        d (dict): Dictionary containing polygon coordinates information.

        Returns:
        PolygonCoordinates: A PolygonCoordinates instance.

        Examples:
        Legacy format (mapping of index -> point):
        ```json
        {
          "polygon": {
            "0": {"x": 12.3, "y": 45.6},
            "1": {"x": 78.9, "y": 12.3}
          }
        }
        ```

        Legacy format (list of points):
        ```json
        {
          "polygon": [
            {"x": 12.3, "y": 45.6},
            {"x": 78.9, "y": 12.3}
          ]
        }
        ```

        New format (polygons -> contours -> points):
        ```json
        {
          "polygons": [
            [
              [
                {"x": 12.3, "y": 45.6},
                {"x": 78.9, "y": 12.3}
              ]
            ]
          ]
        }
        ```
        """
        polygon_dict = d.get("polygon")
        values: List[PointCoordinate] = []

        if isinstance(polygon_dict, Dict):
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
        raw_polygons = d.get("polygons", [])
        if raw_polygons is not None:
            for polygon in raw_polygons:
                contours = [flat_to_pnt_coordinates(contour) for contour in polygon]
                polygons.append(contours)

        return PolygonCoordinates(values=values, polygons=polygons)

    @staticmethod
    def from_polygons_list(flat_polygons: List[List[List[float]]]) -> "PolygonCoordinates":
        polygons: List[List[List[PointCoordinate]]] = []
        for polygon in flat_polygons:
            contours: List[List[PointCoordinate]] = []
            for contour in polygon:
                contours.append(flat_to_pnt_coordinates(contour))
            polygons.append(contours)

        return PolygonCoordinates(polygons=polygons)

    def to_dict(
        self, kind: Union[PolygonCoordsToDict, str] = PolygonCoordsToDict.single_polygon
    ) -> Union[Dict, List[List[List[float]]]]:
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


def flat_to_pnt_coordinates(ring: List[float]) -> List[PointCoordinate]:
    return [PointCoordinate(x=ring[idx], y=ring[idx + 1]) for idx in range(0, len(ring), 2)]


def pnt_coordinates_to_flat(coordinates: List[PointCoordinate]) -> List[float]:
    return [coord for point in coordinates for coord in [point.x, point.y]]


PolylineDict = Union[Dict[str, PointDict], list[PointDict], Dict[str, PointDict3D], list[PointDict3D]]


@dataclass(frozen=True)
class PolylineCoordinates:
    """Represents polyline coordinates as a list of point coordinates.

    Attributes:
        values (Union[List[PointCoordinate], List[PointCoordinate3D]]): A list of (3D) PointCoordinate objects defining the polyline.
    """

    values: Union[List[PointCoordinate], List[PointCoordinate3D]]

    @staticmethod
    def from_dict(d: PolylineFrameCoordinatesDict) -> PolylineCoordinates:
        """Create a PolylineCoordinates instance from a dictionary.

        Args:
            d (dict): A dictionary containing polyline coordinates information.

        Returns:
            PolylineCoordinates: An instance of PolylineCoordinates.
        """
        polyline = d["polyline"]

        if isinstance(polyline, Dict):
            sorted_dict_value_tuples = sorted((int(key), value) for key, value in polyline.items())
            sorted_dict_values = [item[1] for item in sorted_dict_value_tuples]
        elif isinstance(polyline, list):
            sorted_dict_values = list(polyline)
        else:
            raise LabelRowError(f"Invalid format for polyline coordinates: {polyline}")

        all_2d = all("x" in pnt and "y" in pnt and "z" not in pnt for pnt in sorted_dict_values)
        all_3d = all("x" in pnt and "y" in pnt and "z" in pnt for pnt in sorted_dict_values)
        values: Union[List[PointCoordinate], List[PointCoordinate3D]] = []
        if all_3d:
            values_3d = cast(List[PointDict3D], sorted_dict_values)
            values = [PointCoordinate3D(x=value["x"], y=value["y"], z=value["z"]) for value in values_3d]
        elif all_2d:
            values = [PointCoordinate(x=value["x"], y=value["y"]) for value in sorted_dict_values]
        else:
            raise LabelRowError(f"Invalid point format in polyline coordinates: {sorted_dict_values}")

        return PolylineCoordinates(values=values)

    def to_dict(self) -> Dict:
        """Convert the PolylineCoordinates instance to a dictionary.

        Returns:
            dict: A dictionary representation of the polyline coordinates.
        """
        ret: Dict[str, Dict[str, float]] = {}
        for idx, value in enumerate(self.values):
            if isinstance(value, PointCoordinate3D):
                ret[str(idx)] = {"x": value.x, "y": value.y, "z": value.z}
            elif isinstance(value, PointCoordinate):
                ret[str(idx)] = {"x": value.x, "y": value.y}
        return ret


class Visibility(CamelStrEnum):
    """An enumeration to represent the visibility state of an item.

    Attributes:
        VISIBLE: The item is visible within the frame.
        INVISIBLE: The item is outside the frame and thus invisible.
        OCCLUDED: The item is within the frame but occluded by something else.
        SELF_OCCLUDED: The item is occluded by itself.
    """

    VISIBLE = auto()
    INVISIBLE = auto()
    OCCLUDED = auto()
    SELF_OCCLUDED = auto()


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
    PointCoordinate3D,
    PolygonCoordinates,
    PolylineCoordinates,
    SkeletonCoordinates,
    BitmaskCoordinates,
    CuboidCoordinates,
]

GeometricCoordinates = Union[
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
    Shape.POINT: [PointCoordinate, PointCoordinate3D],
    Shape.POLYGON: [PolygonCoordinates],
    Shape.POLYLINE: [PolylineCoordinates],
    Shape.SKELETON: [SkeletonCoordinates],
    Shape.BITMASK: [BitmaskCoordinates],
    Shape.CUBOID: [CuboidCoordinates],
    Shape.AUDIO: [AudioCoordinates],
    Shape.TEXT: [TextCoordinates, HtmlCoordinates],
}


def add_coordinates_to_frame_object_dict(
    coordinates: Coordinates,
    base_frame_object: BaseFrameObject,
    width: int,
    height: int,
) -> FrameObject:
    result: Dict[str, Any] = dict(base_frame_object)

    if isinstance(coordinates, BoundingBoxCoordinates):
        result["boundingBox"] = coordinates.to_dict()
        result["shape"] = Shape.BOUNDING_BOX.value
    elif isinstance(coordinates, RotatableBoundingBoxCoordinates):
        result["rotatableBoundingBox"] = coordinates.to_dict()
        result["shape"] = Shape.ROTATABLE_BOUNDING_BOX.value
    elif isinstance(coordinates, PolygonCoordinates):
        result["polygon"] = coordinates.to_dict()
        result["polygons"] = coordinates.to_dict(PolygonCoordsToDict.multiple_polygons)
        result["shape"] = Shape.POLYGON.value
    elif isinstance(coordinates, PolylineCoordinates):
        result["polyline"] = coordinates.to_dict()
        result["shape"] = Shape.POLYLINE.value
    elif isinstance(coordinates, (PointCoordinate, PointCoordinate3D)):
        result["point"] = coordinates.to_dict()
        result["shape"] = Shape.POINT.value
    elif isinstance(coordinates, BitmaskCoordinates):
        if not (height == coordinates._encoded_bitmask.height and width == coordinates._encoded_bitmask.width):
            raise ValueError("Bitmask dimensions don't match the media dimensions")
        result["bitmask"] = coordinates.to_dict()
        result["shape"] = Shape.BITMASK.value
    elif isinstance(coordinates, SkeletonCoordinates):
        result["skeleton"] = coordinates.to_dict()
        result["shape"] = Shape.SKELETON.value
    elif isinstance(coordinates, CuboidCoordinates):
        result["cuboid"] = coordinates.to_dict()
        result["shape"] = Shape.CUBOID.value
    else:
        raise NotImplementedError(f"adding coordinates for this type not yet implemented {type(coordinates)}")

    return cast(FrameObject, result)


def get_coordinates_from_frame_object_dict(frame_object_dict: FrameObject) -> Coordinates:
    if frame_object_dict["shape"] == Shape.BOUNDING_BOX:
        return BoundingBoxCoordinates.from_dict(frame_object_dict)
    elif frame_object_dict["shape"] == Shape.ROTATABLE_BOUNDING_BOX:
        return RotatableBoundingBoxCoordinates.from_dict(frame_object_dict)
    elif frame_object_dict["shape"] == Shape.POLYGON:
        return PolygonCoordinates.from_dict(frame_object_dict)
    elif frame_object_dict["shape"] == Shape.POINT:
        coords = frame_object_dict["point"]["0"]
        if "x" in coords and "y" in coords and "z" in coords:
            return PointCoordinate3D.from_dict(frame_object_dict)  # type: ignore
        elif "x" in coords and "y" in coords:
            return PointCoordinate.from_dict(frame_object_dict)  # type: ignore
        else:
            raise ValueError(f"Invalid point coordinates in {frame_object_dict}")
    elif frame_object_dict["shape"] == Shape.POLYLINE:
        return PolylineCoordinates.from_dict(frame_object_dict)
    elif "skeleton" in frame_object_dict:

        def _with_visibility_enum(point: dict):
            if point.get(Visibility.INVISIBLE.value):
                point["visibility"] = Visibility.INVISIBLE
            elif point.get(Visibility.OCCLUDED.value):
                point["visibility"] = Visibility.OCCLUDED
            elif point.get(Visibility.SELF_OCCLUDED.value):
                point["visibility"] = Visibility.SELF_OCCLUDED
            elif point.get(Visibility.VISIBLE.value):
                point["visibility"] = Visibility.VISIBLE
            return point

        values = [_with_visibility_enum(pnt) for pnt in frame_object_dict["skeleton"].values()]
        skeleton_frame_object_label = {
            "name": frame_object_dict["name"],
            "values": values,
        }
        return SkeletonCoordinates.from_dict(skeleton_frame_object_label)
    elif "bitmask" in frame_object_dict:
        return BitmaskCoordinates.from_dict(frame_object_dict)
    elif "cuboid" in frame_object_dict:
        return CuboidCoordinates.from_dict(frame_object_dict)
    else:
        raise NotImplementedError(f"Getting coordinates for `{frame_object_dict}` is not supported yet.")


def get_geometric_coordinates_from_frame_object_dict(
    frame_object_dict: FrameObject,
) -> GeometricCoordinates:
    coordinates = get_coordinates_from_frame_object_dict(frame_object_dict)
    if isinstance(coordinates, CuboidCoordinates):
        raise NotImplementedError("Cuboid is not a two dimensional coordinate.")

    # The cast is safe because we've excluded the non-geometric types.
    return cast(GeometricCoordinates, coordinates)
