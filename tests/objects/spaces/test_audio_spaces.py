import json
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from deepdiff import DeepDiff

from encord.objects import Classification, LabelRowV2, Object
from encord.objects.constants import DEFAULT_MANUAL_ANNOTATION
from encord.objects.frames import Range
from encord.objects.spaces.range_space import AudioSpace
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.two_audio import DATA_GROUP_TWO_AUDIO_NO_LABELS, DATA_GROUP_WITH_TWO_AUDIO_LABELS
from tests.objects.data.data_group.two_videos import (
    DATA_GROUP_METADATA,
)

audio_obj_ontology_item = all_types_structure.get_child_by_hash("KVfzNkFy", Object)
text_classification = all_types_structure.get_child_by_hash("jPOcEsbw", Classification)


@pytest.fixture
def ontology():
    ontology_structure = Mock()
    ontology_structure.get_child_by_hash = all_types_structure.get_child_by_hash
    ontology = Mock(structure=ontology_structure)
    yield ontology


def test_audio_space_can_add_object_instances(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)

    audio_space = label_row.get_space_by_id("audio-1-uuid", type_=AudioSpace)
    # Check that no objects exist on space
    objects_on_audio_space = audio_space.get_object_instances()
    assert len(objects_on_audio_space) == 0

    # After adding, check that object exists, and has correct properties
    created_by = "new_user"
    created_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
    added_object_instance = audio_space.add_object_instance(
        obj=audio_obj_ontology_item,
        range=Range(start=10, end=100),
        created_by=created_by,
        created_at=created_at,
        manual_annotation=False,
    )
    objects_on_audio_space = audio_space.get_object_instances()
    assert len(objects_on_audio_space) == 1

    first_object_instance = objects_on_audio_space[0]

    first_object_instance_annotation = first_object_instance.get_annotation()
    assert first_object_instance.object_hash == added_object_instance.object_hash

    assert first_object_instance_annotation.ranges[0] == Range(start=10, end=100)
    assert first_object_instance_annotation.created_by == created_by
    assert first_object_instance_annotation.created_at == created_at
    assert first_object_instance_annotation.manual_annotation is False

    # Check that spaces has correct properties
    assert len(audio_space._objects_map.keys()) == 1
    assert added_object_instance.object_hash in audio_space._objects_map


def test_audio_space_can_remove_object_instances(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)

    audio_space = label_row.get_space_by_id("audio-1-uuid", type_=AudioSpace)

    assert audio_space is not None
    added_object_instance = audio_space.add_object_instance(obj=audio_obj_ontology_item, range=Range(start=10, end=100))
    objects_on_audio_space = audio_space.get_object_instances()

    # Check properties after adding object
    assert len(objects_on_audio_space) == 1
    assert len(audio_space._objects_map.keys()) == 1
    assert added_object_instance.object_hash in audio_space._objects_map

    # Check properties after removing object
    audio_space.remove_object_instance(added_object_instance.object_hash)
    objects_on_audio_space = audio_space.get_object_instances()
    assert len(objects_on_audio_space) == 0
    assert len(audio_space._objects_map.keys()) == 0


def test_audio_space_move_object_instances(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)

    audio_space_1 = label_row.get_space_by_id("audio-1-uuid", type_=AudioSpace)
    object_on_audio_space_1 = audio_space_1.add_object_instance(
        obj=audio_obj_ontology_item, range=Range(start=10, end=100)
    )
    objects_on_audio_space_1 = audio_space_1.get_object_instances()

    # Check properties of vision space 1 before moving object
    assert len(objects_on_audio_space_1) == 1
    assert len(audio_space_1._objects_map.keys()) == 1
    assert object_on_audio_space_1.object_hash in audio_space_1._objects_map

    # Check properties of vision space 2 before moving object
    audio_space_2 = label_row.get_space_by_id("audio-2-uuid", type_=AudioSpace)
    objects_on_audio_space_2 = audio_space_2.get_object_instances()
    assert len(objects_on_audio_space_2) == 0
    assert len(audio_space_2._objects_map.keys()) == 0

    # Move object from space 1 to space 2
    audio_space_2.move_object_instance_from_space(object_on_audio_space_1)

    # Check properties of image space 1 after moving object
    objects_on_audio_space_1 = audio_space_1.get_object_instances()
    assert len(objects_on_audio_space_1) == 0
    assert len(audio_space_1._objects_map.keys()) == 0

    # Check properties of image space 2 after moving object
    objects_on_audio_space_2 = audio_space_2.get_object_instances()
    assert len(objects_on_audio_space_2) == 1
    assert len(audio_space_2._objects_map.keys()) == 1


def test_audio_space_can_update_annotations_on_object_instance(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)

    audio_space = label_row.get_space_by_id("audio-1-uuid", type_=AudioSpace)
    added_object = audio_space.add_object_instance(obj=audio_obj_ontology_item, range=Range(start=10, end=100))

    annotation_on_audio = added_object.get_annotation()

    # Change annotation values
    annotation_on_audio.last_edited_by = "arthur@encord.com"
    annotation_on_audio.created_by = "clinton@encord.com"
    annotation_on_audio.ranges = Range(start=200, end=300)

    # Check output dict
    actual_object_answers = audio_space._to_object_answers()
    EXPECTED_OBJECT_ANSWERS = {
        added_object.object_hash: {
            "classifications": [],
            "objectHash": added_object.object_hash,
            "createdBy": "clinton@encord.com",
            "createdAt": "Fri, 24 Oct 2025 12:14:56 UTC",
            "lastEditedBy": "arthur@encord.com",
            "lastEditedAt": "Fri, 24 Oct 2025 12:14:56 UTC",
            "manualAnnotation": True,
            "featureHash": "KVfzNkFy",
            "name": "audio object",
            "color": "#A4FF00",
            "shape": "audio",
            "value": "audio_object",
            "range": [[10, 100]],
        }
    }

    assert not DeepDiff(
        EXPECTED_OBJECT_ANSWERS, actual_object_answers, exclude_regex_paths=[r".*\['lastEditedAt'\]|.*\['createdAt'\]"]
    )


