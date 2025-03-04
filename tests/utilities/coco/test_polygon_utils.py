import numpy as np
import pytest

from encord.common.bitmask_operations import serialise_bitmask
from encord.objects.coordinates import PointCoordinate, PolygonCoordinates
from encord.utilities.coco.polygon_utils import find_contours, rle_to_polygons_coordinates


@pytest.fixture
def polygon_with_hole() -> np.ndarray:
    array = np.zeros((100, 100), dtype=np.uint8)
    # Draw outer square (50x50 white square)
    array[25:75, 25:75] = 255
    # Draw inner square (hole - 20x20 black square inside the white one)
    array[40:60, 40:60] = 0

    return array


@pytest.fixture
def two_disjoint_polygons() -> np.ndarray:
    array = np.zeros((100, 100), dtype=np.uint8)
    # Draw two 20x20 white squares
    array[10:30, 10:30] = 255
    array[40:60, 40:60] = 255

    return array


def test_find_contours_with_holes(polygon_with_hole: np.ndarray) -> None:
    polygons = find_contours(polygon_with_hole)
    assert len(polygons) == 1, "Should have one polygon"
    assert polygons == [
        # the hole is a bit "jagged" from the pixelisation, but it's correct.
        [[25, 25, 25, 74, 74, 74, 74, 25], [39, 40, 40, 39, 59, 39, 60, 40, 60, 59, 59, 60, 40, 60, 39, 59]]
    ]


def test_find_contours_multipolygons(two_disjoint_polygons: np.ndarray) -> None:
    polygons = find_contours(two_disjoint_polygons)
    assert len(polygons) == 2, "Should have two polygons"
    assert polygons == [[[40, 40, 40, 59, 59, 59, 59, 40]], [[10, 10, 10, 29, 29, 29, 29, 10]]]


def test_rle_to_polygons_coordinates(polygon_with_hole: np.ndarray) -> None:
    counts = serialise_bitmask(polygon_with_hole.tobytes())
    res = rle_to_polygons_coordinates(counts=counts, height=100, width=100)
    assert isinstance(res, PolygonCoordinates)
    assert res.polygons == [
        [
            [
                PointCoordinate(x=0.25, y=0.25),
                PointCoordinate(x=0.25, y=0.74),
                PointCoordinate(x=0.74, y=0.74),
                PointCoordinate(x=0.74, y=0.25),
            ],
            [
                PointCoordinate(x=0.39, y=0.4),
                PointCoordinate(x=0.4, y=0.39),
                PointCoordinate(x=0.59, y=0.39),
                PointCoordinate(x=0.6, y=0.4),
                PointCoordinate(x=0.6, y=0.59),
                PointCoordinate(x=0.59, y=0.6),
                PointCoordinate(x=0.4, y=0.6),
                PointCoordinate(x=0.39, y=0.59),
            ],
        ]
    ]
