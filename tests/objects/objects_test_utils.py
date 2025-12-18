from copy import deepcopy
from typing import List, Mapping, Union

from deepdiff import DeepDiff, helper

from encord.objects import LabelRowV2
from tests.objects.common import BASE_LABEL_ROW_METADATA


def validate_label_row_serialisation(label_row: LabelRowV2) -> None:
    """
    Validates that a LabelRowV2 can be serialized to a labels dict and deserialized back without loss of information.
    """
    original_encord_dict = label_row.to_encord_dict()
    new_label_row = LabelRowV2(BASE_LABEL_ROW_METADATA, label_row._project_client, label_row._ontology)
    new_label_row._label_row_read_only_data = deepcopy(
        label_row._label_row_read_only_data
    )  # replace the metadata with the one from the row

    new_label_row.from_labels_dict(original_encord_dict)
    new_serialised_dict = new_label_row.to_encord_dict()

    deep_diff_enhanced(original_encord_dict, new_serialised_dict)


def deep_diff_enhanced(
    actual: Union[dict, list],
    expected: Union[Mapping, list],
    exclude_regex_paths: List[str] = None,
    exclude_paths: List[str] = None,
):
    """
    Deep comparison that uses DeepDiff for regex path exclusions and `assert` to get an easily comparable,
    human-readable diff in tools like PyCharm.
    """
    exclude_paths = [] if exclude_paths is None else exclude_paths
    exclude_regex_paths = [] if exclude_regex_paths is None else exclude_regex_paths
    if DeepDiff(
        expected,
        actual,
        ignore_order=True,
        exclude_paths=exclude_paths,
        exclude_regex_paths=exclude_regex_paths,
    ):
        print(
            DeepDiff(
                expected,
                actual,
                ignore_order=True,
                exclude_regex_paths=exclude_regex_paths,
                view=helper.COLORED_COMPACT_VIEW,
            )
        )
        assert actual == expected
