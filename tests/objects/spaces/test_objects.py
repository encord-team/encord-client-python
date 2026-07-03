from unittest.mock import Mock, PropertyMock

import numpy as np
import pytest

from encord.exceptions import LabelRowError
from encord.objects import LabelRowV2, Object, Shape
from encord.objects.bitmask import BitmaskCoordinates
from tests.objects.data.data_group.all_modalities import (
    DATA_GROUP_METADATA,
    DATA_GROUP_NO_LABELS,
)

bitmask_object = Object(
    uid=1, name="Mask", color="#D33115", shape=Shape.BITMASK, feature_node_hash="bitmask123", attributes=[]
)
box_object = Object(
    uid=2, name="Box", color="#D33115", shape=Shape.BOUNDING_BOX, feature_node_hash="box123", attributes=[]
)


def _label_row_for_bitmask_tests():
    get_child_by_hash = PropertyMock(return_value=bitmask_object)
    ontology_structure = Mock(get_child_by_hash=get_child_by_hash)
    ontology = Mock(structure=ontology_structure)

    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_NO_LABELS)
    return label_row


def _rle_string(height: int, width: int) -> str:
    mask = np.zeros((height, width), dtype=bool)
    mask[0, 0] = True
    mask[2:4, 5:7] = True
    return BitmaskCoordinates(mask)._encoded_bitmask.rle_string


def test_bitmask_dimension_validation():
    # The "space" equivalent of test_bitmask_validation.py
    label_row = _label_row_for_bitmask_tests()

    video_space = label_row.get_space(id="video-uuid", type_="video")
    image_space = label_row.get_space(id="image-uuid", type_="image")
    dicom_stack_space = label_row.get_space(id="dicom-stack-uuid", type_="medical")

    # Correct dimensions (100x100) should succeed on both spaces
    correct_bitmask = BitmaskCoordinates(np.zeros((100, 100), dtype=bool))

    video_instance = bitmask_object.create_instance()
    video_space.put_object_instance(object_instance=video_instance, frames=[0], coordinates=correct_bitmask)
    assert len(video_space.get_object_instances()) == 1

    image_instance = bitmask_object.create_instance()
    image_space.put_object_instance(object_instance=image_instance, coordinates=correct_bitmask)
    assert len(image_space.get_object_instances()) == 1

    dicom_stack_instance = bitmask_object.create_instance()
    dicom_stack_space.put_object_instance(object_instance=dicom_stack_instance, coordinates=correct_bitmask, frames=[0])
    assert len(dicom_stack_space.get_object_instances()) == 1
    label_row.to_encord_dict()  # Serialization should succeed

    # Incorrect dimensions (50x50) should raise ValueError on serialization
    incorrect_bitmask = BitmaskCoordinates(np.zeros((50, 50), dtype=bool))

    incorrect_video_instance = bitmask_object.create_instance()
    video_space.put_object_instance(object_instance=incorrect_video_instance, frames=[0], coordinates=incorrect_bitmask)
    assert len(video_space.get_object_instances()) == 2

    with pytest.raises(ValueError, match="Bitmask dimensions don't match the media dimensions"):
        label_row.to_encord_dict()

    # Remove incorrect video instance
    video_space.remove_object_instance(incorrect_video_instance.object_hash)
    label_row.to_encord_dict()  # Should succeed again

    # Test incorrect dimensions on image space
    incorrect_image_instance = bitmask_object.create_instance()
    image_space.put_object_instance(object_instance=incorrect_image_instance, coordinates=incorrect_bitmask)
    assert len(image_space.get_object_instances()) == 2

    with pytest.raises(ValueError, match="Bitmask dimensions don't match the media dimensions"):
        label_row.to_encord_dict()

    # Test incorrect dimensions on medical stack space
    incorrect_dicom_stack_instance = bitmask_object.create_instance()
    dicom_stack_space.put_object_instance(
        object_instance=incorrect_dicom_stack_instance, coordinates=incorrect_bitmask, frames=[0]
    )
    assert len(dicom_stack_space.get_object_instances()) == 2

    with pytest.raises(ValueError, match="Bitmask dimensions don't match the media dimensions"):
        label_row.to_encord_dict()


def test_put_bitmask_rle_string_on_image_video_and_medical_spaces():
    label_row = _label_row_for_bitmask_tests()

    image_space = label_row.get_space(id="image-uuid", type_="image")
    video_space = label_row.get_space(id="video-uuid", type_="video")
    dicom_space = label_row.get_space(id="dicom-uuid", type_="medical")
    dicom_stack_space = label_row.get_space(id="dicom-stack-uuid", type_="medical")

    rle_100_by_100 = _rle_string(100, 100)
    rle_200_by_100 = _rle_string(200, 100)

    image_instance = bitmask_object.create_instance()
    image_space.put_object_instance(object_instance=image_instance, coordinates=rle_100_by_100)

    video_instance = bitmask_object.create_instance()
    video_space.put_object_instance(object_instance=video_instance, frames=[0, 1], coordinates=rle_100_by_100)

    dicom_instance = bitmask_object.create_instance()
    dicom_space.put_object_instance(object_instance=dicom_instance, frames=[0], coordinates=rle_200_by_100)

    dicom_stack_instance = bitmask_object.create_instance()
    dicom_stack_space.put_object_instance(
        object_instance=dicom_stack_instance,
        frames=[0],
        coordinates=rle_100_by_100,
    )

    assert (
        list(image_space.get_annotations(type_="object"))[0].coordinates._encoded_bitmask.rle_string == rle_100_by_100
    )
    assert [
        annotation.coordinates._encoded_bitmask.rle_string for annotation in video_space.get_annotations(type_="object")
    ] == [
        rle_100_by_100,
        rle_100_by_100,
    ]
    assert (
        list(dicom_space.get_annotations(type_="object"))[0].coordinates._encoded_bitmask.rle_string == rle_200_by_100
    )
    assert (
        list(dicom_stack_space.get_annotations(type_="object"))[0].coordinates._encoded_bitmask.rle_string
        == rle_100_by_100
    )
    label_row.to_encord_dict()


def test_put_bitmask_rle_string_wrong_shape_raises():
    label_row = _label_row_for_bitmask_tests()
    image_space = label_row.get_space(id="image-uuid", type_="image")

    with pytest.raises(LabelRowError, match="bitmask"):
        image_space.put_object_instance(object_instance=box_object.create_instance(), coordinates=_rle_string(100, 100))


def test_put_bitmask_rle_string_on_mixed_dimension_frames_raises():
    label_row = _label_row_for_bitmask_tests()
    dicom_stack_space = label_row.get_space(id="dicom-stack-uuid", type_="medical")

    with pytest.raises(LabelRowError, match="share dimensions"):
        dicom_stack_space.put_object_instance(
            object_instance=bitmask_object.create_instance(),
            frames=[0, 1],
            coordinates=_rle_string(100, 100),
        )
