from encord.objects import Object
from encord.objects.label_utils import _read_object_id
from tests.objects.data.all_types_ontology_structure import all_types_structure

box_ontology_item = all_types_structure.get_child_by_hash("MjI2NzEy", Object)


def test_read_object_id_accepts_both_spellings():
    assert _read_object_id({"objectId": 7}) == 7
    assert _read_object_id({"objectID": 7}) == 7
    assert _read_object_id({}) is None


def test_read_object_id_prefers_object_id_spelling_when_both_present():
    assert _read_object_id({"objectId": 7, "objectID": 9}) == 7
