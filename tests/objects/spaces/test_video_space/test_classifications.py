from datetime import datetime
from unittest.mock import Mock

import pytest
from deepdiff import DeepDiff

from encord.common.time_parser import format_datetime_to_long_string
from encord.exceptions import LabelRowError
from encord.objects import Classification, LabelRowV2, Object
from encord.objects.attributes import Attribute
from encord.objects.frames import Range
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.two_videos import (
    DATA_GROUP_METADATA,
    DATA_GROUP_TWO_VIDEOS_NO_LABELS,
)

box_ontology_item = all_types_structure.get_child_by_hash("MjI2NzEy", Object)
box_with_attributes_ontology_item = all_types_structure.get_child_by_hash("MTA2MjAx", Object)
box_text_attribute_ontology_item = box_with_attributes_ontology_item.get_child_by_hash("OTkxMjU1", type_=Attribute)
text_classification = all_types_structure.get_child_by_hash("jPOcEsbw", Classification)
checklist_classification = all_types_structure.get_child_by_hash("3DuQbFxo", Classification)


@pytest.fixture
def ontology():
    ontology_structure = Mock()
    ontology_structure.get_child_by_hash = all_types_structure.get_child_by_hash
    ontology = Mock(structure=ontology_structure)
    yield ontology


def test_label_row_get_classification_instances_on_video_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")
    video_space_2 = label_row.get_space(id="video-2-uuid", type_="video")

    # Act
    classification_instance_1 = text_classification.create_instance()
    classification_instance_2 = checklist_classification.create_instance()

    # Place classification on space 1
    video_space_1.put_classification_instance(classification_instance=classification_instance_1, frames=[0, 1, 2])
    video_space_1.put_classification_instance(classification_instance=classification_instance_2, frames=[2, 3, 4])

    # Place classification on space 2
    video_space_2.put_classification_instance(classification_instance=classification_instance_1, frames=[1])

    # Assert
    all_classification_instances = label_row.get_classification_instances()
    assert len(all_classification_instances) == 2

    classification_instances_on_frame_1 = label_row.get_classification_instances(filter_frames=1)
    assert len(classification_instances_on_frame_1) == 1


def test_place_classification_on_video_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")

    # Act
    new_classification_instance = text_classification.create_instance()
    video_space_1.put_classification_instance(classification_instance=new_classification_instance, frames=[1])
    video_space_1.put_classification_instance(classification_instance=new_classification_instance, frames=[0, 2, 3])

    text_answer = "Some answer"
    new_classification_instance.set_answer(answer=text_answer)

    # Assert
    classifications_on_label_row = label_row.get_classification_instances()
    assert len(classifications_on_label_row) == 1

    classifications_on_space = video_space_1.get_classification_instances()
    classification_on_space = classifications_on_space[0]
    assert len(classifications_on_space) == 1
    assert classification_on_space._spaces == {video_space_1.space_id: video_space_1}

    annotations = video_space_1.get_classification_instance_annotations()
    assert len(annotations) == 4

    first_annotation = annotations[0]
    assert first_annotation.frame == 0
    assert first_annotation.classification_hash == new_classification_instance.classification_hash

    classification_answers_dict = label_row.to_encord_dict()["classification_answers"]
    expected_dict = {
        new_classification_instance.classification_hash: {
            "classifications": [
                {
                    "name": "Text classification",
                    "value": "text_classification",
                    "answers": text_answer,
                    "featureHash": "OxrtEM+v",
                    "manualAnnotation": True,
                }
            ],
            "classificationHash": new_classification_instance.classification_hash,
            "featureHash": "jPOcEsbw",
        }
    }

    assert not DeepDiff(classification_answers_dict, expected_dict)


