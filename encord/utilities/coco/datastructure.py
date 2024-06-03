from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Set, Tuple

from encord.objects.common import Shape

ImageID = int
CategoryID = int


@dataclass
class FrameIndex:
    label_hash: str
    frame: int = 0


@dataclass
class CocoInfo:
    # DENIS: extensibility??
    contributor: Optional[str]
    date_created: date
    url: str
    version: str  # DENIS: figure this out
    year: str
    description: str


@dataclass
class CocoCategory:
    supercategory: str
    id_: int
    name: str


@dataclass
class CocoImage:
    id_: int
    height: int
    width: int
    file_name: str
    coco_url: str
    flickr_url: str


CocoBbox = Tuple[float, float, float, float]
"""x, y, w, h"""


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


@dataclass
class CocoCategoryInfo:
    shapes: Set[Shape] = field(default_factory=set)
    has_rotation: bool = False
