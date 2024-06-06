from typing import Any, Dict, List, Optional, Tuple, Union

from nptyping import NDArray
from pycocotools.mask import decode, frPyObjects


def parse_annotation(annotation, h: int, w: int) -> Union[list, NDArray]:
    segm = annotation["segmentation"]
    if isinstance(segm, list):
        # polygon
        return segm
    elif segm.get("counts") and isinstance(segm.get("counts"), list):
        # uncompressed RLE
        rle = frPyObjects(segm, h, w)
        return decode(rle)
    else:
        # raw rle
        rle = segm
        return decode(rle)


def crop_box_to_image_size(
    x: float, y: float, w: float, h: float, img_w: float, img_h: float
) -> Tuple[float, float, float, float]:
    if x > img_w:
        raise ValueError(f"x coordinate {x} of bounding box outside the image of width {img_w}")
    if y > img_h:
        raise ValueError(f"y coordinate {y} of bounding box outside the image of height {img_h}.")
    if x < 0:
        w += x
        x = 0
    if y < 0:
        h += y
        y = 0
    if x + w > img_w:
        w -= x + w - img_w
    if y + h > img_h:
        h -= y + h - img_h
    return x, y, w, h
