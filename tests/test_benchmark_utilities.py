import pytest
from shapely.geometry import Point, Polygon, box

from encord.utilities.benchmark_utilities import calculate_jaccard_similarity, transform_object_dict_to_polygon


@pytest.fixture
def objects():
    p0 = {
        "shape": "polygon",
        "polygon": {
            "0": {"x": 1, "y": 0},
            "1": {"x": 2, "y": 1},
            "2": {"x": 1, "y": 2},
            "3": {"x": 0, "y": 1},
        },
    }
    p1 = {"shape": "bounding_box", "boundingBox": {"x": 1, "y": -1, "w": 1, "h": 2}}
    p2 = {
        "shape": "polygon",
        "polygon": {"0": {"x": 1, "y": 1}, "1": {"x": 2, "y": 1}, "2": {"x": 1, "y": 2}},
    }
    p3 = {
        "shape": "polygon",
        "polygon": {"0": {"x": 1, "y": 1}, "1": {"x": 2, "y": 1}, "2": {"x": 1, "y": 0}},
    }
    p4 = {
        "shape": "polygon",
        "polygon": {
            "0": {"x": 0.5, "y": 0},
            "1": {"x": 2, "y": 1.5},
            "2": {"x": 1.5, "y": 2},
            "3": {"x": 0, "y": 0.5},
        },
    }
    p5 = {"shape": "point", "point": {"0": {"x": 1, "y": 1}}}
    return [p0, p1, p2, p3, p4, p5]


def test_transform_object_dict_to_polygon(objects):
    p0 = Polygon([(1, 0), (2, 1), (1, 2), (0, 1)])  # rhombus
    p1 = box(1, -1, 2, 1)  # rectangle
    p2 = Polygon([(1, 1), (2, 1), (1, 2)])  # triangle
    p3 = Polygon([(1, 1), (2, 1), (1, 0)])  # triangle
    p4 = Polygon([(0.5, 0), (2, 1.5), (1.5, 2), (0, 0.5)])  # parallelogram
    p5 = Point(1, 1)  # point
    polygons = [p0, p1, p2, p3, p4, p5]
    pred_polygons = [transform_object_dict_to_polygon(obj) for obj in objects]
    assert len(polygons) == len(pred_polygons)
    for i in range(len(polygons)):
        assert polygons[i].equals(pred_polygons[i])


def test_calculate_jaccard_similarity(objects):
    # (intersection_area) / (first_polygon_area + second_polygon_area - intersection_area)
    assert calculate_jaccard_similarity(objects[0], objects[1]) == (1 / 2) / (4 / 2 + 2 - 1 / 2)
    assert calculate_jaccard_similarity(objects[0], objects[2]) == (1 / 2) / (4 / 2 + 1 / 2 - 1 / 2)
    assert calculate_jaccard_similarity(objects[0], objects[3]) == (1 / 2) / (4 / 2 + 1 / 2 - 1 / 2)
    assert calculate_jaccard_similarity(objects[0], objects[4]) == (2 * 1 * 0.5) / (4 / 2 + 2 * 1.5 * 0.5 - 2 * 1 * 0.5)
    assert calculate_jaccard_similarity(objects[1], objects[2]) == 0 / (2 + 1 / 2 - 0)
    assert calculate_jaccard_similarity(objects[1], objects[3]) == (1 / 2) / (2 + 1 / 2 - 1 / 2)
    assert calculate_jaccard_similarity(objects[1], objects[4]) == (0.5 * 0.5 / 2) / (2 + 2 * 1.5 * 0.5 - 0.5 * 0.5 / 2)
