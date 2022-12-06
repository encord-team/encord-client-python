"""
All tests in regards to converting from and to Encord dict to the label row.
"""
from encord.objects.label_structure import LabelRow
from tests.objects.data.empty_image_group import (
    empty_image_group_labels,
    empty_image_group_ontology,
)
from tests.objects.data.image_group import image_group_labels, image_group_ontology


def test_serialise_label_row_class_for_empty_image_group():
    label_row = LabelRow(empty_image_group_labels, empty_image_group_ontology)

    expected = label_row.to_encord_dict()
    assert expected == empty_image_group_labels


def test_serialise_label_row_class_used_image_group():
    label_row = LabelRow(image_group_labels, image_group_ontology)

    expected = label_row.to_encord_dict()
    assert expected == image_group_labels
    # DENIS: probably needs a deepdiff. Some bits still missing.
