from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Set, Type

from encord.objects.coordinates import SkeletonCoordinate, SkeletonCoordinates


@dataclass(frozen=True)
class SkeletonTemplateCoordinate:
    x: float
    y: float
    name: str
    color: Optional[str] = "#00000"
    value: Optional[str] = ""
    featureHash: Optional[str] = None

    @staticmethod
    def from_dict(d: dict[str, Any]) -> SkeletonTemplateCoordinate:
        return SkeletonTemplateCoordinate(**d)

    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "name": self.name,
        }


@dataclass
class SkeletonTemplate:
    name: str
    width: float
    height: float
    skeleton: dict[str, SkeletonTemplateCoordinate]
    skeletonEdges: dict[str, dict[str, dict[str, str]]]  # start-end-color-hex
    feature_node_hash: str | None = None

    @property
    def required_vertices(self) -> Set[str]:
        return {coordinate.name for coordinate in self.skeleton.values()}

    def create_instance(self, provided_coordinates: List[SkeletonCoordinate]) -> SkeletonCoordinates:
        provided_vertices = {provided_coordinate.name for provided_coordinate in provided_coordinates}
        if provided_vertices != self.required_vertices:
            difference = provided_vertices.symmetric_difference(self.required_vertices)
            raise ValueError(f"Provided vertices does not match the required vertices, difference is {difference}")
        aligned_coordinates = []
        for coord in provided_coordinates:
            partner = [x for x in self.skeleton.values() if x.name == coord.name][0]
            aligned_coordinate = SkeletonCoordinate(
                x=coord.x, y=coord.y, name=coord.name, featureHash=partner.featureHash
            )
            aligned_coordinates.append(aligned_coordinate)
        return SkeletonCoordinates(values=aligned_coordinates, template=self.name)

    @staticmethod
    def from_dict(d: dict) -> SkeletonTemplate:
        skeleton_coordinates = {
            str(i): SkeletonTemplateCoordinate.from_dict(coord) for (i, coord) in d["skeleton"].items()
        }
        return SkeletonTemplate(
            name=d["name"],
            width=d["width"],
            height=d["height"],
            skeleton=skeleton_coordinates,
            skeletonEdges=d["skeletonEdges"],
            feature_node_hash=d.get("feature_node_hash"),
        )

    def to_dict(self) -> dict:
        serialise_skeleton = {idx: coord.to_dict() for (idx, coord) in self.skeleton.items()}
        return {
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "skeleton": serialise_skeleton,
            "skeletonEdges": self.skeletonEdges,
            "feature_node_hash": self.feature_node_hash,
        }
