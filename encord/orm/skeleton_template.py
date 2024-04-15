from typing import Any, Dict, List, Optional, Set, Union

from encord.objects.coordinates import SkeletonCoordinate, SkeletonCoordinates
from encord.orm.base_dto import BaseDTO


class SkeletonTemplateCoordinate(BaseDTO):
    x: float
    y: float
    name: str
    color: Optional[str] = "#00000"
    value: Optional[str] = ""
    feature_hash: Optional[str] = None


class SkeletonTemplate(BaseDTO):
    name: str
    width: float
    height: float
    skeleton: Dict[str, SkeletonTemplateCoordinate]
    skeleton_edges: Dict[str, Dict[str, Dict[str, str]]]  # start-end-color-hex
    feature_node_hash: Optional[str] = None
    shape: Optional[str] = "skeleton"

    @classmethod
    def from_dict(cls, d: Dict[str, Any]):
        coords = {key: SkeletonTemplateCoordinate.from_dict(val) for key, val in d["skeleton"].items()}
        return cls(
            name=d["name"],
            width=d["width"],
            height=d["height"],
            skeleton=coords,
            skeleton_edges=d["skeletonEdges"],
            shape=d["shape"],
            feature_node_hash=d["feature_node_hash"],
        )

    def to_dict(self, by_alias=True, exclude_none=True) -> Dict[str, Any]:
        dict_skeleton = {key: value.to_dict() for key, value in self.skeleton.items()}
        return {
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "skeleton": dict_skeleton,
            "skeletonEdges": self.skeleton_edges,
            "feature_node_hash": self.feature_node_hash,
            "shape": self.shape,
        }
