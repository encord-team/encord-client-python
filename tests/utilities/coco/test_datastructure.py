import copy

import numpy as np

from encord.utilities.coco.datastructure import (
    CocoAnnotationModel,
    CocoBoundingBox,
    CocoPolygon,
    CocoRLE,
    CocoRootModel,
)
from tests.utilities.coco.data_test_datastructure import DATA_TEST_DATASTRUCTURE_COCO


def get_bbox_from_polygon(polygon: CocoPolygon) -> CocoBoundingBox:
    min_x = float("inf")
    min_y = float("inf")
    max_x = -float("inf")
    max_y = -float("inf")
    for poly in polygon.values:
        for point in poly:
            min_x = min(min_x, point.x)
            min_y = min(min_y, point.y)
            max_x = max(max_x, point.x)
            max_y = max(max_y, point.y)
    return CocoBoundingBox(x=min_x, y=min_y, w=max_x - min_x, h=max_y - min_y)


def polygon_area(polygon: CocoPolygon) -> float:
    area = 0.0
    for poly in polygon.values:
        for i in range(len(poly)):
            area += poly[i - 1].x * (poly[i].y - poly[i - 2].y)
    return abs(area / 2)


def test_coco_annotation_model_with_missing_segmentation_field() -> None:
    for ann in copy.deepcopy(DATA_TEST_DATASTRUCTURE_COCO)["annotations"]:
        ann.pop("segmentation")
        ann_model = CocoAnnotationModel.from_dict(ann)
        # Assert the generated segmentation is a single polygon with 4 points
        assert isinstance(ann_model.segmentation, CocoPolygon) and len(ann_model.segmentation.values[0]) == 4
        # Assert the bounding box containing the generated polygon is the same as the input bounding box
        containing_bbox = get_bbox_from_polygon(ann_model.segmentation)
        assert np.allclose(containing_bbox, ann_model.bbox)
        # Assert the area of the generated polygon is the same as the area of the input bounding box
        assert np.isclose(polygon_area(ann_model.segmentation), ann_model.bbox.w * ann_model.bbox.h)


def test_coco_model_label_validation() -> None:
    coco_model = CocoRootModel.from_dict(copy.deepcopy(DATA_TEST_DATASTRUCTURE_COCO))
    assert sum(isinstance(ann.segmentation, CocoRLE) for ann in coco_model.annotations) == 6
    assert sum(isinstance(ann.segmentation, CocoPolygon) for ann in coco_model.annotations) == 466
