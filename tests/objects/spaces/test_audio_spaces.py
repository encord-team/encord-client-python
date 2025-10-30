from unittest.mock import Mock

import pytest
from deepdiff import DeepDiff

from encord.exceptions import LabelRowError
from encord.objects import Classification, LabelRowV2, Object
from encord.objects.attributes import Attribute
from encord.objects.frames import Range
from encord.objects.spaces.range_space import AudioSpace
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.two_audio import DATA_GROUP_TWO_AUDIO_NO_LABELS, DATA_GROUP_WITH_TWO_AUDIO_LABELS
from tests.objects.data.data_group.two_videos import (
    DATA_GROUP_METADATA,
)

audio_obj_ontology_item = all_types_structure.get_child_by_hash("KVfzNkFy", Object)
audio_obj_transcript_attribute_ontology_item = audio_obj_ontology_item.get_child_by_hash(
    "transcriptFeatureHash", Attribute
)
text_classification = all_types_structure.get_child_by_hash("jPOcEsbw", Classification)


@pytest.fixture
def ontology():
    ontology_structure = Mock()
    ontology_structure.get_child_by_hash = all_types_structure.get_child_by_hash
    ontology = Mock(structure=ontology_structure)
    yield ontology


def test_add_object_to_audio_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space_by_id("audio-1-uuid", type_=AudioSpace)

    # Act
    new_object = label_row.create_space_object(ontology_class=audio_obj_ontology_item)
    audio_space_1.place_object(
        object=new_object,
        ranges=[Range(start=0, end=500)],
    )

    audio_space_1.place_object(object=new_object, ranges=[Range(start=400, end=1000)])

    # Assert
    space_objects_on_label_row = label_row.list_space_objects()
    assert len(space_objects_on_label_row) == 1

    space_objects = audio_space_1.get_objects()
    space_object = space_objects[0]
    assert len(space_objects) == 1
    assert space_object.spaces == {audio_space_1.space_id: audio_space_1}

    annotations = audio_space_1.get_object_annotations()
    assert len(annotations) == 1

    first_annotation = annotations[0]

    assert first_annotation.ranges == [Range(start=0, end=1000)]
    assert first_annotation.object_hash == new_object.object_hash


def test_remove_object_from_audio_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space_by_id("audio-1-uuid", type_=AudioSpace)
    new_object = label_row.create_space_object(ontology_class=audio_obj_ontology_item)
    audio_space_1.place_object(
        object=new_object,
        ranges=[Range(start=0, end=500)],
    )

    space_objects = audio_space_1.get_objects()
    assert len(space_objects) == 1

    annotations = audio_space_1.get_object_annotations()
    assert len(annotations) == 1

    first_annotation = annotations[0]

    # Act
    audio_space_1.remove_space_object(new_object.object_hash)

    # Assert
    space_objects_on_label_row = label_row.list_space_objects()
    space_object_on_label_row = space_objects_on_label_row[0]

    assert len(space_objects_on_label_row) == 1
    assert space_object_on_label_row.spaces == {}

    space_objects = audio_space_1.get_objects()
    assert len(space_objects) == 0

    annotations = audio_space_1.get_object_annotations()
    assert len(annotations) == 0
    with pytest.raises(LabelRowError):
        assert first_annotation.ranges