def test_place_classification_on_frame_where_classification_exists_video_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")

    classification_instance_1 = text_classification.create_instance()
    classification_instance_2 = text_classification.create_instance()
    text_answer_1 = "Answer 1"
    text_answer_2 = "Answer 2"

    classification_instance_1.set_answer(answer=text_answer_1)
    classification_instance_2.set_answer(answer=text_answer_2)

    video_space_1.put_classification_instance(classification_instance=classification_instance_1, frames=[0, 1, 2])

    # Act
    with pytest.raises(LabelRowError) as e:
        video_space_1.put_classification_instance(classification_instance=classification_instance_2, frames=[1])

    # Assert
    assert (
        e.value.message
        == f"The classification '{classification_instance_2.classification_hash}' already exists on the ranges {[Range(start=1, end=1)]}. Set 'on_overlap' parameter to 'replace' to overwrite."
    )


def test_place_classification_on_frames_with_overwrite_on_video_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")

    classification_instance_1 = text_classification.create_instance()
    classification_instance_2 = text_classification.create_instance()
    text_answer_1 = "Answer 1"
    text_answer_2 = "Answer 2"

    classification_instance_1.set_answer(answer=text_answer_1)
    classification_instance_2.set_answer(answer=text_answer_2)

    video_space_1.put_classification_instance(classification_instance=classification_instance_1, frames=[0, 1, 2])

    # Act
    video_space_1.put_classification_instance(
        classification_instance=classification_instance_2, frames=[1], overwrite=True
    )

    annotations_on_classifications = video_space_1.get_classification_instance_annotations()

    assert len(annotations_on_classifications) == 3
    annotation_on_frame_0 = annotations_on_classifications[0]
    assert annotation_on_frame_0.frame == 0
    assert annotation_on_frame_0.classification_hash == classification_instance_1.classification_hash

    annotation_on_frame_1 = annotations_on_classifications[1]
    assert annotation_on_frame_1.frame == 1
    assert annotation_on_frame_1.classification_hash == classification_instance_2.classification_hash


