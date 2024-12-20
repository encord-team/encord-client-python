from typing import Dict, Optional

from pydantic import Field

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
    skeleton: dict[str, SkeletonTemplateCoordinate]
    skeleton_edges: dict[str, dict[str, dict[str, str]]]  # start-end-color-hex
    feature_node_hash: Optional[str] = Field(default=None, alias="feature_node_hash")
    shape: Optional[str] = "skeleton"