def test_add_object_to_two_audio(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space_by_id("audio-1-uuid", type_=AudioSpace)
    audio_space_2 = label_row.get_space_by_id("audio-2-uuid", type_=AudioSpace)

    new_object = label_row.create_space_object(ontology_class=audio_obj_ontology_item)
    range_1 = Range(start=0, end=500)
    range_2 = Range(start=700, end=1000)

    # Act
    audio_space_1.place_object(
        object=new_object,
        ranges=range_1,
    )
    audio_space_2.place_object(object=new_object, ranges=range_2)

    # Assert
    entities = audio_space_1.get_objects()
    assert len(entities) == 1

    annotations_on_audio_space_1 = audio_space_1.get_object_annotations()
    first_annotation_on_audio_space_1 = annotations_on_audio_space_1[0]
    assert len(annotations_on_audio_space_1) == 1
    assert first_annotation_on_audio_space_1.ranges == [range_1]

    annotations_on_audio_space_2 = audio_space_2.get_object_annotations()
    first_annotation_on_audio_space_2 = annotations_on_audio_space_2[0]
    assert len(annotations_on_audio_space_2) == 1
    assert first_annotation_on_audio_space_2.ranges == [range_2]


def test_update_attribute_for_object_which_exist_on_two_spaces(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space_by_id("audio-1-uuid", type_=AudioSpace)
    audio_space_2 = label_row.get_space_by_id("audio-2-uuid", type_=AudioSpace)

    new_object = label_row.create_space_object(ontology_class=audio_obj_ontology_item)
    ranges = Range(start=0, end=500)

    audio_space_1.place_object(
        object=new_object,
        ranges=ranges,
    )

    audio_space_2.place_object(
        object=new_object,
        ranges=ranges,
    )

    object_answer = new_object.get_answer(attribute=audio_obj_transcript_attribute_ontology_item)
    assert object_answer is None

    # Act
    new_answer = "Hi, my name is Arthur."
    new_object.set_answer(attribute=audio_obj_transcript_attribute_ontology_item, answer=new_answer)

    # Assert
    object_answer = new_object.get_answer(attribute=audio_obj_transcript_attribute_ontology_item)
    assert object_answer == new_answer

    object_on_audio_space_1 = audio_space_1.get_objects()[0]
    assert object_on_audio_space_1.get_answer(audio_obj_transcript_attribute_ontology_item) == new_answer

    object_on_audio_space_2 = audio_space_2.get_objects()[0]
    assert object_on_audio_space_2.get_answer(audio_obj_transcript_attribute_ontology_item) == new_answer

    object_answer_dict = label_row.to_encord_dict()["object_answers"]
    EXPECTED_DICT = {
        new_object.object_hash: {
            "classifications": [
                {
                    "name": "Transcript",
                    "value": "transcript",
                    "answers": new_answer,
                    "featureHash": "transcriptFeatureHash",
                    "manualAnnotation": True,
                }
            ],
            "objectHash": new_object.object_hash,
            "range": [[0, 500]],
            "createdBy": None,
            "createdAt": "Wed, 29 Oct 2025 20:11:16 UTC",
            "lastEditedBy": None,
            "lastEditedAt": "Wed, 29 Oct 2025 20:11:16 UTC",
            "manualAnnotation": True,
            "featureHash": "KVfzNkFy",
            "name": "audio object",
            "color": "#A4FF00",
            "shape": "audio",
            "value": "audio_object",
        }
    }

    assert not DeepDiff(
        object_answer_dict,
        EXPECTED_DICT,
        exclude_regex_paths=[r".*\['createdAt'\]", r".*\['lastEditedAt'\]"],
    )


def test_add_classification_to_audio_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space_by_id("audio-1-uuid", type_=AudioSpace)

    # Act
    new_classification = label_row.create_space_classification(ontology_class=text_classification)
    audio_space_1.place_classification(classification=new_classification, ranges=Range(start=0, end=500))
    audio_space_1.place_classification(classification=new_classification, ranges=Range(start=700, end=1000))

    text_answer = "Some answer"
    new_classification.set_answer(answer=text_answer)

    # Assert
    entities = audio_space_1.get_classifications()
    assert len(entities) == 1

    annotations = audio_space_1.get_classification_annotations()
    assert len(annotations) == 1

    first_annotation = annotations[0]
    assert first_annotation.classification_hash == new_classification.classification_hash

    classification_answers_dict = label_row.to_encord_dict()["classification_answers"]
    expected_dict = {
        new_classification.classification_hash: {
            "classifications": [
                {
                    "name": "Text classification",
                    "value": "text_classification",
                    "answers": text_answer,
                    "featureHash": "OxrtEM+v",
                    "manualAnnotation": True,
                }
            ],
            "classificationHash": new_classification.classification_hash,
            "featureHash": "jPOcEsbw",
            "range": [],
            "createdBy": None,
            "createdAt": "Wed, 29 Oct 2025 23:38:32 UTC",
            "lastEditedBy": None,
            "lastEditedAt": "Wed, 29 Oct 2025 23:38:32 UTC",
            "manualAnnotation": True,
        }
    }

    assert not DeepDiff(
        classification_answers_dict,
        expected_dict,
        exclude_regex_paths=[r".*\['createdAt'\]", r".*\['lastEditedAt'\]"],
    )


def test_remove_classification_from_audio_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space_by_id("audio-1-uuid", type_=AudioSpace)

    new_classification = label_row.create_space_classification(ontology_class=text_classification)
    audio_space_1.place_classification(classification=new_classification, ranges=Range(start=0, end=500))
    entities = audio_space_1.get_classifications()
    assert len(entities) == 1
    annotations = audio_space_1.get_classification_annotations()
    assert len(annotations) == 1

    # Act
    audio_space_1.remove_space_classification(new_classification.classification_hash)

    # Assert
    entities = audio_space_1.get_classifications()
    assert len(entities) == 0
    annotations = audio_space_1.get_classification_annotations()
    assert len(annotations) == 0


def test_read_and_export_labels(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_WITH_TWO_AUDIO_LABELS)

    audio_space_1 = label_row.get_space_by_id("audio-1-uuid", type_=AudioSpace)
    objects_on_audio_space_1 = audio_space_1.get_objects()
    assert len(objects_on_audio_space_1) == 1

    audio_object_instance = objects_on_audio_space_1[0]
    assert audio_object_instance.object_hash == "speaker1"

    annotations_on_audio_space_1 = audio_space_1.get_object_annotations()
    first_annotation_on_audio_space_1 = annotations_on_audio_space_1[0]
    assert first_annotation_on_audio_space_1.ranges == [Range(start=100, end=200)]

    classifications_on_audio_space_1 = audio_space_1.get_classifications()
    assert len(classifications_on_audio_space_1) == 1

    classification_instance = classifications_on_audio_space_1[0]
    assert classification_instance.classification_hash == "classification1"

    output_dict = label_row.to_encord_dict()

    assert not DeepDiff(
        DATA_GROUP_WITH_TWO_AUDIO_LABELS,
        output_dict,
        exclude_regex_paths=[r".*\['trackHash'\]"],
        ignore_order_func=lambda x: x.path().endswith("['objects']"),
    )
