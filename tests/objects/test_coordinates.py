import logging
from copy import copy

import pytest

from encord.exceptions import LabelRowError
from encord.objects import Shape
from encord.objects.coordinates import ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS, PointCoordinate, PolygonCoordinates


def test_acceptable_coordinates_for_ontology_items() -> None:
    all_mappings = copy(ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS)
    for shape in Shape:
        assert shape in all_mappings
        del all_mappings[shape]
    assert not all_mappings


def test_polygon_coordinates(caplog):
    c1 = PolygonCoordinates(values=[PointCoordinate(x=0, y=0), PointCoordinate(x=1, y=1)])
    assert len(c1.polygons) == 1  # 1 polygon
    assert len(c1.polygons[0]) == 1  # 1 ring
    assert c1.polygons[0][0] == [PointCoordinate(x=0, y=0), PointCoordinate(x=1, y=1)]

    c2 = PolygonCoordinates(
        polygons=[
            [[PointCoordinate(x=0, y=0), PointCoordinate(x=1, y=1)]],
            [[PointCoordinate(x=2, y=2), PointCoordinate(x=3, y=3)]],
        ]
    )
    assert len(c2.polygons) == 2  # 2 polygons
    assert c2.values == [
        PointCoordinate(x=0, y=0),
        PointCoordinate(x=1, y=1),
    ]  # only contains the first polygon, second is ignored

    # inconsistent values being provided should log a warning & set to polygons value
    caplog.set_level(logging.WARNING)  # Set the log level to capture warnings
    c3 = PolygonCoordinates(values=[PointCoordinate(x=0, y=0)], polygons=[[[PointCoordinate(x=1, y=1)]]])
    assert "`values` and `polygons` are not consistent, defaulting to polygons value" in caplog.text
    # Assert that the values are now equal based on polygons value
    assert c3.values == [PointCoordinate(x=1, y=1)]

    # Not providing either values or polygons should raise an error
    with pytest.raises(LabelRowError):
        PolygonCoordinates()


def test_polygon_coordinates_from_and_to_dict():
    c1 = PolygonCoordinates.from_dict({"polygon": [{"x": 0, "y": 0}, {"x": 1, "y": 1}]})
    assert c1.values == [PointCoordinate(x=0, y=0), PointCoordinate(x=1, y=1)]
    assert c1.polygons[0][0] == [PointCoordinate(x=0, y=0), PointCoordinate(x=1, y=1)]
    assert c1.to_dict() == {"0": {"x": 0, "y": 0}, "1": {"x": 1, "y": 1}}
    assert c1.to_dict("multiple_polygons") == [[[0, 0, 1, 1]]]

    c2 = PolygonCoordinates.from_dict({"polygons": [[[0, 0, 1, 1]], [[2, 2, 3, 3]]]})
    assert c2.values == [PointCoordinate(x=0, y=0), PointCoordinate(x=1, y=1)]
    assert len(c2.polygons) == 2
    assert c2.polygons[0][0] == [PointCoordinate(x=0, y=0), PointCoordinate(x=1, y=1)]
    assert c2.polygons[1][0] == [PointCoordinate(x=2, y=2), PointCoordinate(x=3, y=3)]
    assert c2.to_dict("multiple_polygons") == [[[0, 0, 1, 1]], [[2, 2, 3, 3]]]
    assert c1.to_dict() == {"0": {"x": 0, "y": 0}, "1": {"x": 1, "y": 1}}


def test_polygon_coordinates_from_polygons_list():
    c1 = PolygonCoordinates.from_polygons_list([[[0, 0, 1, 1, 2, 2]], [[3, 3, 4, 4, 5, 5]]])
    assert c1.polygons == [
        [[PointCoordinate(x=0, y=0), PointCoordinate(x=1, y=1), PointCoordinate(x=2, y=2)]],
        [[PointCoordinate(x=3, y=3), PointCoordinate(x=4, y=4), PointCoordinate(x=5, y=5)]],
    ]
