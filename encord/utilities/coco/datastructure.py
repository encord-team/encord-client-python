from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, NamedTuple, Optional, Union

from encord.objects.bitmask import (
    _mask_to_rle,
    _rle_to_mask,
    _rle_to_string,
    _string_to_rle,
    transpose_bytearray,
)
from encord.objects.coordinates import BitmaskCoordinates, BoundingBoxCoordinates, PointCoordinate, PolygonCoordinates
from encord.orm.base_dto import BaseDTO, dto_validator

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
            raise ValueError

        # Note: It's essential to transpose the input and output coordinates when using pycocotools' functions,
        # in order to address the distinction between treating masks as C-contiguous (row-major order, Encord's
        # implementation) versus pycocotools' expectation of Fortran-contiguous (column-major order, COCO's API
        # implementation) data.

        if isinstance(_value["counts"], list):
            mask = _rle_to_mask(_value["counts"], _value["size"][0] * _value["size"][1])
            mask = transpose_bytearray(mask, shape=(_value["size"][1], _value["size"][0]))
            rle = {"size": _value["size"], "counts": _rle_to_string(_mask_to_rle(mask))}
        elif isinstance(_value["counts"], str):
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


class CocoAnnotationModel(BaseDTO):
    @dto_validator(mode="before")
    def polygon_validator(cls, _value):
        segm = _value.get("segmentation")
        if segm is None:
            # Generate a polygon from the existing bounding box
            bbox = CocoBoundingBox(*_value["bbox"])
            coords = [
                (bbox.x, bbox.y),
                (bbox.x, bbox.y + bbox.h),
                (bbox.x + bbox.w, bbox.y + bbox.h),
                (bbox.x + bbox.w, bbox.y),
            ]
            _value["segmentation"] = CocoPolygon.from_dict({"values": coords})
        elif isinstance(segm, list) and len(segm) > 0 and isinstance(segm[0], list):
            coords = [(segm[0][i], segm[0][i + 1]) for i in range(0, len(segm[0]), 2)]
            poly = CocoPolygon.from_dict({"values": coords})
            _value["segmentation"] = poly
        elif isinstance(segm, dict) and "counts" in segm:
            rle = CocoRLE.from_dict(segm)
            _value["segmentation"] = rle
        return _value

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
