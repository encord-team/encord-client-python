from typing import Any, Dict, Optional

from encord.orm.base_dto import BaseDTO


class SkeletonTemplateCoordinate(BaseDTO):
    x: float
    y: float
    name: str
    color: Optional[str] = "#00000"
    value: Optional[str] = ""
    featureHash: Optional[str] = None


class SkeletonTemplate(BaseDTO):
    name: str
    width: float
    height: float
    skeleton: dict[str, SkeletonTemplateCoordinate]
    skeleton_edges: dict[str, dict[str, dict[str, str]]]  # start-end-color-hex
    feature_node_hash: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return super().to_dict(by_alias=False)