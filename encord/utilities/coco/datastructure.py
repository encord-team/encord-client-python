from dataclasses import dataclass, field
from typing import List, NamedTuple, Optional

ImageID = int
CategoryID = int


@dataclass
class FrameIndex:
    data_hash: str
    frame: int = 0


class CocoBbox(NamedTuple):
    x: float
    y: float
    w: float
    h: float



@dataclass
class CocoAnnotation:
    area: float
    bbox: CocoBbox
    category_id: CategoryID
    id_: int
    image_id: ImageID
    iscrowd: int
    segmentation: List
    keypoints: Optional[List[int]] = None
    num_keypoints: Optional[int] = None
    track_id: Optional[int] = None
    encord_track_uuid: Optional[str] = None
    rotation: Optional[float] = None
