from copy import copy

from encord.objects import Shape
from encord.objects.coordinates import ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS, SkeletonCoordinate, Visibility


def test_acceptable_coordinates_for_ontology_items() -> None:
    all_mappings = copy(ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS)
    for shape in Shape:
        assert shape in all_mappings
        del all_mappings[shape]
    assert not all_mappings


def test_skeleton_coordinates_without_visibility_works() -> None:
    invisible_pnt = SkeletonCoordinate.from_dict(
        {
            "x": 0.2356,
            "y": 0.9396,
            "name": "point_2",
            "color": "#000000",
            "value": "point_2",
            "featureHash": "OqR+F4dN",
            "visibility": "invisible",
        }
    )
    assert invisible_pnt.visibility is Visibility.INVISIBLE

    visible_pnt = SkeletonCoordinate.from_dict(
        {
            "x": 0.2356,
            "y": 0.9396,
            "name": "point_2",
            "color": "#000000",
            "value": "point_2",
            "featureHash": "OqR+F4dN",
        }
    )
    assert visible_pnt.visibility is Visibility.VISIBLE
