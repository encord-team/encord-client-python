from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Iterable, List, Optional, Tuple


class SuperClass:
    def asdict(self) -> dict:
        pass


@dataclass
class CocoInfo:
    # DENIS: extensibility??
    contributor: Optional[str]
    date_created: datetime.date
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


CocoBbox = Tuple[float, float, float, float]
"""x, y, w, h"""


@dataclass
class CocoAnnotation(SuperClass):
    #  DENIS: does this depend on the format? Can this be extended?
    area: float
    bbox: CocoBbox
    category_id: int
    id_: int  # DENIS: how is this translated to the json. => maybe a wrapper around asdict
    image_id: int
    iscrowd: int
    segmentation: List  # DENIS: this is actually some union
    keypoints: Optional[List[int]] = None
    num_keypoints: Optional[int] = None


@dataclass
class Coco:
    info: CocoInfo
    licenses: List[dict]  # TODO:
    categories: List[CocoCategory]
    images: List[CocoImage]
    annotations: List[CocoAnnotation]


# DENIS: inherit from some sort of serialiser class?


def as_dict_custom(data_class):
    # DENIS: this does not work for deeply nested stuff
    res = asdict(data_class)
    add_id_value = None
    for key, value in res.items():
        if key == "id_":
            add_id_value = value
    if add_id_value is not None:
        res["id"] = add_id_value
    del res["id_"]
    return res
