"""`LabelRowV2._validate_object_ids` must catch collisions on space-placed objects, not just root ones,
while still allowing the same object instance to legitimately sit on more than one space."""

from unittest.mock import Mock

import pytest

from encord.exceptions import LabelRowError
from encord.objects import LabelRowV2, Object
from encord.objects.coordinates import BoundingBoxCoordinates
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.two_images import (
    DATA_GROUP_METADATA,
    DATA_GROUP_TWO_IMAGES_NO_LABELS,
)

box_ontology_item = all_types_structure.get_child_by_hash("MjI2NzEy", Object)


def test_validate_object_ids_catches_collision_between_two_space_objects():
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), all_types_structure)
    label_row.from_labels_dict(DATA_GROUP_TWO_IMAGES_NO_LABELS)
    image_space = label_row.get_space(id="image-1-uuid", type_="image")

    instance_a = box_ontology_item.create_instance(object_id=1)
    instance_b = box_ontology_item.create_instance(object_id=1)
    coordinates = BoundingBoxCoordinates(height=0.1, width=0.1, top_left_x=0.1, top_left_y=0.1)
    image_space.put_object_instance(object_instance=instance_a, coordinates=coordinates)
    image_space.put_object_instance(object_instance=instance_b, coordinates=coordinates)

    with pytest.raises(LabelRowError, match="both claim"):
        label_row._validate_object_ids()


def test_validate_object_ids_catches_collision_between_root_and_space_object():
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), all_types_structure)
    label_row.from_labels_dict(DATA_GROUP_TWO_IMAGES_NO_LABELS)
    image_space = label_row.get_space(id="image-1-uuid", type_="image")

    root_instance = box_ontology_item.create_instance(object_id=2)
    root_instance.set_for_frames(
        BoundingBoxCoordinates(height=0.1, width=0.1, top_left_x=0.2, top_left_y=0.2), frames=0
    )
    label_row.add_object_instance(root_instance)

    space_instance = box_ontology_item.create_instance(object_id=2)
    coordinates = BoundingBoxCoordinates(height=0.1, width=0.1, top_left_x=0.1, top_left_y=0.1)
    image_space.put_object_instance(object_instance=space_instance, coordinates=coordinates)

    with pytest.raises(LabelRowError, match="both claim"):
        label_row._validate_object_ids()


def test_validate_object_ids_allows_same_instance_placed_on_two_spaces():
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), all_types_structure)
    label_row.from_labels_dict(DATA_GROUP_TWO_IMAGES_NO_LABELS)
    image_space_1 = label_row.get_space(id="image-1-uuid", type_="image")
    image_space_2 = label_row.get_space(id="image-2-uuid", type_="image")

    instance = box_ontology_item.create_instance(object_id=3)
    coordinates = BoundingBoxCoordinates(height=0.1, width=0.1, top_left_x=0.1, top_left_y=0.1)
    image_space_1.put_object_instance(object_instance=instance, coordinates=coordinates)
    image_space_2.put_object_instance(object_instance=instance, coordinates=coordinates)

    label_row._validate_object_ids()
