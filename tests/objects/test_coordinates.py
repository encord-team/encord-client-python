import logging
from copy import copy

import pytest

from encord.exceptions import LabelRowError
from encord.objects import Shape
from encord.objects.coordinates import (
    ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS,
    Cuboid2DCoordinates,
    PointCoordinate,
    PointCoordinate3D,
    PolygonCoordinates,
    PolylineCoordinates,
)


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


def test_polyline_coordinates():
    p1 = PolylineCoordinates.from_dict({"polyline": [{"x": 0, "y": 0}, {"x": 1, "y": 1}]})
    assert p1.values == [PointCoordinate(x=0, y=0), PointCoordinate(x=1, y=1)]

    p2_dict = {"0": {"x": 0, "y": 0}, "1": {"x": 1, "y": 1}}
    p2 = PolylineCoordinates.from_dict({"polyline": p2_dict})
    assert p2.values == [PointCoordinate(x=0, y=0), PointCoordinate(x=1, y=1)]
    assert p2.to_dict() == p2_dict

    p3_dict = {"0": {"x": 0, "y": 0, "z": 0}, "1": {"x": 1, "y": 1, "z": 1}}
    p3 = PolylineCoordinates.from_dict({"polyline": p3_dict})
    assert p3.values == [PointCoordinate3D(x=0, y=0, z=0), PointCoordinate3D(x=1, y=1, z=1)]
    assert p3.to_dict() == p3_dict

    # mixed 2D and 3D points
    with pytest.raises(LabelRowError):
        PolylineCoordinates.from_dict({"polyline": [{"x": 0, "y": 0}, {"x": 1, "y": 1, "z": 1}]})
    # point with missing coordinate
    with pytest.raises(LabelRowError):
        PolylineCoordinates.from_dict({"polyline": [{"x": 0}, {"x": 1, "y": 1}]})


def test_cuboid_2d_coordinates_perspective():
    """Test Cuboid2DCoordinates with perspective projection (vanishing point + scale ratio)."""
    front = [
        PointCoordinate(x=0, y=0),
        PointCoordinate(x=100, y=0),
        PointCoordinate(x=100, y=100),
        PointCoordinate(x=0, y=100),
    ]
    vanishing_point = PointCoordinate(x=400, y=300)
    scale_ratio = 0.75

    cuboid = Cuboid2DCoordinates(
        front=front,
        vanishing_point=vanishing_point,
        scale_ratio=scale_ratio,
    )

    assert cuboid.front == front
    assert cuboid.vanishing_point == vanishing_point
    assert cuboid.scale_ratio == scale_ratio
    assert cuboid.offset is None


def test_cuboid_2d_coordinates_parallel():
    """Test Cuboid2DCoordinates with parallel projection (offset)."""
    front = [
        PointCoordinate(x=0, y=0),
        PointCoordinate(x=100, y=0),
        PointCoordinate(x=100, y=100),
        PointCoordinate(x=0, y=100),
    ]
    offset = PointCoordinate(x=50, y=-50)

    cuboid = Cuboid2DCoordinates(front=front, offset=offset)

    assert cuboid.front == front
    assert cuboid.offset == offset
    assert cuboid.vanishing_point is None
    assert cuboid.scale_ratio is None


def test_cuboid_2d_coordinates_validation():
    """Test that Cuboid2DCoordinates validation raises errors for invalid configurations."""
    front = [PointCoordinate(x=0, y=0), PointCoordinate(x=100, y=100)]

    # Neither perspective nor parallel
    with pytest.raises(LabelRowError):
        Cuboid2DCoordinates(front=front)

    # Both perspective and parallel
    with pytest.raises(LabelRowError):
        Cuboid2DCoordinates(
            front=front,
            vanishing_point=PointCoordinate(x=400, y=300),
            scale_ratio=0.75,
            offset=PointCoordinate(x=50, y=-50),
        )

    # Perspective with only vanishing_point (missing scale_ratio)
    with pytest.raises(LabelRowError):
        Cuboid2DCoordinates(front=front, vanishing_point=PointCoordinate(x=400, y=300))

    # Perspective with only scale_ratio (missing vanishing_point)
    with pytest.raises(LabelRowError):
        Cuboid2DCoordinates(front=front, scale_ratio=0.75)


