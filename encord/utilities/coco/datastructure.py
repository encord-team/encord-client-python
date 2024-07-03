import importlib.metadata as importlib_metadata
from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, NamedTuple, Optional, Union

# import pycocotools.mask as coco_mask_utils
from encord.objects.bitmask import (
    # BitmaskCoordinates,
    _mask_to_rle,
    _rle_to_mask,
    _rle_to_string,
    _string_to_rle,
    transpose_bytearray,
)
from encord.objects.coordinates import BitmaskCoordinates, BoundingBoxCoordinates, PointCoordinate, PolygonCoordinates
from encord.orm.base_dto import BaseDTO, Field, dto_validator

# try:
#     import pycocotools.mask as coco_mask_utils
#     from pydantic import BaseModel, RootModel, model_validator
# except ImportError:
#     raise ModuleNotFoundError(
#         "The optional dependency `pycocotools` must be installed to import coco projects. You can install it with `pip install encord[pycocotools]"
#     )

ImageID = int
CategoryID = int


@dataclass
class FrameIndex:
    data_hash: str
    frame: int = 0


class CocoInfoModel(BaseDTO):
    year: Optional[int] = None
    version: Optional[str] = None
    description: Optional[str] = None
    contributor: Optional[str] = None
    url: Optional[str] = None
    date_created: Optional[str] = None


class CocoLicenseModel(BaseDTO):
    id: int
    name: str
    url: str


class CocoImageModel(BaseDTO):
    id: ImageID
    width: int
    height: int
    file_name: Optional[str] = None
    license: Optional[int] = None
    flickr_url: Optional[str] = None
    coco_url: Optional[str] = None
    date_captured: Optional[datetime] = None


class CocoCategoryModel(BaseDTO):
    id: CategoryID
    name: str
    supercategory: Optional[str] = None


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


class CocoPolygon(BaseDTO):
    values: List[PointTuple]

    @dto_validator(mode="before")
    @classmethod
    def validate_polygon(cls, _value: Any) -> Any:
        if not (isinstance(_value, list) and len(_value) > 0):
            return None
        if not isinstance(_value[0], list):
            return None

        return {"values": [(_value[0][i], _value[0][i + 1]) for i in range(0, len(_value[0]), 2)]}

    def to_encord(self, img_w: int, img_h: int) -> PolygonCoordinates:
        return PolygonCoordinates(values=[PointCoordinate(x=p.x / img_w, y=p.y / img_h) for p in self.values])


class CocoRLE(BaseDTO):
    size: RLESize
    counts: str

    @dto_validator(mode="before")
    @classmethod
    def parse_rle(cls, _value: Any) -> Any:
        if not isinstance(_value, dict):
            # This is not RLE
            return None

        if isinstance(_value["counts"], list):
            mask = _rle_to_mask(_value["counts"])
            mask = transpose_bytearray(mask, shape=(_value["size"][1], _value["size"][0]))
            rle = {"size": _value["size"], "counts": _rle_to_string(_mask_to_rle(mask))}
            # return cls(size=_value["size"], counts=_rle_to_string(_value["counts"]))
        elif isinstance(_value["counts"], str):
            # return cls(size=_value["size"], counts=_value["counts"])
            # rle = {"size": _value["size"], _value["counts"]]}
            mask = _rle_to_mask(_string_to_rle(_value["counts"]), _value["size"][0] * _value["size"][1])
            mask = transpose_bytearray(mask, shape=(_value["size"][1], _value["size"][0]))
            rle_str = _rle_to_string(_mask_to_rle(mask))
            rle = {"size": _value["size"], "counts": rle_str}
        else:
            rle = _value
        return rle

    def to_encord(self) -> BitmaskCoordinates:
        encoded_bitmask = BitmaskCoordinates.EncodedBitmask(
            top=0, left=0, height=self.size.height, width=self.size.width, rle_string=self.counts
        )
        return BitmaskCoordinates(encoded_bitmask)
        # return BitmaskCoordinates(coco_mask_utils.decode(self.dict()).astype(bool))


class CocoAnnotationModel(BaseDTO):
    id: int
    image_id: ImageID
    category_id: int
    segmentation: Union[CocoPolygon, List[CocoPolygon], CocoRLE]
    area: float
    bbox: CocoBoundingBox
    iscrowd: bool


class CocoRootModel(BaseDTO):
    info: CocoInfoModel
    categories: List[CocoCategoryModel]
    images: List[CocoImageModel]
    annotations: List[CocoAnnotationModel]
    licenses: Optional[List[CocoLicenseModel]] = None
