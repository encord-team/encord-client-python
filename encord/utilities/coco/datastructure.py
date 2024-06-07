import importlib.metadata as importlib_metadata
from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, NamedTuple, Optional, Union

from encord.objects.bitmask import BitmaskCoordinates
from encord.objects.coordinates import (
    BoundingBoxCoordinates,
    PointCoordinate,
    PolygonCoordinates,
)

try:
    import pycocotools.mask as coco_mask_utils
    from pydantic import BaseModel, RootModel, model_validator
except ImportError:
    raise ModuleNotFoundError(
        "The optional dependency `pycocotools` must be installed to import coco projects. You can install it with `pip install encord[pycocotools]"
    )


pydantic_version_str = importlib_metadata.version("pydantic")
pydantic_version = int(pydantic_version_str.split(".")[0])
if pydantic_version < 3:
    ModuleNotFoundError("To be able to import coco projects, you must have `pydantic>=2.0`")


ImageID = int
CategoryID = int


@dataclass
class FrameIndex:
    data_hash: str
    frame: int = 0


class CocoInfoModel(BaseModel):
    year: Optional[int]
    version: Optional[str]
    description: Optional[str]
    contributor: Optional[str]
    url: Optional[str]
    date_created: Optional[str]


class CocoLicenseModel(BaseModel):
    id: int
    name: str
    url: str


class CocoImageModel(BaseModel):
    id: ImageID
    width: int
    height: int
    file_name: Optional[str]
    license: Optional[int]
    flickr_url: Optional[str]
    coco_url: Optional[str]
    date_captured: datetime


class CocoCategoryModel(BaseModel):
    id: CategoryID
    name: str
    supercategory: Optional[str]


# ints in documentation but this gives more flexibility
class CocoBoundingBox(NamedTuple):
    x: float
    y: float
    w: float
    h: float

    def to_encord(self, img_w: int, img_h: int) -> BoundingBoxCoordinates:
        return BoundingBoxCoordinates(
            top_left_x=self.x / img_w,
            top_left_y=self.y / img_h,
            width=self.w / img_w,
            height=self.h / img_h,
        )


class RLESize(NamedTuple):
    height: int
    width: int


class PointTuple(NamedTuple):
    x: float
    y: float


class CocoPolygon(RootModel):
    root: List[PointTuple]

    @model_validator(mode="before")
    @classmethod
    def validate_polyton(cls, _value: Any) -> Any:
        if not (isinstance(_value, list) and len(_value) > 0):
            return _value
        if isinstance(_value[0], list):
            return

        return [[_value[i], _value[i + 1]] for i in range(0, len(_value), 2)]

    def to_encord(self, img_w: int, img_h: int) -> PolygonCoordinates:
        return PolygonCoordinates(values=[PointCoordinate(x=p.x / img_w, y=p.y / img_h) for p in self.root])


class CocoRLE(BaseModel):
    size: RLESize
    counts: bytes

    @model_validator(mode="before")
    @classmethod
    def parse_rle(cls, _value: Any) -> Any:
        if not isinstance(_value, dict):
            # This is not RLE
            return None

        h, w = _value["size"]
        if isinstance(_value, list):
            rles = coco_mask_utils.frPyObjects(_value, h, w)
            rle = coco_mask_utils.merge(rles)
        elif isinstance(_value["counts"], list):
            rle = coco_mask_utils.frPyObjects(_value, h, w)
        else:
            rle = _value
        return rle

    def to_encord(self) -> BitmaskCoordinates:
        return BitmaskCoordinates(coco_mask_utils.decode(self.dict()).astype(bool))


class CocoAnnotationModel(BaseModel):
    id: int
    image_id: ImageID
    category_id: int
    segmentation: Union[CocoPolygon, List[CocoPolygon], CocoRLE]
    area: float
    bbox: CocoBoundingBox
    iscrowd: bool


class CocoRootModel(BaseModel):
    info: CocoInfoModel
    categories: List[CocoCategoryModel]
    images: List[CocoImageModel]
    annotations: List[CocoAnnotationModel]
    licenses: List[CocoLicenseModel]
