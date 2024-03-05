from __future__ import annotations

from dataclasses import dataclass
from typing import List, Set, Type

from encord.objects.coordinates import SkeletonCoordinate
from encord.orm.base_dto import BaseDTO


@dataclass
class SkeletonInstance:
    values: List[SkeletonCoordinate]
    template: SkeletonTemplate

    def to_dict(self) -> dict:
        return {i: x.to_dict() for i, x in enumerate(self.values)}


class SkeletonTemplate(BaseDTO):
    name: str
    width: float
    height: float
    skeleton: dict[str, SkeletonCoordinate]
    skeletonEdges: dict[str, dict[str, str]]
    feature_node_hash: str

    @property
    def required_vertices(self) -> Set[str]:
        return {coordinate.name for coordinate in self.skeleton.values()}

    def create_instance(self, provided_coordinates: dict[str:SkeletonCoordinate]) -> SkeletonInstance:
        provided_vertices = {provided_coordinate.name for provided_coordinate in provided_coordinates.values()}
        if provided_vertices != self.required_vertices:
            difference = provided_vertices.symmetric_difference(self.required_vertices)
            raise ValueError(f"Provided vertices does not match the required vertices, difference is {difference}")
        sorted_dict_value_tuples = sorted((int(key), value) for key, value in provided_coordinates.items())
        sorted_dict_values = [item[1] for item in sorted_dict_value_tuples]
        return SkeletonInstance(values=sorted_dict_values, template=self)
