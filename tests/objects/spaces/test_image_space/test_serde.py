from unittest.mock import Mock

import pytest
from deepdiff import DeepDiff

from encord.constants.enums import SpaceType
from encord.objects import LabelRowV2
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.two_images import (
    DATA_GROUP_METADATA,
    DATA_GROUP_WITH_TWO_IMAGES_LABELS,
)


@pytest.fixture
def ontology():
    ontology_structure = Mock()
    ontology_structure.get_child_by_hash = all_types_structure.get_child_by_hash
    ontology = Mock(structure=ontology_structure)
    yield ontology


def test_parse_spaces_before_initialise_labels(ontology):
    # Arrange

    # Act
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)

    # Assert
    spaces = label_row.get_spaces()
    assert len(spaces) == 2

    image_space_1 = label_row.get_space(id="image-1-uuid", type_="image")
    assert image_space_1.space_id == "image-1-uuid"
    assert image_space_1.space_type == SpaceType.IMAGE
    assert image_space_1.layout_key == "front"

    image_space_2 = label_row.get_space(id="image-2-uuid", type_="image")
    assert image_space_2.space_id == "image-2-uuid"
    assert image_space_2.space_type == SpaceType.IMAGE
    assert image_space_2.layout_key == "back"


def test_read_and_export_image_space_labels(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_WITH_TWO_IMAGES_LABELS)

    image_space_1 = label_row.get_space(id="image-1-uuid", type_="image")
    image_space_1_object_annotations = image_space_1.get_object_annotations()
    assert len(image_space_1_object_annotations) == 1

    image_space_1_object_entities = image_space_1.get_objects()
    assert len(image_space_1_object_entities) == 1

    image_space_1_classification_annotations = image_space_1.get_classification_annotations()
    assert len(image_space_1_classification_annotations) == 1
    classification_entities = image_space_1.get_classifications()
    assert len(classification_entities) == 1

    output_dict = label_row.to_encord_dict()

    assert not DeepDiff(
        DATA_GROUP_WITH_TWO_IMAGES_LABELS,
        output_dict,
        exclude_regex_paths=[r".*\['trackHash'\]"],
        ignore_order_func=lambda x: x.path().endswith("['objects']"),
    )
