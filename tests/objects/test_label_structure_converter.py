"""
All tests regarding converting from and to Encord dict to the label row.
"""
from typing import List, Union

from deepdiff import DeepDiff

from encord.objects.label_structure import LabelRowClass
from tests.objects.data import (
    data_1,
    native_image_data,
    ontology_with_many_dynamic_classifications,
    video_with_dynamic_classifications,
)
from tests.objects.data.all_ontology_types import all_ontology_types
from tests.objects.data.dicom_labels import dicom_labels
from tests.objects.data.dynamic_classifications_ontology import (
    dynamic_classifications_ontology,
)
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
        print(DeepDiff(expected, actual, ignore_order=True, exclude_regex_paths=exclude_regex_paths))
        assert expected == actual


def test_serialise_image_group_with_classifications():
    label_row = LabelRowClass(empty_image_group_labels, empty_image_group_ontology)

    actual = label_row.to_encord_dict()
    assert empty_image_group_labels == actual

    label_row = LabelRowClass(image_group_labels, image_group_ontology)

    actual = label_row.to_encord_dict()
    deep_diff_enhanced(
        image_group_labels,
        actual,
        exclude_regex_paths=["\['reviews'\]", "\['isDeleted'\]", "\['createdAt'\]", "\['lastEditedAt'\]"],
    )
    # TODO: I'm only not comparing dates because of timezone differences. This should be done properly.
    #  Probably I can just save timezone information to ensure that going back will not crash the timezone.


def test_serialise_video():
    label_row = LabelRowClass(data_1.labels, data_1.ontology)

    # TODO: also check at this point whether the internal data is correct.

    actual = label_row.to_encord_dict()
    deep_diff_enhanced(
        actual,
        data_1.labels,
        exclude_regex_paths=["\['reviews'\]", "\['isDeleted'\]", "\['createdAt'\]", "\['lastEditedAt'\]"],
    )


def test_serialise_image_with_object_answers():
    label_row = LabelRowClass(native_image_data.labels, all_ontology_types)

    actual = label_row.to_encord_dict()

    # assert actual == native_image_data.labels
    deep_diff_enhanced(
        actual,
        native_image_data.labels,
        exclude_regex_paths=["\['reviews'\]", "\['isDeleted'\]", "\['createdAt'\]", "\['lastEditedAt'\]"],
    )


def test_serialise_dicom_with_dynamic_classifications():
    label_row = LabelRowClass(dicom_labels, dynamic_classifications_ontology)

    assert label_row.data_link is None
    assert label_row.height == 256
    assert label_row.width == 256
    assert isinstance(label_row.dicom_data_links, list)
    assert isinstance(label_row.dicom_data_links[0], str)

    actual = label_row.to_encord_dict()

    deep_diff_enhanced(
        actual,
        dicom_labels,
        exclude_regex_paths=["\['trackHash'\]"],
    )
    # NOTE: likely we do not care about the trackHash. If we end up caring about it, we'll have to ensure that we can
    #  set it from parsing the data and keep it around when setting new answers for example.


def test_dynamic_classifications():
    label_row = LabelRowClass(
        video_with_dynamic_classifications.labels, ontology_with_many_dynamic_classifications.ontology
    )

    actual = label_row.to_encord_dict()

    # assert actual == video_with_dynamic_classifications.labels
    deep_diff_enhanced(
        actual,
        video_with_dynamic_classifications.labels,
        exclude_regex_paths=["\['trackHash'\]"],
    )
