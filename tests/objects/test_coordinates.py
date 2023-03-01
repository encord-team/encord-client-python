from copy import copy

from encord.objects import Shape
from encord.objects.coordinates import ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS


def test_acceptable_coordinates_for_ontology_items() -> None:
    all_mappings = copy(ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS)
    for shape in Shape:
        assert shape in all_mappings
        del all_mappings[shape]
    assert not all_mappings
