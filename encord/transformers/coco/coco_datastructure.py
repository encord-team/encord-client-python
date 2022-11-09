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
    track_id: Optional[str] = None
    rotation: Optional[float] = None


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

    # The track_id and rotation stuff is a huge hack ... don't use this pattern in the future
    add_track_id = None
    add_rotation = None
    for key, value in res.items():
        if key == "id_":
            add_id_value = value
        if key == "track_id":
            add_track_id = value
        if key == "rotation":
            add_rotation = value

    if add_id_value is not None:
        res["id"] = add_id_value
    del res["id_"]

    if add_track_id is not None or add_rotation is not None:
        res["attributes"] = {}

    if add_track_id is not None:
        res["attributes"]["track_id"] = add_track_id
    del res["track_id"]

    if add_rotation is not None:
        res["attributes"]["rotation"] = add_rotation
    del res["rotation"]

    return res