from __future__ import annotations

from dataclasses import dataclass
from enum import Flag, auto
from typing import Any, Dict, List, Optional, Type, Union

from encord.objects.bitmask import BitmaskCoordinates
from encord.objects.common import Shape


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

        sorted_dict_value_tuples = sorted((int(key), value) for key, value in polygon_dict.items())
        sorted_dict_values = [item[1] for item in sorted_dict_value_tuples]

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

        sorted_dict_value_tuples = sorted((int(key), value) for key, value in polyline.items())
        sorted_dict_values = [item[1] for item in sorted_dict_value_tuples]

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


@dataclass(init=False)
class SkeletonCoordinate:
    x: float
    y: float

    # `name` and `color` can be removed as they are part of the ontology.
    # The frontend must first be aware of how to merge with ontology.
    name: str
    color: Optional[str] = "#00000"

    # `featureHash` and `value` seem to appear when visibility is
    # present. They might not have any meaning. Remove if confirmed that
    # Frontend does not need it.
    featureHash: Optional[str] = None
    value: Optional[str] = None

    def __init__(
        self,
        x: float,
        y: float,
        name: str,
        color: str = "#00000",
        featureHash: Optional[str] = None,
        value: Optional[str] = None,
    ) -> None:
        self.x = x
        self.y = y
        self.name = name
        self.color = color
        self.featureHash = featureHash if featureHash else ""
        self.value = value if value else name

    @staticmethod
    def from_dict(d: dict[str, Any]) -> SkeletonCoordinate:
        return SkeletonCoordinate(**d)

    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "name": self.name,
            "color": self.color,
            "value": self.value,
            "featureHash": self.featureHash,
        }


@dataclass(frozen=True)
class SkeletonCoordinates:
    values: List[SkeletonCoordinate]

    @staticmethod
    def from_dict(d: dict) -> SkeletonCoordinates:
        skeleton_dict = d["skeleton"]
        list_coordinates: List[SkeletonCoordinate] = []
        sorted_dict_value_tuples = sorted((int(key), value) for key, value in skeleton_dict.items())
        sorted_dict_values = [item[1] for item in sorted_dict_value_tuples]
        for coordinate in sorted_dict_values:
            skeleton_coordinate = SkeletonCoordinate(
                x=coordinate["x"],
                y=coordinate["y"],
                name=coordinate["name"],
                value=coordinate["value"],
                color=coordinate["color"],
                featureHash=coordinate["featureHash"],
            )
            list_coordinates.append(skeleton_coordinate)
        return SkeletonCoordinates(values=list_coordinates)

    def to_dict(self) -> dict:
        return {i: x.to_dict() for i, x in enumerate(self.values)}

@dataclass
class SkeletonInstance:
    values: List[SkeletonCoordinate]
    template: str

    @staticmethod
    def from_dict(d: dict, skeleton_template: str) -> SkeletonInstance:
        skeleton_coords = [SkeletonCoordinate(coord) for coord in d["skeleton"].values()]
        return SkeletonInstance(skeleton_coords, skeleton_template)

    def to_dict(self) -> dict:
        return {i: x.to_dict() for i, x in enumerate(self.values)}

Coordinates = Union[
    BoundingBoxCoordinates,
    RotatableBoundingBoxCoordinates,
    PointCoordinate,
    PolygonCoordinates,
    PolylineCoordinates,
    # SkeletonCoordinates,
    SkeletonInstance,
    BitmaskCoordinates,
]
ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS: Dict[Shape, Type[Coordinates]] = {
    Shape.BOUNDING_BOX: BoundingBoxCoordinates,
    Shape.ROTATABLE_BOUNDING_BOX: RotatableBoundingBoxCoordinates,
    Shape.POINT: PointCoordinate,
    Shape.POLYGON: PolygonCoordinates,
    Shape.POLYLINE: PolylineCoordinates,
    # Shape.SKELETON: SkeletonCoordinates,
    Shape.SKELETON: SkeletonInstance,
    Shape.BITMASK: BitmaskCoordinates,
}