def test_audio_space_can_add_classification_instances(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)

    audio_space = label_row.get_space_by_id("audio-1-uuid", type_=AudioSpace)
    # Check that no objects exist on space
    classifications_on_audio_space = audio_space.get_classification_instances()
    assert len(classifications_on_audio_space) == 0

    # After adding, check that object exists, and has correct properties
    created_by = "new_user"
    created_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
    added_classification_instance = audio_space.add_classification_instance(
        classification=text_classification,
        created_by=created_by,
        created_at=created_at,
        manual_annotation=False,
    )
    classifications_on_audio_space = audio_space.get_classification_instances()
    assert len(classifications_on_audio_space) == 1

    first_classification_instance = classifications_on_audio_space[0]
    annotations_on_first_classification_instance = first_classification_instance.get_annotations()
    assert first_classification_instance.classification_hash == added_classification_instance.classification_hash
    assert len(annotations_on_first_classification_instance) == 1

    frames_on_annotations = [annotation.frame for annotation in annotations_on_first_classification_instance]
    assert frames_on_annotations == [0]
    for annotation in annotations_on_first_classification_instance:
        assert annotation.created_by == created_by
        assert annotation.created_at == created_at
        assert annotation.manual_annotation is False

    # Check that spaces has correct properties
    assert len(audio_space._classifications_map.keys()) == 1
    assert added_classification_instance.classification_hash in audio_space._classifications_map


def test_audio_space_can_remove_classification_instances(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)

    audio_space = label_row.get_space_by_id("audio-1-uuid", type_=AudioSpace)

    assert audio_space is not None
    added_classification_instance = audio_space.add_classification_instance(classification=text_classification)
    classifications_on_audio_space = audio_space.get_classification_instances()

    # Check properties after adding classification
    assert len(classifications_on_audio_space) == 1
    assert len(audio_space._classifications_map.keys()) == 1
    assert added_classification_instance.classification_hash in audio_space._classifications_map

    # Check properties after removing classification
    audio_space.remove_classification_instance(added_classification_instance.classification_hash)
    classifications_on_audio_space = audio_space.get_classification_instances()
    assert len(classifications_on_audio_space) == 0
    assert len(audio_space._classifications_map.keys()) == 0


def test_audio_space_move_classification_instances(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)

    audio_space_1 = label_row.get_space_by_id("audio-1-uuid", type_=AudioSpace)
    classification_on_audio_space_1 = audio_space_1.add_classification_instance(classification=text_classification)
    classifications_on_audio_space_1 = audio_space_1.get_classification_instances()

    # Check properties of vision space 1 before moving classification
    assert len(classifications_on_audio_space_1) == 1
    assert len(audio_space_1._classifications_map.keys()) == 1
    assert classification_on_audio_space_1.classification_hash in audio_space_1._classifications_map

    # Check properties of vision space 2 before moving classification
    audio_space_2 = label_row.get_space_by_id("audio-2-uuid", type_=AudioSpace)
    classifications_on_image_space_2 = audio_space_2.get_classification_instances()
    assert len(classifications_on_image_space_2) == 0
    assert len(audio_space_2._classifications_map.keys()) == 0

    # Move classification from space 1 to space 2
    audio_space_2.move_classification_instance_from_space(classification_on_audio_space_1)

    # Check properties of vision space 1 after moving classification
    classifications_on_audio_space_1 = audio_space_1.get_classification_instances()
    assert len(classifications_on_audio_space_1) == 0
    assert len(audio_space_1._classifications_map.keys()) == 0

    # Check properties of vision space 2 after moving classification
    classifications_on_image_space_2 = audio_space_2.get_classification_instances()
    assert len(classifications_on_image_space_2) == 1
    assert len(audio_space_2._classifications_map.keys()) == 1


def test_read_and_export_labels(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_WITH_TWO_AUDIO_LABELS)

    audio_space_1 = label_row.get_space_by_id("audio-1-uuid", type_=AudioSpace)
    objects_on_audio_space_1 = audio_space_1.get_object_instances()
    assert len(objects_on_audio_space_1) == 1

    audio_object_instance = objects_on_audio_space_1[0]
    assert audio_object_instance.object_hash == "speaker1"
    assert audio_object_instance.get_annotation_frames() == {0}
    assert audio_object_instance.get_annotation().coordinates.range[0] == Range(start=100, end=200)

    classifications_on_audio_space_1 = audio_space_1.get_classification_instances()
    assert len(classifications_on_audio_space_1) == 1
    classification_instance = classifications_on_audio_space_1[0]
    assert classification_instance.classification_hash == "classification1"
    assert classification_instance.get_annotation_frames() == {0}

    output_dict = label_row.to_encord_dict()
    assert not DeepDiff(
        DATA_GROUP_WITH_TWO_AUDIO_LABELS,
        output_dict,
        exclude_regex_paths=[r".*\['trackHash'\]"],
        ignore_order_func=lambda x: x.path().endswith("['objects']"),
    )