def test_place_classification_on_invalid_frames(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")

    classification_instance_1 = text_classification.create_instance()

    # Act
    with pytest.raises(LabelRowError) as negative_frame_error:
        video_space_1.put_classification_instance(classification_instance=classification_instance_1, frames=[-1])

    with pytest.raises(LabelRowError) as exceed_frame_error:
        video_space_1.put_classification_instance(classification_instance=classification_instance_1, frames=[100])

    # Assert
    assert negative_frame_error.value.message == "Frame -1 is invalid. Negative frames are not supported."
    assert exceed_frame_error.value.message == "Frame 100 is invalid. The max frame on this video is 9."


def test_unplace_classification_from_frames_on_video_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")

    new_classification_instance = text_classification.create_instance()
    video_space_1.put_classification_instance(classification_instance=new_classification_instance, frames=[0, 1, 2])

    annotations_before_removing = video_space_1.get_classification_instance_annotations()
    annotation_to_be_removed = annotations_before_removing[1]

    assert len(annotations_before_removing) == 3
    assert annotation_to_be_removed.frame == 1

    # Act
    video_space_1.remove_classification_instance_from_frames(
        classification_instance=new_classification_instance, frames=[1]
    )

    # Assert
    annotations_after_removing = video_space_1.get_classification_instance_annotations()
    assert len(annotations_after_removing) == 2

    annotations_on_classification_after_removing = new_classification_instance.get_annotations()
    assert len(annotations_on_classification_after_removing) == 2

    with pytest.raises(LabelRowError):
        assert annotation_to_be_removed.created_by


def test_remove_classification_from_video_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")

    new_classification_instance = text_classification.create_instance()
    video_space_1.put_classification_instance(classification_instance=new_classification_instance, frames=[0, 2, 3])
    classifications_on_space = video_space_1.get_classification_instances()
    assert len(classifications_on_space) == 1
    annotations = video_space_1.get_classification_instance_annotations()
    assert len(annotations) == 3

    # Act
    video_space_1.remove_classification_instance(new_classification_instance.classification_hash)

    # Assert
    classifications_on_label_row = label_row.get_classification_instances()
    assert len(classifications_on_label_row) == 0

    classifications_on_space = video_space_1.get_classification_instances()
    assert len(classifications_on_space) == 0

    annotations = video_space_1.get_classification_instance_annotations()
    assert len(annotations) == 0


def test_get_classification_annotations(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")
    new_classification_instance = text_classification.create_instance()

    name_1 = "james"
    name_2 = "timmy"

    date1 = datetime(2020, 1, 1)
    date2 = datetime(2020, 5, 5)

    video_space_1.put_classification_instance(
        classification_instance=new_classification_instance,
        frames=[1],
        last_edited_by=name_1,
        last_edited_at=date1,
    )

    video_space_1.put_classification_instance(
        classification_instance=new_classification_instance,
        frames=[0, 2, 3],
        last_edited_by=name_2,
        last_edited_at=date2,
    )

    # Act
    classification_annotations = video_space_1.get_classification_instance_annotations()
    first_annotation = classification_annotations[0]
    second_annotation = classification_annotations[1]

    # Assert
    assert len(classification_annotations) == 4

    assert first_annotation.space.space_id == "video-1-uuid"
    assert first_annotation.frame == 0
    assert first_annotation.classification_hash == new_classification_instance.classification_hash
    assert first_annotation.last_edited_by == name_2
    assert first_annotation.last_edited_at == date2

    assert second_annotation.space.space_id == "video-1-uuid"
    assert second_annotation.frame == 1
    assert second_annotation.classification_hash == new_classification_instance.classification_hash
    assert second_annotation.last_edited_by == name_1
    assert second_annotation.last_edited_at == date1


def test_get_classification_annotations_with_filter_classifications(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")
    classification_instance_1 = text_classification.create_instance()
    classification_instance_2 = text_classification.create_instance()

    name_1 = "james"
    name_2 = "timmy"

    date1 = datetime(2020, 1, 1)
    date2 = datetime(2020, 5, 5)

    video_space_1.put_classification_instance(
        classification_instance=classification_instance_1,
        frames=[0, 1, 2],
        last_edited_by=name_1,
        last_edited_at=date1,
    )

    video_space_1.put_classification_instance(
        classification_instance=classification_instance_2,
        frames=[4, 5],
        last_edited_by=name_2,
        last_edited_at=date2,
    )

    # Act
    annotations_for_classification_1 = video_space_1.get_classification_instance_annotations(
        filter_classification_instances=[classification_instance_1.classification_hash]
    )
    first_annotation_for_classification_1 = annotations_for_classification_1[0]

    annotations_for_classification_2 = video_space_1.get_classification_instance_annotations(
        filter_classification_instances=[classification_instance_2.classification_hash]
    )
    first_annotation_for_classification_2 = annotations_for_classification_2[0]

    # Assert
    assert len(annotations_for_classification_1) == 3
    assert first_annotation_for_classification_2.space.space_id == "video-1-uuid"
    assert first_annotation_for_classification_1.frame == 0
    assert first_annotation_for_classification_1.classification_hash == classification_instance_1.classification_hash
    assert first_annotation_for_classification_1.last_edited_by == name_1
    assert first_annotation_for_classification_1.last_edited_at == date1

    assert len(annotations_for_classification_2) == 2
    assert first_annotation_for_classification_2.space.space_id == "video-1-uuid"
    assert first_annotation_for_classification_2.frame == 4
    assert first_annotation_for_classification_2.classification_hash == classification_instance_2.classification_hash
    assert first_annotation_for_classification_2.last_edited_by == name_2
    assert first_annotation_for_classification_2.last_edited_at == date2


def test_get_classification_annotations_from_classification_instance(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")
    classification_instance_1 = text_classification.create_instance()
    classification_instance_2 = text_classification.create_instance()

    name_1 = "james"
    name_2 = "timmy"

    date1 = datetime(2020, 1, 1)
    date2 = datetime(2020, 5, 5)

    video_space_1.put_classification_instance(
        classification_instance=classification_instance_1,
        frames=[0, 1, 2],
        last_edited_by=name_1,
        last_edited_at=date1,
    )

    video_space_1.put_classification_instance(
        classification_instance=classification_instance_2,
        frames=[4, 5],
        last_edited_by=name_2,
        last_edited_at=date2,
    )

    # Act
    annotations_for_classification_1 = classification_instance_1.get_annotations()
    first_annotation_for_classification_1 = annotations_for_classification_1[0]

    annotations_for_classification_2 = classification_instance_2.get_annotations()
    first_annotation_for_classification_2 = annotations_for_classification_2[0]

    # Assert
    assert len(annotations_for_classification_1) == 3
    assert first_annotation_for_classification_2.space.space_id == "video-1-uuid"
    assert first_annotation_for_classification_1.frame == 0
    assert first_annotation_for_classification_1.classification_hash == classification_instance_1.classification_hash
    assert first_annotation_for_classification_1.last_edited_by == name_1
    assert first_annotation_for_classification_1.last_edited_at == date1

    assert len(annotations_for_classification_2) == 2
    assert first_annotation_for_classification_2.space.space_id == "video-1-uuid"
    assert first_annotation_for_classification_2.frame == 4
    assert first_annotation_for_classification_2.classification_hash == classification_instance_2.classification_hash
    assert first_annotation_for_classification_2.last_edited_by == name_2
    assert first_annotation_for_classification_2.last_edited_at == date2


def test_update_annotation_from_object_annotation(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")
    classification_instance_1 = text_classification.create_instance()

    name = "james@encord.com"
    new_name = "timmy@encord.com"

    date = datetime(2020, 1, 1)
    new_date = datetime(2020, 5, 5)

    video_space_1.put_classification_instance(
        classification_instance=classification_instance_1,
        frames=[1],
        created_at=date,
        last_edited_by=name,
        last_edited_at=date,
    )

    current_label_row_dict = label_row.to_encord_dict()
    current_frame_dict = current_label_row_dict["spaces"]["video-1-uuid"]["labels"]

    EXPECTED_CURRENT_LABELS_DICT = {
        "1": {
            "objects": [],
            "classifications": [
                {
                    "classificationHash": classification_instance_1.classification_hash,
                    "featureHash": "jPOcEsbw",
                    "name": "Text classification",
                    "value": "text_classification",
                    "createdAt": format_datetime_to_long_string(date),
                    "confidence": 1.0,
                    "manualAnnotation": True,
                    "lastEditedAt": format_datetime_to_long_string(date),
                    "lastEditedBy": name,
                }
            ],
        }
    }
    assert not DeepDiff(current_frame_dict, EXPECTED_CURRENT_LABELS_DICT)

    # Act
    classification_annotations = video_space_1.get_classification_instance_annotations()
    classification_annotation = classification_annotations[0]

    classification_annotation.created_by = new_name
    classification_annotation.created_at = new_date
    classification_annotation.last_edited_by = new_name
    classification_annotation.last_edited_at = new_date

    # Assert
    new_label_row_dict = label_row.to_encord_dict()
    new_frame_dict = new_label_row_dict["spaces"]["video-1-uuid"]["labels"]

    EXPECTED_NEW_LABELS_DICT = {
        "1": {
            "objects": [],
            "classifications": [
                {
                    "classificationHash": classification_instance_1.classification_hash,
                    "featureHash": "jPOcEsbw",
                    "name": "Text classification",
                    "value": "text_classification",
                    "createdAt": format_datetime_to_long_string(new_date),
                    "createdBy": new_name,
                    "confidence": 1.0,
                    "manualAnnotation": True,
                    "lastEditedAt": format_datetime_to_long_string(new_date),
                    "lastEditedBy": new_name,
                }
            ],
        }
    }
    assert not DeepDiff(new_frame_dict, EXPECTED_NEW_LABELS_DICT)
