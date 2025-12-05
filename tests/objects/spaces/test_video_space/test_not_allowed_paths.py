from unittest.mock import Mock

import pytest

from encord.exceptions import LabelRowError
from encord.objects import Classification, LabelRowV2, Object
from encord.objects.attributes import Attribute
from encord.objects.coordinates import BoundingBoxCoordinates, PointCoordinate
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.two_videos import (
    DATA_GROUP_METADATA,
    DATA_GROUP_TWO_VIDEOS_NO_LABELS,
)

box_ontology_item = all_types_structure.get_child_by_hash("MjI2NzEy", Object)
box_with_attributes_ontology_item = all_types_structure.get_child_by_hash("MTA2MjAx", Object)
box_text_attribute_ontology_item = box_with_attributes_ontology_item.get_child_by_hash("OTkxMjU1", type_=Attribute)
text_classification = all_types_structure.get_child_by_hash("jPOcEsbw", Classification)
keypoint_with_dynamic_attributes_ontology_item = all_types_structure.get_child_by_hash("MTY2MTQx", Object)
key_point_dynamic_text_attribute = keypoint_with_dynamic_attributes_ontology_item.get_child_by_hash(
    "OTkxMjU1", type_=Attribute
)


@pytest.fixture
def ontology():
    ontology_structure = Mock()
    ontology_structure.get_child_by_hash = all_types_structure.get_child_by_hash
    ontology = Mock(structure=ontology_structure)
    yield ontology


def test_place_object_on_video_space_throws_error_if_object_has_frames(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")
    new_object_instance = box_ontology_item.create_instance()
    box_coordinates = BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0)
    new_object_instance.set_for_frames(frames=0, coordinates=box_coordinates)

    # Act
    with pytest.raises(LabelRowError) as e:
        video_space_1.put_object_instance(
            object_instance=new_object_instance,
            frames=[1],
            coordinates=box_coordinates,
        )

    assert (
        e.value.message
        == "Object instance contains frames data. Ensure ObjectInstance.set_for_frames was not used before calling this method. "
    )


def test_unplace_object_on_video_space_throws_error_if_object_has_frames(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")
    new_object_instance = box_ontology_item.create_instance()
    box_coordinates = BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0)
    new_object_instance.set_for_frames(frames=0, coordinates=box_coordinates)

    # Act
    with pytest.raises(LabelRowError) as e:
        video_space_1.remove_object_instance_from_frames(
            object_instance=new_object_instance,
            frames=[1],
        )

    assert (
        e.value.message
        == "Object instance contains frames data. Ensure ObjectInstance.set_for_frames was not used before calling this method. "
    )


def test_add_object_to_label_row_throws_error_if_object_is_on_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")
    new_object_instance = box_ontology_item.create_instance()
    box_coordinates = BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0)
    video_space_1.put_object_instance(
        object_instance=new_object_instance,
        frames=[1],
        coordinates=box_coordinates,
    )

    # Act
    with pytest.raises(LabelRowError) as e:
        label_row.add_object_instance(object_instance=new_object_instance)

    assert (
        e.value.message
        == "Object instance already exists on a space. It cannot be placed directly onto the label row. Please use Space.place_object instead."
    )


def test_remove_object_from_label_row_throws_error_if_object_is_on_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")
    new_object_instance = box_ontology_item.create_instance()
    box_coordinates = BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0)
    video_space_1.put_object_instance(
        object_instance=new_object_instance,
        frames=[1],
        coordinates=box_coordinates,
    )

    # Act
    with pytest.raises(LabelRowError) as e:
        label_row.remove_object(object_instance=new_object_instance)

    assert (
        e.value.message
        == "Object instance already exists on a space. It cannot be removed directly from the label row. Please use Space.remove_object instead."
    )


