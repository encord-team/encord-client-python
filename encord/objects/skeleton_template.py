from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Set, Type

from encord.objects.coordinates import SkeletonCoordinate, SkeletonCoordinates
from encord.orm.skeleton_template import SkeletonTemplate as SkeletonTemplateORM
from encord.orm.skeleton_template import SkeletonTemplateCoordinate


class SkeletonTemplate(SkeletonTemplateORM):
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
