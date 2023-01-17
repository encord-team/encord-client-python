"""
All tests in regards to converting from and to Encord dict to the label row.
"""
from typing import List, Union

from deepdiff import DeepDiff

from encord.objects.label_structure import LabelRowClass
from tests.objects.data import data_1
from tests.objects.data.empty_image_group import (
    empty_image_group_labels,
    empty_image_group_ontology,
)
from tests.objects.data.image_group import image_group_labels, image_group_ontology


def deep_diff_enhanced(actual: Union[dict, list], expected: Union[dict, list], exclude_regex_paths: List[str] = None):
    """Basically a deep diff but with an normal assert after. `DeepDiff` to be able to exclude
    regex paths, and `assert` to see an easily comparable diff with tools such as Pycharm."""
    if exclude_regex_paths is None:
        exclude_regex_paths = []
    if DeepDiff(
        expected,
        actual,
        ignore_order=True,
        exclude_regex_paths=exclude_regex_paths,
    ):
        assert not DeepDiff(expected, actual, ignore_order=True, exclude_regex_paths=exclude_regex_paths)
        assert expected == actual


def test_serialise_label_row_class_for_empty_image_group():
    label_row = LabelRowClass(empty_image_group_labels, empty_image_group_ontology)

    expected = label_row.to_encord_dict()
    assert expected == empty_image_group_labels

    label_row = LabelRowClass(image_group_labels, image_group_ontology)

    expected = label_row.to_encord_dict()
    # assert expected == image_group_labels
    deep_diff_enhanced(
        expected,
        image_group_labels,
        exclude_regex_paths=["\['reviews'\]", "\['isDeleted'\]", "\['createdAt'\]", "\['lastEditedAt'\]"],
    )
    # TODO: I'm only not comparing dates because of timezone differences. This should be done properly.


def test_serialise_video():
    label_row = LabelRowClass(data_1.labels, data_1.ontology)

    expected = label_row.to_encord_dict()
    deep_diff_enhanced(
        expected,
        data_1.labels,
        exclude_regex_paths=["\['reviews'\]", "\['isDeleted'\]", "\['createdAt'\]", "\['lastEditedAt'\]"],
    )