def test_set_for_frames_throws_error_if_object_is_on_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")
    new_object_instance = box_ontology_item.create_instance()
    box_coordinates = BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0)
    video_space_1.put_object_instance(
        object_instance=new_object_instance,
        frames=[1],
        coordinates=box_coordinates,
    )

    # Act
    with pytest.raises(LabelRowError) as e:
        new_object_instance.set_for_frames(frames=0, coordinates=box_coordinates)

    assert (
        e.value.message
        == "This operation is not allowed for objects that exist on a space.For adding the object to different frames on a space, use Space.place_object."
    )


def test_remove_from_frames_throws_error_if_object_is_on_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")
    new_object_instance = box_ontology_item.create_instance()
    box_coordinates = BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0)
    video_space_1.put_object_instance(
        object_instance=new_object_instance,
        frames=[1],
        coordinates=box_coordinates,
    )

    # Act
    with pytest.raises(LabelRowError) as e:
        new_object_instance.remove_from_frames(frames=0)

    assert (
        e.value.message
        == "This operation is not allowed for objects that exist on a space.For removing the object from different frames on a space, use Space.unplace_object."
    )


def test_get_annotation_throws_error_if_object_is_on_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")
    new_object_instance = box_ontology_item.create_instance()
    box_coordinates = BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0)
    video_space_1.put_object_instance(
        object_instance=new_object_instance,
        frames=[1],
        coordinates=box_coordinates,
    )

    # Act
    with pytest.raises(LabelRowError) as e:
        new_object_instance.get_annotation(0)

    assert e.value.message == "This operation is not allowed for objects that exist on a space."


def test_get_annotation_frames_throws_error_if_object_is_on_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")
    new_object_instance = box_ontology_item.create_instance()
    box_coordinates = BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0)
    video_space_1.put_object_instance(
        object_instance=new_object_instance,
        frames=[1],
        coordinates=box_coordinates,
    )

    # Act
    with pytest.raises(LabelRowError) as e:
        new_object_instance.get_annotation_frames()

    assert e.value.message == "This operation is not allowed for objects that exist on a space."


