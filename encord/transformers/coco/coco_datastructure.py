from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Iterable, List, Optional, Tuple


class SuperClass:
    def asdict(self) -> dict:
        pass


@dataclass
class CocoInfo:
    # TODO: extensibility??
    contributor: Optional[str]
    date_created: datetime.date
    url: str
    version: str  # TODO: figure this out
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
    #  TODO: does this depend on the format? Can this be extended?
    area: float
    bbox: CocoBbox
    category_id: int
    id_: int  # TODO: how is this translated to the json. => maybe a wrapper around asdict
    image_id: int
    iscrowd: int
    segmentation: List  # TODO: this is actually some union
    keypoints: Optional[List[int]] = None
    num_keypoints: Optional[int] = None
    track_id: Optional[int] = None
    encord_track_uuid: Optional[str] = None
    rotation: Optional[float] = None
    classifications: Optional[dict] = None
    manual_annotation: Optional[bool] = None


@dataclass
class Coco:
    info: CocoInfo
    licenses: List[dict]  # TODO:
    categories: List[CocoCategory]
    images: List[CocoImage]
    annotations: List[CocoAnnotation]


# TODO: inherit from some sort of serialiser class?


def as_dict_custom(data_class):
    # TODO: this does not work for deeply nested stuff
    res = asdict(data_class)
    add_id_value = None

    # The track_id and rotation stuff is a huge hack ... don't use this pattern in the future
    add_track_id = None
    add_encord_track_uuid = None
    add_rotation = None
    add_classifications = None
    add_manual_annotation = None
    for key, value in res.items():
        if key == "id_":
            add_id_value = value
        if key == "track_id":
            add_track_id = value
        if key == "encord_track_uuid":
            add_encord_track_uuid = value
        if key == "rotation":
            add_rotation = value
        if key == "classifications":
            add_classifications = value
        if key == "manual_annotation":
            add_manual_annotation = value

    if add_id_value is not None:
        res["id"] = add_id_value
    del res["id_"]

    attributes = {}

    if add_track_id is not None:
        attributes["track_id"] = add_track_id
    del res["track_id"]

    if add_encord_track_uuid is not None:
        attributes["encord_track_uuid"] = add_encord_track_uuid
    del res["encord_track_uuid"]

    if add_rotation is not None:
        attributes["rotation"] = add_rotation
    del res["rotation"]

    if add_classifications is not None:
        attributes["classifications"] = add_classifications
    del res["classifications"]

    if add_manual_annotation is not None:
        attributes["manual_annotation"] = add_manual_annotation
    del res["manual_annotation"]

    if attributes != {}:
        res["attributes"] = attributes

    return res
