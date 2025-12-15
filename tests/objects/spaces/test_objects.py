from unittest.mock import Mock, PropertyMock

import numpy as np
import pytest

from encord.objects import LabelRowV2, Object, Shape
from encord.objects.bitmask import BitmaskCoordinates
from tests.objects.data.data_group.all_modalities import (
    DATA_GROUP_METADATA,
    DATA_GROUP_NO_LABELS,
)

bitmask_object = Object(
    uid=1, name="Mask", color="#D33115", shape=Shape.BITMASK, feature_node_hash="bitmask123", attributes=[]
)


def test_bitmask_dimension_validation():
    # The "space" equivalent of test_bitmask_validation.py
    get_child_by_hash = PropertyMock(return_value=bitmask_object)
    ontology_structure = Mock(get_child_by_hash=get_child_by_hash)
    ontology = Mock(structure=ontology_structure)

    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_NO_LABELS)

    video_space = label_row.get_space(id="video-uuid", type_="video")
    image_space = label_row.get_space(id="image-uuid", type_="image")

    # Correct dimensions (100x100) should succeed on both spaces
    correct_bitmask = BitmaskCoordinates(np.zeros((100, 100), dtype=bool))

    video_instance = bitmask_object.create_instance()
    video_space.put_object_instance(object_instance=video_instance, frames=[0], coordinates=correct_bitmask)
    assert len(video_space.get_object_instances()) == 1

    image_instance = bitmask_object.create_instance()
    image_space.put_object_instance(object_instance=image_instance, coordinates=correct_bitmask)
    assert len(image_space.get_object_instances()) == 1

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
