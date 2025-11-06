from dataclasses import asdict
from typing import Tuple
from unittest.mock import Mock

import pytest

from encord.constants.enums import is_geometric
from encord.exceptions import LabelRowError
from encord.objects import Classification, LabelRowV2, Option
from encord.orm.label_row import LabelRowMetadata
from tests.objects.common import FAKE_LABEL_ROW_METADATA
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.audio_labels import EMPTY_AUDIO_LABELS
from tests.objects.data.empty_image_group import empty_image_group_labels
from tests.objects.data.empty_video import labels


@pytest.mark.parametrize(
    "metadata_label",
    [
        pytest.param((FAKE_LABEL_ROW_METADATA, labels), id="empty_video"),
        pytest.param((FAKE_LABEL_ROW_METADATA, empty_image_group_labels), id="empty_image_group"),
        pytest.param((FAKE_LABEL_ROW_METADATA, EMPTY_AUDIO_LABELS), id="empty_audio"),
    ],
)
def test_classification_e2e(all_types_ontology, metadata_label: Tuple[LabelRowMetadata, dict]) -> None:
    label_row_metadata, labels = metadata_label
    label_row_metadata_dict = asdict(label_row_metadata)
    label_row_metadata = LabelRowMetadata(**label_row_metadata_dict)

    label_row = LabelRowV2(label_row_metadata, Mock(), all_types_ontology)
    label_row.from_labels_dict(labels)

    range_only = not is_geometric(label_row.data_type)

    ontology_child_1 = all_types_structure.get_child_by_title("Radio classification 1", Classification)
    answer_1 = ontology_child_1.get_child_by_title("cl 1 option 1", Option)
    answer_2 = ontology_child_1.get_child_by_title("cl 1 option 2", Option)
    classification_instance_1 = ontology_child_1.create_instance(range_only=range_only)

    classification_instance_1.set_answer(answer=answer_1)
    classification_instance_1.set_for_frames(frames=[0, 1, 2], created_by="test-user")

    # Setting with intersecting frames should fail
    if not range_only:
        with pytest.raises(LabelRowError):
            classification_instance_1.set_for_frames([0, 1, 2])

    label_row.add_classification_instance(classification_instance_1)

    # Adding the same classification should fail
    with pytest.raises(LabelRowError):
        label_row.add_classification_instance(classification_instance_1)

    classification_instance_2 = ontology_child_1.create_instance(range_only=range_only)
    classification_instance_2.set_answer(answer=answer_2)
    classification_instance_2.set_for_frames(frames=[0, 1, 2], created_by="test-user")

    # Setting a different classification, but from the same feature should fail
    if not range_only:
        with pytest.raises(LabelRowError):
            classification_instance_2.set_for_frames([2, 3, 4])

    # Testing serialisation -> parsing results in the same object
    encord_dict = label_row.to_encord_dict()

    label_row_2 = LabelRowV2(label_row_metadata, Mock(), all_types_ontology)
    label_row_2.from_labels_dict(encord_dict)
    encord_dict_2 = label_row_2.to_encord_dict()

    assert encord_dict == encord_dict_2, "LabelRows should be equal after serialisation and deserialisation"
