from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Set, Type

from encord.objects.coordinates import SkeletonCoordinate, SkeletonCoordinates  # SkeletonInstance
from encord.orm.base_dto import BaseDTO


@dataclass
class SkeletonInstance:
    values: List[SkeletonCoordinate]
    template: SkeletonTemplate

    @staticmethod
    def from_dict(d: dict, skeleton_template: SkeletonTemplate) -> SkeletonInstance:
        skeleton_coords = [SkeletonCoordinate(coord) for coord in d["skeleton"].values()]
        return SkeletonInstance(skeleton_coords, skeleton_template)

    def to_dict(self) -> dict:
        return {i: x.to_dict() for i, x in enumerate(self.values)}

class SkeletonTemplate(BaseDTO):
    name: str
    width: float
    height: float
    skeleton: dict[str, SkeletonCoordinate]
    skeletonEdges: dict[str, dict[str, dict[str,str]]] # start-end-color-hex
    feature_node_hash: str | None = None

    @property
    def required_vertices(self) -> Set[str]:
        return {coordinate.name for coordinate in self.skeleton.values()}

    def create_instance(self, provided_coordinates: List[SkeletonCoordinate]) -> SkeletonCoordinates: # SkeletonInstance:
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
        return SkeletonCoordinates(values=aligned_coordinates)

    def to_dict(self) -> dict:
        serialise_skeleton = {idx: coord.to_dict() for (idx, coord) in self.skeleton.items()}
        return {"name": self.name, "width": self.width, "height": self.height, "skeleton": serialise_skeleton, "skeletonEdges" : self.skeletonEdges, "feature_node_hash": self.feature_node_hash}
