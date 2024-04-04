from typing import Any, Dict, Optional, Union

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
    feature_node_hash: Union[str, None] = None

    def to_dict(self, by_alias=True, exclude_none=True) -> Dict[str, Any]:
        assert by_alias and exclude_none
        return super().to_dict(by_alias=False)
