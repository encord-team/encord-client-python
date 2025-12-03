from datetime import datetime
from unittest.mock import Mock

import pytest
from deepdiff import DeepDiff

from encord.common.time_parser import format_datetime_to_long_string
from encord.exceptions import LabelRowError
from encord.objects import LabelRowV2, Object
from encord.objects.attributes import Attribute
from encord.objects.coordinates import AudioCoordinates
from encord.objects.frames import Range
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.two_audio import (
    DATA_GROUP_METADATA,
    DATA_GROUP_TWO_AUDIO_NO_LABELS,
)

audio_obj_ontology_item = all_types_structure.get_child_by_hash("KVfzNkFy", Object)
audio_obj_transcription_attribute_ontology_item = audio_obj_ontology_item.get_child_by_hash(
    "transcriptFeatureHash", type_=Attribute
)


@pytest.fixture
def ontology():
    ontology_structure = Mock()
    ontology_structure.get_child_by_hash = all_types_structure.get_child_by_hash
    ontology = Mock(structure=ontology_structure)
    yield ontology


def test_label_row_get_object_instances_on_space(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")
    audio_space_2 = label_row.get_space(id="audio-2-uuid", type_="audio")

    # Act
    object_instance_1 = audio_obj_ontology_item.create_instance()
    object_instance_2 = audio_obj_ontology_item.create_instance()

    range_1 = Range(start=0, end=100)
    range_2 = Range(start=200, end=300)

    # Place objects on space 1
    audio_space_1.put_object_instance(
        object_instance=object_instance_1,
        ranges=range_1,
    )
    audio_space_1.put_object_instance(
        object_instance=object_instance_2,
        ranges=range_2,
    )

    # Place objects on space 2
    audio_space_2.put_object_instance(object_instance=object_instance_1, ranges=range_2)

    # Assert
    object_instances = label_row.get_object_instances()
    assert len(object_instances) == 2

    # For backwards compatibiity, all audio objects are on frame=0
    object_instances_on_frame_1 = label_row.get_object_instances(filter_frames=[0])
    assert len(object_instances_on_frame_1) == 2

    object_instances_on_frame_2 = label_row.get_object_instances(filter_frames=[1])
    assert len(object_instances_on_frame_2) == 0


def test_place_object_on_audio_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")

    # Act
    new_object_instance = audio_obj_ontology_item.create_instance()
    audio_space_1.put_object_instance(
        object_instance=new_object_instance,
        ranges=Range(start=0, end=100),
    )

    audio_space_1.put_object_instance(
        object_instance=new_object_instance, ranges=Range(start=80, end=200), on_overlap="merge"
    )

    # Assert
    object_instances = label_row.get_object_instances()
    assert len(object_instances) == 1

    objects_on_space = audio_space_1.get_object_instances()
    object_on_space = objects_on_space[0]
    assert len(objects_on_space) == 1
    assert object_on_space._spaces == {audio_space_1.space_id: audio_space_1}

    annotations = audio_space_1.get_object_instance_annotations()
    assert len(annotations) == 1

    first_annotation = annotations[0]
    assert first_annotation.frame == 0  # Frame is here for backwards compatibility
    assert first_annotation.coordinates == AudioCoordinates(
        range=[Range(start=0, end=200)]
    )  # Coordinates are here for backwards compatibility
    assert first_annotation.object_hash == new_object_instance.object_hash
    assert first_annotation.ranges == [Range(start=0, end=200)]


def test_put_objects_with_error_overlapping_strategy(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")
    new_object_instance = audio_obj_ontology_item.create_instance()
    audio_space_1.put_object_instance(
        object_instance=new_object_instance,
        ranges=Range(start=0, end=100),
    )

    # Act
    with pytest.raises(LabelRowError) as e:
        audio_space_1.put_object_instance(
            object_instance=new_object_instance,
            ranges=Range(start=80, end=200),
        )

    assert e.value.message == (
        "Annotations already exist on the ranges [(80:100)]. "
        "Set the 'on_overlap' parameter to 'merge' to add the object instance to the new ranges while keeping existing annotations. "
        "Set the 'on_overlap' parameter to 'replace' to remove object instance from existing ranges before adding it to the new ranges."
    )


def test_put_objects_with_merge_overlapping_strategy(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")
    new_object_instance = audio_obj_ontology_item.create_instance()
    audio_space_1.put_object_instance(
        object_instance=new_object_instance,
        ranges=Range(start=0, end=100),
    )

    # Act
    audio_space_1.put_object_instance(
        object_instance=new_object_instance, ranges=Range(start=80, end=200), on_overlap="merge"
    )

    # Assert
    object_annotations = audio_space_1.get_object_instance_annotations()
    assert object_annotations[0].ranges == [Range(start=0, end=200)]


def test_put_objects_with_replace_overlapping_strategy(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")
    new_object_instance = audio_obj_ontology_item.create_instance()
    audio_space_1.put_object_instance(
        object_instance=new_object_instance,
        ranges=Range(start=0, end=100),
    )

    # Act
    audio_space_1.put_object_instance(
        object_instance=new_object_instance, ranges=Range(start=80, end=200), on_overlap="replace"
    )

    # Assert
    object_annotations = audio_space_1.get_object_instance_annotations()
    assert object_annotations[0].ranges == [Range(start=80, end=200)]


def test_place_object_on_invalid_ranges_on_audio_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")
    new_object_instance = audio_obj_ontology_item.create_instance()

    # Act
    with pytest.raises(LabelRowError) as negative_range_error:
        audio_space_1.put_object_instance(
            object_instance=new_object_instance,
            ranges=Range(start=-20, end=100),
        )

    with pytest.raises(LabelRowError) as exceed_max_range_error:
        audio_space_1.put_object_instance(object_instance=new_object_instance, ranges=Range(start=0, end=6 * 60 * 1000))

    # Assert
    assert (
        negative_range_error.value.message == "Range starting with -20 is invalid. Negative ranges are not supported."
    )
    assert (
        exceed_max_range_error.value.message
        == f"Range ending with {6 * 60 * 1000} is invalid. This audio file is only {5 * 60 * 1000} ms long."
    )


def test_remove_object_from_ranges_on_audio_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")
    new_object_instance = audio_obj_ontology_item.create_instance()

    audio_space_1.put_object_instance(object_instance=new_object_instance, ranges=Range(start=100, end=500))

    # Act
    removed_ranges = audio_space_1.remove_object_instance_from_range(
        object_instance=new_object_instance, ranges=[Range(start=150, end=200), Range(start=600, end=700)]
    )
    assert removed_ranges == [Range(start=150, end=200)]

    # Assert
    object_instances = label_row.get_object_instances()
    assert len(object_instances) == 1

    objects_on_space = audio_space_1.get_object_instances()
    object_on_space = objects_on_space[0]
    assert len(objects_on_space) == 1
    assert object_on_space._spaces == {audio_space_1.space_id: audio_space_1}

    annotations_on_space = audio_space_1.get_object_instance_annotations()
    assert len(annotations_on_space) == 1

    first_annotation = annotations_on_space[0]
    assert first_annotation.frame == 0  # Frames is here for backwards compatibility
    assert first_annotation.coordinates == AudioCoordinates(
        range=[Range(start=100, end=149), Range(start=201, end=500)]
    )
    assert first_annotation.object_hash == new_object_instance.object_hash

    # Also works for annotations obtained via object_instance
    annotations_on_object = new_object_instance.get_annotations()
    assert len(annotations_on_object) == 1


def test_remove_object_from_all_ranges_on_audio_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")
    new_object_instance = audio_obj_ontology_item.create_instance()

    audio_space_1.put_object_instance(object_instance=new_object_instance, ranges=Range(start=100, end=500))

    # Act
    removed_ranges = audio_space_1.remove_object_instance_from_range(
        object_instance=new_object_instance, ranges=Range(start=100, end=500)
    )
    assert removed_ranges == [Range(start=100, end=500)]

    # Assert
    object_instances = label_row.get_object_instances()
    assert len(object_instances) == 0

    objects_on_space = audio_space_1.get_object_instances()
    assert len(objects_on_space) == 0

    annotations_on_space = audio_space_1.get_object_instance_annotations()
    assert len(annotations_on_space) == 0

    # Also works for annotations obtained via object_instance
    annotations_on_object = new_object_instance.get_annotations()
    assert len(annotations_on_object) == 0


def test_remove_object_from_audio_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")
    new_object_instance = audio_obj_ontology_item.create_instance()

    audio_space_1.put_object_instance(object_instance=new_object_instance, ranges=Range(start=0, end=100))

    # Act
    audio_space_1.remove_object_instance(
        object_hash=new_object_instance.object_hash,
    )

    # Assert
    object_instances = label_row.get_object_instances()
    assert len(object_instances) == 0

    objects_on_space = audio_space_1.get_object_instances()
    assert len(objects_on_space) == 0

    annotations_on_space = audio_space_1.get_object_instance_annotations()
    assert len(annotations_on_space) == 0

    annotations_on_object = new_object_instance.get_annotations()
    assert len(annotations_on_object) == 0


def test_add_object_to_two_spaces(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")
    audio_space_2 = label_row.get_space(id="audio-2-uuid", type_="audio")

    new_object_instance = audio_obj_ontology_item.create_instance()
    range_1 = Range(start=0, end=100)
    range_2 = Range(start=200, end=300)

    # Act
    audio_space_1.put_object_instance(
        object_instance=new_object_instance,
        ranges=range_1,
    )
    audio_space_2.put_object_instance(
        object_instance=new_object_instance,
        ranges=range_2,
    )

    # Assert
    objects = audio_space_1.get_object_instances()
    assert len(objects) == 1

    annotations_on_audio_space_1 = audio_space_1.get_object_instance_annotations()
    first_annotation_on_audio_space_1 = annotations_on_audio_space_1[0]
    assert len(annotations_on_audio_space_1) == 1
    assert first_annotation_on_audio_space_1.coordinates == AudioCoordinates(
        range=[range_1]
    )  # Coordinates here for backwards compatibility
    assert first_annotation_on_audio_space_1.ranges == [range_1]

    annotations_on_audio_space_2 = audio_space_2.get_object_instance_annotations()
    first_annotation_on_audio_space_2 = annotations_on_audio_space_2[0]
    assert len(annotations_on_audio_space_2) == 1
    assert first_annotation_on_audio_space_2.coordinates == AudioCoordinates(
        range=[range_2]
    )  # Coordinates here for backwards compatibility
    assert first_annotation_on_audio_space_2.ranges == [range_2]


def test_update_attribute_for_object_which_exist_on_two_spaces(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")
    audio_space_2 = label_row.get_space(id="audio-2-uuid", type_="audio")

    new_object_instance = audio_obj_ontology_item.create_instance()
    range_1 = Range(start=0, end=100)
    range_2 = Range(start=200, end=300)

    audio_space_1.put_object_instance(object_instance=new_object_instance, ranges=range_1)
    audio_space_2.put_object_instance(object_instance=new_object_instance, ranges=range_2)

    object_answer = new_object_instance.get_answer(attribute=audio_obj_transcription_attribute_ontology_item)
    assert object_answer is None

    # Act
    new_answer = "Hello!"
    new_object_instance.set_answer(attribute=audio_obj_transcription_attribute_ontology_item, answer=new_answer)

    # Assert
    object_answer = new_object_instance.get_answer(attribute=audio_obj_transcription_attribute_ontology_item)
    assert object_answer == new_answer

    object_on_audio_space_1 = audio_space_1.get_object_instances()[0]
    assert object_on_audio_space_1.get_answer(audio_obj_transcription_attribute_ontology_item) == new_answer

    object_on_audio_space_2 = audio_space_2.get_object_instances()[0]
    assert object_on_audio_space_2.get_answer(audio_obj_transcription_attribute_ontology_item) == new_answer

    object_answer_dict = label_row.to_encord_dict()["object_answers"]

    EXPECTED_DICT = {
        new_object_instance.object_hash: {
            "classifications": [
                {
                    "name": "Transcript",
                    "value": "transcript",
                    "answers": "Hello!",
                    "featureHash": "transcriptFeatureHash",
                    "manualAnnotation": True,
                }
            ],
            "featureHash": "KVfzNkFy",
            "objectHash": new_object_instance.object_hash,
            "createdBy": None,
            "lastEditedBy": None,
            "manualAnnotation": True,
            "name": "audio object",
            "value": "audio_object",
            "color": "#A4FF00",
            "shape": "audio",
            "spaces": {"audio-1-uuid": {"range": [[0, 100]]}, "audio-2-uuid": {"range": [[200, 300]]}},
            "range": [],
        }
    }

    assert not DeepDiff(
        object_answer_dict, EXPECTED_DICT, exclude_regex_paths=[r".*\['lastEditedAt'\]", r".*\['createdAt'\]"]
    )


def test_get_object_annotations(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")
    object_instance_1 = audio_obj_ontology_item.create_instance()
    object_instance_2 = audio_obj_ontology_item.create_instance()

    range_1 = Range(start=0, end=100)
    range_2 = Range(start=200, end=300)

    name_1 = "james"
    name_2 = "timmy"

    date1 = datetime(2020, 1, 1)
    date2 = datetime(2020, 5, 5)

    audio_space_1.put_object_instance(
        object_instance=object_instance_1,
        ranges=range_1,
        last_edited_by=name_1,
        last_edited_at=date1,
    )

    audio_space_1.put_object_instance(
        object_instance=object_instance_2,
        ranges=range_2,
        last_edited_by=name_2,
        last_edited_at=date2,
    )

    # Act
    object_annotations = audio_space_1.get_object_instance_annotations()
    first_annotation = object_annotations[0]
    second_annotation = object_annotations[1]

    # Assert
    assert len(object_annotations) == 2

    assert first_annotation.space.space_id == "audio-1-uuid"
    assert first_annotation.frame == 0  # Frame here for backwards compatibility
    assert first_annotation.object_hash == object_instance_1.object_hash
    assert first_annotation.coordinates == AudioCoordinates(
        range=[range_1]
    )  # Coordinates here for backwards compatibility
    assert first_annotation.last_edited_by == name_1
    assert first_annotation.last_edited_at == date1

    assert second_annotation.space.space_id == "audio-1-uuid"
    assert second_annotation.frame == 0  # Frame here for backwards compatibility
    assert second_annotation.object_hash == object_instance_2.object_hash
    assert second_annotation.coordinates == AudioCoordinates(
        range=[range_2]
    )  # Coordinates here for backwards compatibility
    assert second_annotation.last_edited_by == name_2
    assert second_annotation.last_edited_at == date2


def test_get_object_annotations_with_filter_objects(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")
    object_instance_1 = audio_obj_ontology_item.create_instance()
    object_instance_2 = audio_obj_ontology_item.create_instance()

    range_1 = Range(start=0, end=100)
    range_2 = Range(start=200, end=300)

    name_1 = "james"
    name_2 = "timmy"

    date1 = datetime(2020, 1, 1)
    date2 = datetime(2020, 5, 5)

    audio_space_1.put_object_instance(
        object_instance=object_instance_1,
        ranges=range_1,
        last_edited_by=name_1,
        last_edited_at=date1,
    )

    audio_space_1.put_object_instance(
        object_instance=object_instance_2,
        ranges=range_2,
        last_edited_by=name_2,
        last_edited_at=date2,
    )

    # Act
    object_annotations_for_object_1 = audio_space_1.get_object_instance_annotations(
        filter_object_instances=[object_instance_1.object_hash]
    )
    first_annotation_for_object_1 = object_annotations_for_object_1[0]

    object_annotations_for_object_2 = audio_space_1.get_object_instance_annotations(
        filter_object_instances=[object_instance_2.object_hash]
    )
    first_annotation_for_object_2 = object_annotations_for_object_2[0]

    # Assert
    assert len(object_annotations_for_object_1) == 1
    assert first_annotation_for_object_1.space.space_id == "audio-1-uuid"
    assert first_annotation_for_object_1.frame == 0  # Frame here for backwards compatibility
    assert first_annotation_for_object_1.object_hash == object_instance_1.object_hash
    assert first_annotation_for_object_1.ranges == [range_1]
    assert first_annotation_for_object_1.coordinates == AudioCoordinates(
        range=[range_1]
    )  # Coordinates here for backwards compatibility
    assert first_annotation_for_object_1.last_edited_by == name_1
    assert first_annotation_for_object_1.last_edited_at == date1

    assert len(object_annotations_for_object_2) == 1
    assert first_annotation_for_object_2.space.space_id == "audio-1-uuid"
    assert first_annotation_for_object_2.frame == 0  # Frame here for backwards compatibility
    assert first_annotation_for_object_2.object_hash == object_instance_2.object_hash
    assert first_annotation_for_object_2.ranges == [range_2]
    assert first_annotation_for_object_2.coordinates == AudioCoordinates(
        range=[range_2]
    )  # Coordinates here for backwards compatibility
    assert first_annotation_for_object_2.last_edited_by == name_2
    assert first_annotation_for_object_2.last_edited_at == date2


def test_get_object_annotations_from_object_instance(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")
    object_instance_1 = audio_obj_ontology_item.create_instance()
    object_instance_2 = audio_obj_ontology_item.create_instance()

    range_1 = Range(start=0, end=100)
    range_2 = Range(start=200, end=300)

    name_1 = "james"
    name_2 = "timmy"

    date1 = datetime(2020, 1, 1)
    date2 = datetime(2020, 5, 5)

    audio_space_1.put_object_instance(
        object_instance=object_instance_1,
        ranges=range_1,
        last_edited_by=name_1,
        last_edited_at=date1,
    )

    audio_space_1.put_object_instance(
        object_instance=object_instance_2,
        ranges=range_2,
        last_edited_by=name_2,
        last_edited_at=date2,
    )

    # Act
    object_annotations_for_object_1 = object_instance_1.get_annotations()
    first_annotation_for_object_1 = object_annotations_for_object_1[0]

    object_annotations_for_object_2 = object_instance_2.get_annotations()
    first_annotation_for_object_2 = object_annotations_for_object_2[0]

    # Assert
    assert len(object_annotations_for_object_1) == 1
    assert first_annotation_for_object_1.space.space_id == "audio-1-uuid"
    assert first_annotation_for_object_1.frame == 0  # Frame here for backwards compatibility
    assert first_annotation_for_object_1.object_hash == object_instance_1.object_hash
    assert first_annotation_for_object_1.ranges == [range_1]
    assert first_annotation_for_object_1.coordinates == AudioCoordinates(
        range=[range_1]
    )  # Coordinates here for backwards compatibility
    assert first_annotation_for_object_1.last_edited_by == name_1
    assert first_annotation_for_object_1.last_edited_at == date1

    assert len(object_annotations_for_object_2) == 1
    assert first_annotation_for_object_2.space.space_id == "audio-1-uuid"
    assert first_annotation_for_object_2.frame == 0  # Frame here for backwards compatibility
    assert first_annotation_for_object_2.object_hash == object_instance_2.object_hash
    assert first_annotation_for_object_2.ranges == [range_2]
    assert first_annotation_for_object_2.coordinates == AudioCoordinates(
        range=[range_2]
    )  # Coordinates here for backwards compatibility
    assert first_annotation_for_object_2.last_edited_by == name_2
    assert first_annotation_for_object_2.last_edited_at == date2


def test_update_annotation_from_object_annotation_using_coordinates(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")
    object_instance = audio_obj_ontology_item.create_instance()

    current_range = Range(start=0, end=100)
    new_range = Range(start=200, end=300)

    name = "james@encord.com"
    new_name = "timmy@encord.com"

    date = datetime(2020, 1, 1)
    new_date = datetime(2020, 5, 5)

    audio_space_1.put_object_instance(
        object_instance=object_instance,
        ranges=current_range,
        last_edited_by=name,
        last_edited_at=date,
        created_at=date,
    )

    current_label_row_dict = label_row.to_encord_dict()
    current_object_answers_dict = current_label_row_dict["object_answers"]

    EXPECTED_CURRENT_OBJECT_ANSWERS_DICT = {
        object_instance.object_hash: {
            "objectHash": object_instance.object_hash,
            "featureHash": "KVfzNkFy",
            "name": "audio object",
            "value": "audio_object",
            "color": "#A4FF00",
            "createdBy": None,
            "createdAt": format_datetime_to_long_string(date),
            "lastEditedAt": format_datetime_to_long_string(date),
            "lastEditedBy": name,
            "manualAnnotation": True,
            "shape": "audio",
            "classifications": [],
            "range": [],
            "spaces": {
                "audio-1-uuid": {
                    "range": [[0, 100]],
                }
            },
        },
    }

    assert not DeepDiff(current_object_answers_dict, EXPECTED_CURRENT_OBJECT_ANSWERS_DICT)

    # Act
    object_annotations = audio_space_1.get_object_instance_annotations()
    object_annotation = object_annotations[0]

    object_annotation.created_by = new_name
    object_annotation.created_at = new_date
    object_annotation.last_edited_by = new_name
    object_annotation.last_edited_at = new_date
    object_annotation.coordinates = AudioCoordinates(
        range=[new_range]
    )  # This is a backwards compatible flow. Should change it via object_annotation.ranges

    # Assert
    new_label_row_dict = label_row.to_encord_dict()
    new_object_answers_dict = new_label_row_dict["object_answers"]

    EXPECTED_NEW_OBJECT_ANSWERS_DICT = {
        object_instance.object_hash: {
            "objectHash": object_instance.object_hash,
            "featureHash": "KVfzNkFy",
            "name": "audio object",
            "value": "audio_object",
            "color": "#A4FF00",
            "createdBy": new_name,
            "createdAt": format_datetime_to_long_string(new_date),
            "lastEditedAt": format_datetime_to_long_string(new_date),
            "lastEditedBy": new_name,
            "manualAnnotation": True,
            "shape": "audio",
            "classifications": [],
            "range": [],
            "spaces": {
                "audio-1-uuid": {
                    "range": [[200, 300]],
                }
            },
        },
    }
    assert not DeepDiff(new_object_answers_dict, EXPECTED_NEW_OBJECT_ANSWERS_DICT)


def test_update_annotation_from_object_annotation(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_AUDIO_NO_LABELS)
    audio_space_1 = label_row.get_space(id="audio-1-uuid", type_="audio")
    object_instance = audio_obj_ontology_item.create_instance()

    current_range = Range(start=0, end=100)
    new_range = Range(start=200, end=300)

    name = "james@encord.com"
    new_name = "timmy@encord.com"

    date = datetime(2020, 1, 1)
    new_date = datetime(2020, 5, 5)

    audio_space_1.put_object_instance(
        object_instance=object_instance,
        ranges=current_range,
        last_edited_by=name,
        last_edited_at=date,
        created_at=date,
    )

    current_label_row_dict = label_row.to_encord_dict()
    current_object_answers_dict = current_label_row_dict["object_answers"]

    EXPECTED_CURRENT_OBJECT_ANSWERS_DICT = {
        object_instance.object_hash: {
            "objectHash": object_instance.object_hash,
            "featureHash": "KVfzNkFy",
            "name": "audio object",
            "value": "audio_object",
            "color": "#A4FF00",
            "createdBy": None,
            "createdAt": format_datetime_to_long_string(date),
            "lastEditedAt": format_datetime_to_long_string(date),
            "lastEditedBy": name,
            "manualAnnotation": True,
            "shape": "audio",
            "classifications": [],
            "range": [],
            "spaces": {
                "audio-1-uuid": {
                    "range": [[0, 100]],
                }
            },
        },
    }

    assert not DeepDiff(current_object_answers_dict, EXPECTED_CURRENT_OBJECT_ANSWERS_DICT)

    # Act
    object_annotations = audio_space_1.get_object_instance_annotations()
    object_annotation = object_annotations[0]

    object_annotation.created_by = new_name
    object_annotation.created_at = new_date
    object_annotation.last_edited_by = new_name
    object_annotation.last_edited_at = new_date
    object_annotation.ranges = new_range

    # Assert
    new_label_row_dict = label_row.to_encord_dict()
    new_object_answers_dict = new_label_row_dict["object_answers"]

    EXPECTED_NEW_OBJECT_ANSWERS_DICT = {
        object_instance.object_hash: {
            "objectHash": object_instance.object_hash,
            "featureHash": "KVfzNkFy",
            "name": "audio object",
            "value": "audio_object",
            "color": "#A4FF00",
            "createdBy": new_name,
            "createdAt": format_datetime_to_long_string(new_date),
            "lastEditedAt": format_datetime_to_long_string(new_date),
            "lastEditedBy": new_name,
            "manualAnnotation": True,
            "shape": "audio",
            "classifications": [],
            "range": [],
            "spaces": {
                "audio-1-uuid": {
                    "range": [[200, 300]],
                }
            },
        },
    }
    assert not DeepDiff(new_object_answers_dict, EXPECTED_NEW_OBJECT_ANSWERS_DICT)
