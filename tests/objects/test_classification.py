from dataclasses import asdict
from unittest.mock import Mock, PropertyMock

import pytest

from encord.exceptions import LabelRowError
from encord.objects import ClassificationInstance, LabelRowV2, Classification
from encord.objects.frames import Range
from encord.orm.label_row import LabelRowMetadata
from tests.objects.common import FAKE_LABEL_ROW_METADATA
from tests.objects.data.all_ontology_types import all_ontology_types
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.audio_labels import EMPTY_AUDIO_LABELS
from tests.objects.test_label_structure_converter import ontology_from_dict

checklist_classification: Classification = all_types_structure.get_child_by_hash("3DuQbFxo")


@pytest.fixture
def ontology():
    ontology_structure = PropertyMock(return_value=all_types_structure)
    ontology = Mock(structure=ontology_structure)
    yield ontology


@pytest.fixture
def empty_audio_label_row() -> LabelRowV2:
    label_row_metadata_dict = asdict(FAKE_LABEL_ROW_METADATA)
    label_row_metadata_dict["frames_per_second"] = 1000
    label_row_metadata_dict["data_type"] = "AUDIO"
    label_row_metadata = LabelRowMetadata(**label_row_metadata_dict)

    label_row = LabelRowV2(label_row_metadata, Mock(), ontology_from_dict(all_ontology_types))
    label_row.from_labels_dict(EMPTY_AUDIO_LABELS)

    return label_row


def test_non_range_classification_cannot_be_added_to_audio_label_row(ontology):
    label_row_metadata_dict = asdict(FAKE_LABEL_ROW_METADATA)
    label_row_metadata_dict["frames_per_second"] = 1000
    label_row_metadata_dict["data_type"] = "AUDIO"
    label_row_metadata = LabelRowMetadata(**label_row_metadata_dict)

    label_row = LabelRowV2(label_row_metadata, Mock(), ontology_from_dict(all_ontology_types))
    label_row.from_labels_dict(EMPTY_AUDIO_LABELS)

    with pytest.raises(LabelRowError):
        classification_instance = ClassificationInstance(checklist_classification)
        classification_instance.set_for_frames(Range(start=0, end=1500))
        label_row.add_classification_instance(classification_instance)

    with pytest.raises(LabelRowError):
        classification_instance = checklist_classification.create_instance()
        label_row.add_classification_instance(classification_instance)


def test_audio_classification_overwrite(ontology, empty_audio_label_row: LabelRowV2):
    classification_instance = ClassificationInstance(checklist_classification, range_only=True)
    classification_instance.set_for_frames(Range(start=0, end=100))
    empty_audio_label_row.add_classification_instance(classification_instance)

    with pytest.raises(LabelRowError):
        classification_instance.set_for_frames(Range(start=5, end=20))

    with pytest.raises(LabelRowError):
        classification_instance.set_for_frames(Range(start=100, end=101))

    # No error when set overwrite to True
    classification_instance.set_for_frames(Range(start=100, end=101), overwrite=True)
    range_list = classification_instance.range_list
    assert len(range_list) == 1
    assert range_list[0].start == 0
    assert range_list[0].end == 101


def test_audio_classification_exceed_max_frames(ontology, empty_audio_label_row: LabelRowV2):
    classification_instance = ClassificationInstance(checklist_classification, range_only=True)
    classification_instance.set_for_frames(Range(start=0, end=100))
    empty_audio_label_row.add_classification_instance(classification_instance)

    with pytest.raises(LabelRowError):
        classification_instance.set_for_frames(Range(start=200, end=5000))


def test_audio_classification_can_be_added_edited_and_removed(ontology, empty_audio_label_row: LabelRowV2):
    label_row = empty_audio_label_row
    classification_instance = ClassificationInstance(checklist_classification, range_only=True)
    classification_instance.set_for_frames(Range(start=0, end=1500))
    range_list = classification_instance.range_list
    assert len(range_list) == 1
    assert range_list[0].start == 0
    assert range_list[0].end == 1500

    label_row.add_classification_instance(classification_instance)
    assert len(label_row.get_classification_instances()) == 1
    classification_instance.set_for_frames(Range(start=2000, end=2499))
    range_list = classification_instance.range_list
    assert len(range_list) == 2
    assert range_list[0].start == 0
    assert range_list[0].end == 1500
    assert range_list[1].start == 2000
    assert range_list[1].end == 2499

    label_row.remove_classification(classification_instance)
    assert len(label_row.get_classification_instances()) == 0