def test_place_classification_on_video_space_throws_error_if_object_has_frames(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")
    new_classification_instance = text_classification.create_instance()
    new_classification_instance.set_for_frames(frames=0)

    # Act
    with pytest.raises(LabelRowError) as e:
        video_space_1.put_classification_instance(classification_instance=new_classification_instance, frames=[0])

    assert (
        e.value.message
        == "Classification instance contains frames data. Ensure ClassificationInstance.set_for_frames was not used before calling this method. "
    )


def test_unplace_classification_on_video_space_throws_error_if_classification_has_frames(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")
    new_classification_instance = text_classification.create_instance()
    new_classification_instance.set_for_frames(frames=0)

    # Act
    with pytest.raises(LabelRowError) as e:
        video_space_1.remove_classification_instance_from_frames(
            classification_instance=new_classification_instance,
            frames=[1],
        )

    assert (
        e.value.message
        == "Classification instance contains frames data. Ensure ClassificationInstance.set_for_frames was not used before calling this method. "
    )


def test_add_classification_to_label_row_throws_error_if_classification_is_on_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")
    new_classification_instance = text_classification.create_instance()
    video_space_1.put_classification_instance(classification_instance=new_classification_instance, frames=0)

    # Act
    with pytest.raises(LabelRowError) as e:
        label_row.add_classification_instance(classification_instance=new_classification_instance)

    assert (
        e.value.message
        == "Classification instance already exists on a space. It cannot be placed directly onto the label row. Please use Space.place_classification instead."
    )


def test_remove_classification_from_label_row_throws_error_if_classification_is_on_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")
    new_classification_instance = text_classification.create_instance()
    video_space_1.put_classification_instance(classification_instance=new_classification_instance, frames=0)

    # Act
    with pytest.raises(LabelRowError) as e:
        label_row.remove_classification(classification_instance=new_classification_instance)

    assert (
        e.value.message
        == "Classification instance already exists on a space. It cannot be removed directly from the label row. Please use Space.remove_classification instead."
    )


def test_set_for_frames_throws_error_if_classification_is_on_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")
    new_classification_instance = text_classification.create_instance()
    video_space_1.put_classification_instance(classification_instance=new_classification_instance, frames=0)

    # Act
    with pytest.raises(LabelRowError) as e:
        new_classification_instance.set_for_frames(frames=0)

    assert (
        e.value.message
        == "This operation is not allowed for classifications that exist on a space.For adding the classification to different frames on a space, use Space.place_classification."
    )


def test_remove_from_frames_throws_error_if_classification_is_on_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")
    new_classification_instance = text_classification.create_instance()
    video_space_1.put_classification_instance(classification_instance=new_classification_instance, frames=0)

    # Act
    with pytest.raises(LabelRowError) as e:
        new_classification_instance.remove_from_frames(frames=0)

    assert (
        e.value.message
        == "This operation is not allowed for classifications that exist on a space.For removing the classification from different frames on a space, use Space.unplace_classification."
    )


def test_get_annotation_throws_error_if_classification_is_on_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")
    new_classification_instance = text_classification.create_instance()
    video_space_1.put_classification_instance(classification_instance=new_classification_instance, frames=0)

    # Act
    with pytest.raises(LabelRowError) as e:
        new_classification_instance.get_annotation()

    assert e.value.message == "This operation is not allowed for classifications that exist on a space."


def test_place_object_on_video_space_throws_error_if_object_has_dynamic_attributes(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")

    new_object_instance = keypoint_with_dynamic_attributes_ontology_item.create_instance()
    new_object_instance.set_answer(frames=0, attribute=key_point_dynamic_text_attribute, answer="Hi there")

    # Act
    with pytest.raises(LabelRowError) as e:
        video_space_1.put_object_instance(
            object_instance=new_object_instance,
            frames=[0, 1, 2],
            coordinates=PointCoordinate(x=0.5, y=0.5),
        )

    assert (
        e.value.message
        == "Object instance contains dynamic attributes. Please ensure no dynamic attributes were set on this ObjectInstance. "
    )


def test_set_dynamic_attributes_throws_error_if_object_on_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")

    new_object_instance = keypoint_with_dynamic_attributes_ontology_item.create_instance()
    video_space_1.put_object_instance(
        object_instance=new_object_instance,
        frames=[0, 1, 2],
        coordinates=PointCoordinate(x=0.5, y=0.5),
    )

    # Act
    with pytest.raises(LabelRowError) as e:
        new_object_instance.set_answer(frames=0, attribute=key_point_dynamic_text_attribute, answer="Hi there")

    assert (
        e.value.message
        == "This operation is not allowed for objects that exist on a space.For setting dynamic attributes for objects on a space, use VideoSpace.set_answer_on_frames."
    )


def test_get_dynamic_attributes_throws_error_if_object_on_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")

    new_object_instance = keypoint_with_dynamic_attributes_ontology_item.create_instance()
    video_space_1.put_object_instance(
        object_instance=new_object_instance,
        frames=[0, 1, 2],
        coordinates=PointCoordinate(x=0.5, y=0.5),
    )

    # Act
    with pytest.raises(LabelRowError) as e:
        new_object_instance.get_answer(attribute=key_point_dynamic_text_attribute)

    assert (
        e.value.message
        == "This operation is not allowed for objects that exist on a space.For getting dynamic attributes for objects on a space, use VideoSpace.get_answer_on_frames."
    )


def test_delete_dynamic_attributes_throws_error_if_object_on_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space_1 = label_row.get_space(id="video-1-uuid", type_="video")

    new_object_instance = keypoint_with_dynamic_attributes_ontology_item.create_instance()
    video_space_1.put_object_instance(
        object_instance=new_object_instance,
        frames=[0, 1, 2],
        coordinates=PointCoordinate(x=0.5, y=0.5),
    )

    # Act
    with pytest.raises(LabelRowError) as e:
        new_object_instance.delete_answer(attribute=key_point_dynamic_text_attribute)

    assert (
        e.value.message
        == "This operation is not allowed for objects that exist on a space.For removing dynamic attributes for objects on a space, use VideoSpace.remove_answer_from_frame."
    )
