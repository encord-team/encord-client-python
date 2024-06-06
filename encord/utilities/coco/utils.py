from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
from nptyping import NDArray
from pycocotools.mask import decode, frPyObjects, merge

from encord.utilities.coco.datastructure import CocoBbox


def annToRLE(ann: Dict[str,Any], h: int, w: int):
    """
    Convert annotation which can be polygons, uncompressed RLE to RLE.
    :return: binary mask (numpy 2D array)
    """
    segm = ann["segmentation"]
    if isinstance(segm, list):
        # polygon -- a single object might consist of multiple parts
        # we merge all parts into one mask rle code
        rles = frPyObjects(segm, h, w)
        rle = merge(rles)
    elif isinstance(segm["counts"], list):
        # uncompressed RLE
        rle = frPyObjects(segm, h, w)
    else:
        # rle
        rle = ann["segmentation"]
    return rle


def annToMask(ann, h:int, w: int):
    """
    Convert annotation which can be polygons, uncompressed RLE, or RLE to binary mask.
    :return: binary mask (numpy 2D array)
    """
    rle = annToRLE(ann, h, w)
    return decode(rle)

def parse_annotation(annotation, h: int, w: int) -> Union[list, NDArray]:
    segm = annotation["segmentation"]
    if isinstance(segm, list):
        # polygon
        return segm
    elif segm.get("counts") and isinstance(segm.get("counts"), list):
        # uncompressed RLE
        rle = frPyObjects(segm, h,w)
        return decode(rle)
    else:
        # raw rle
        rle = segm
        return decode(rle)


def crop_box_to_image_size(x: float, y: float, w: float, h: float, img_w: int, img_h: int) -> Tuple[int, int, int, int]:
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


def mask_to_polygon(mask: np.ndarray) -> Tuple[Optional[List[Any]], CocoBbox]:
    [x, y, w, h] = cv2.boundingRect(mask)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        # Valid polygons have >= 6 coordinates (3 points)
        if contour.size >= 6:
            return contour.squeeze(1).tolist(), CocoBbox(x, y, w, h)

    return None, CocoBbox(x, y, w, h)