def test_cuboid_2d_coordinates_from_dict_perspective():
    """Test Cuboid2DCoordinates.from_dict with perspective projection."""
    data = {
        "cuboid_2d": {
            "front": [0, 0, 100, 0, 100, 100, 0, 100],
            "vanishingPoint": {"x": 400, "y": 300},
            "scaleRatio": 0.75,
        }
    }

    cuboid = Cuboid2DCoordinates.from_dict(data)

    assert len(cuboid.front) == 4
    assert cuboid.front[0] == PointCoordinate(x=0, y=0)
    assert cuboid.front[1] == PointCoordinate(x=100, y=0)
    assert cuboid.front[2] == PointCoordinate(x=100, y=100)
    assert cuboid.front[3] == PointCoordinate(x=0, y=100)
    assert cuboid.vanishing_point == PointCoordinate(x=400, y=300)
    assert cuboid.scale_ratio == 0.75
    assert cuboid.offset is None


def test_cuboid_2d_coordinates_from_dict_parallel():
    """Test Cuboid2DCoordinates.from_dict with parallel projection."""
    data = {
        "cuboid_2d": {
            "front": [0, 0, 100, 0, 100, 100, 0, 100],
            "offset": {"x": 50, "y": -50},
        }
    }

    cuboid = Cuboid2DCoordinates.from_dict(data)

    assert len(cuboid.front) == 4
    assert cuboid.offset == PointCoordinate(x=50, y=-50)
    assert cuboid.vanishing_point is None
    assert cuboid.scale_ratio is None


def test_cuboid_2d_coordinates_to_dict_perspective():
    """Test Cuboid2DCoordinates.to_dict with perspective projection."""
    front = [
        PointCoordinate(x=0, y=0),
        PointCoordinate(x=100, y=0),
        PointCoordinate(x=100, y=100),
        PointCoordinate(x=0, y=100),
    ]

    cuboid = Cuboid2DCoordinates(
        front=front,
        vanishing_point=PointCoordinate(x=400, y=300),
        scale_ratio=0.75,
    )

    result = cuboid.to_dict()

    assert result["front"] == [0, 0, 100, 0, 100, 100, 0, 100]
    assert result["vanishingPoint"] == {"x": 400, "y": 300}
    assert result["scaleRatio"] == 0.75
    assert "offset" not in result


def test_cuboid_2d_coordinates_to_dict_parallel():
    """Test Cuboid2DCoordinates.to_dict with parallel projection."""
    front = [
        PointCoordinate(x=0, y=0),
        PointCoordinate(x=100, y=0),
        PointCoordinate(x=100, y=100),
        PointCoordinate(x=0, y=100),
    ]

    cuboid = Cuboid2DCoordinates(front=front, offset=PointCoordinate(x=50, y=-50))

    result = cuboid.to_dict()

    assert result["front"] == [0, 0, 100, 0, 100, 100, 0, 100]
    assert result["offset"] == {"x": 50, "y": -50}
    assert "vanishingPoint" not in result
    assert "scaleRatio" not in result


def test_cuboid_2d_coordinates_roundtrip():
    """Test that to_dict and from_dict are inverse operations."""
    # Perspective projection
    original_perspective = Cuboid2DCoordinates(
        front=[
            PointCoordinate(x=10.5, y=20.5),
            PointCoordinate(x=110.5, y=20.5),
            PointCoordinate(x=110.5, y=120.5),
            PointCoordinate(x=10.5, y=120.5),
        ],
        vanishing_point=PointCoordinate(x=500.0, y=400.0),
        scale_ratio=0.6,
    )
    dict_perspective = original_perspective.to_dict()
    reconstructed_perspective = Cuboid2DCoordinates.from_dict({"cuboid_2d": dict_perspective})
    assert reconstructed_perspective == original_perspective

    # Parallel projection
    original_parallel = Cuboid2DCoordinates(
        front=[
            PointCoordinate(x=0, y=0),
            PointCoordinate(x=50, y=0),
            PointCoordinate(x=50, y=50),
            PointCoordinate(x=0, y=50),
        ],
        offset=PointCoordinate(x=25, y=-25),
    )
    dict_parallel = original_parallel.to_dict()
    reconstructed_parallel = Cuboid2DCoordinates.from_dict({"cuboid_2d": dict_parallel})
    assert reconstructed_parallel == original_parallel
