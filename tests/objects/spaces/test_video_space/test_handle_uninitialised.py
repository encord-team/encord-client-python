"""Tests for ensuring all public API methods check if labelling is initialised before proceeding."""

from unittest.mock import Mock

import pytest

from encord.exceptions import LabelRowError
from encord.objects import LabelRowV2, Object
from encord.objects.attributes import Attribute, TextAttribute
from encord.objects.coordinates import BoundingBoxCoordinates
from encord.objects.ontology_labels_impl import LABELLING_NOT_INITIALISED_ERROR_MESSAGE
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.two_videos import (
    DATA_GROUP_METADATA,
)

box_ontology_item = all_types_structure.get_child_by_hash("MjI2NzEy", Object)
box_with_attributes_ontology_item = all_types_structure.get_child_by_hash("MTA2MjAx", Object)
box_text_attribute_ontology_item = box_with_attributes_ontology_item.get_child_by_hash("OTkxMjU1", type_=Attribute)


@pytest.fixture
def uninitialised_video_space(ontology):
    """Create a label row with uninitialised labelling and return a video space."""
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)

    return label_row._get_space(id="video-1-uuid", type_="video")


def test_put_object_instance_requires_initialisation(uninitialised_video_space):
    """Test that put_object_instance checks if labelling is initialised."""
    new_object_instance = box_ontology_item.create_instance()

    with pytest.raises(LabelRowError) as exc_info:
        uninitialised_video_space.put_object_instance(
            object_instance=new_object_instance,
            frames=[1],
            coordinates=BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0),
        )

    assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE


def test_remove_object_instance_from_frames_requires_initialisation(uninitialised_video_space):
    """Test that remove_object_instance_from_frames checks if labelling is initialised."""
    new_object_instance = box_ontology_item.create_instance()

    with pytest.raises(LabelRowError) as exc_info:
        uninitialised_video_space.remove_object_instance_from_frames(
            object_instance=new_object_instance,
            frames=[1],
        )

    assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE


def test_set_answer_on_frames_requires_initialisation(uninitialised_video_space):
    """Test that set_answer_on_frames checks if labelling is initialised."""
    # Create an object instance with a dynamic text attribute
    new_object_instance = box_with_attributes_ontology_item.create_instance()

    with pytest.raises(LabelRowError) as exc_info:
        uninitialised_video_space.set_answer_on_frames(
            object_instance=new_object_instance,
            frames=[1],
            answer="test answer",
            attribute=box_text_attribute_ontology_item,
        )

    assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE


def test_remove_answer_from_frame_requires_initialisation(uninitialised_video_space):
    """Test that remove_answer_from_frame checks if labelling is initialised."""
    new_object_instance = box_with_attributes_ontology_item.create_instance()

    with pytest.raises(LabelRowError) as exc_info:
        uninitialised_video_space.remove_answer_from_frame(
            object_instance=new_object_instance,
            attribute=box_text_attribute_ontology_item,
            frame=1,
        )

    assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE


def test_get_answer_on_frames_requires_initialisation(uninitialised_video_space):
    """Test that get_answer_on_frames checks if labelling is initialised."""
    new_object_instance = box_with_attributes_ontology_item.create_instance()

    with pytest.raises(LabelRowError) as exc_info:
        uninitialised_video_space.get_answer_on_frames(
            object_instance=new_object_instance,
            frames=[1],
            attribute=box_text_attribute_ontology_item,
        )

    assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE


def test_put_classification_instance_requires_initialisation(uninitialised_video_space, ontology):
    """Test that put_classification_instance checks if labelling is initialised."""
    from encord.objects import Classification

    text_classification = all_types_structure.get_child_by_hash("jPOcEsbw", Classification)
    classification_instance = text_classification.create_instance()

    # Set a required answer if needed
    if text_classification.attributes:
        first_attribute = text_classification.attributes[0]
        if isinstance(first_attribute, TextAttribute):
            classification_instance.set_answer("test", first_attribute)

    with pytest.raises(LabelRowError) as exc_info:
        uninitialised_video_space.put_classification_instance(
            classification_instance=classification_instance,
            frames=[1],
        )

    assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE


def test_remove_classification_instance_from_frames_requires_initialisation(uninitialised_video_space, ontology):
    """Test that remove_classification_instance_from_frames checks if labelling is initialised."""
    from encord.objects import Classification

    text_classification = all_types_structure.get_child_by_hash("jPOcEsbw", Classification)
    classification_instance = text_classification.create_instance()

    with pytest.raises(LabelRowError) as exc_info:
        uninitialised_video_space.remove_classification_instance_from_frames(
            classification_instance=classification_instance,
            frames=[1],
        )

    assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE


def test_get_object_instance_annotations_requires_initialisation(uninitialised_video_space):
    """Test that get_object_instance_annotations checks if labelling is initialised."""
    with pytest.raises(LabelRowError) as exc_info:
        uninitialised_video_space.get_object_instance_annotations()

    assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE


def test_get_object_instance_annotations_by_frame_requires_initialisation(uninitialised_video_space):
    """Test that get_object_instance_annotations_by_frame checks if labelling is initialised."""
    with pytest.raises(LabelRowError) as exc_info:
        uninitialised_video_space.get_object_instance_annotations_by_frame()

    assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE


def test_get_classification_instance_annotations_requires_initialisation(uninitialised_video_space):
    """Test that get_classification_instance_annotations checks if labelling is initialised."""
    with pytest.raises(LabelRowError) as exc_info:
        uninitialised_video_space.get_classification_instance_annotations()

    assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE


def test_remove_object_instance_requires_initialisation(uninitialised_video_space):
    """Test that remove_object_instance checks if labelling is initialised."""
    new_object_instance = box_ontology_item.create_instance()

    with pytest.raises(LabelRowError) as exc_info:
        uninitialised_video_space.remove_object_instance(
            object_hash=new_object_instance.object_hash,
        )

    assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE


def test_remove_classification_instance_requires_initialisation(uninitialised_video_space, ontology):
    """Test that remove_classification_instance checks if labelling is initialised."""
    from encord.objects import Classification

    text_classification = all_types_structure.get_child_by_hash("jPOcEsbw", Classification)
    classification_instance = text_classification.create_instance()

    with pytest.raises(LabelRowError) as exc_info:
        uninitialised_video_space.remove_classification_instance(
            classification_hash=classification_instance.classification_hash,
        )

    assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE
