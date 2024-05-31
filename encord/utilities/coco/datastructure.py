from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Set, Tuple

from encord.objects.common import Shape

COCO_PERMANENT_ANNOTATIONS = [
    "id_",
    "image_id",
    "category_id",
    "segmentation",
    "area",
    "bbox",
    "iscrowd",
    "keypoints",
    "num_keypoints",
]
ImageID = int
CategoryID = int

class SuperClass:
    def asdict(self) -> dict:
        pass

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
class CocoAnnotation(SuperClass):
    #  DENIS: does this depend on the format? Can this be extended?
    area: float
    bbox: CocoBbox
    category_id: CategoryID
    id_: int  # DENIS: how is this translated to the json. => maybe a wrapper around asdict
    image_id: ImageID
    iscrowd: int
    segmentation: List  # DENIS: this is actually some union
    keypoints: Optional[List[int]] = None
    num_keypoints: Optional[int] = None
    track_id: Optional[int] = None
    encord_track_uuid: Optional[str] = None
    rotation: Optional[float] = None


@dataclass
class CocoResult(SuperClass):
    image_id: ImageID
    category_id: int
    score: float
    bbox: Optional[CocoBbox] = None
    segmentation: Optional[List] = None  # DENIS: this is actually some union]
    keypoints: Optional[List[int]] = None


@dataclass
class Coco:
    info: CocoInfo
    licenses: List[dict]  # TODO:
    categories: List[CocoCategory]
    images: List[CocoImage]
    annotations: List[CocoAnnotation]


@dataclass
class EncordCocoMetadata:
    image_id: ImageID
    image_url: str
    image_path: str
    image_title: str
    label_hash: str
    data_hash: str


@dataclass
class CocoCategoryInfo:
    shapes: Set[Shape] = field(default_factory=set)
    has_rotation: bool = False



def to_attributes_field(res: dict, include_null_annotations: bool = False) -> dict:
    res_tmp = {}
    for key, value in res.items():
        if value is None and not include_null_annotations:
            continue

        if key in COCO_PERMANENT_ANNOTATIONS:
            if key == "id_":
                res_tmp["id"] = value
            else:
                res_tmp[key] = value
        else:
            attr = res_tmp.setdefault("attributes", {})
            attr[key] = value
    return res_tmp
