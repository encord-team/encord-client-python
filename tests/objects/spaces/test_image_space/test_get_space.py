from unittest.mock import Mock

import pytest

from encord.constants.enums import SpaceType
from encord.objects import LabelRowV2
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.two_images import DATA_GROUP_METADATA


@pytest.fixture
def ontology():
    ontology_structure = Mock()
    ontology_structure.get_child_by_hash = all_types_structure.get_child_by_hash
    ontology = Mock(structure=ontology_structure)
    yield ontology


def test_get_space_by_id(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)

    # Act
    video_space_1 = label_row.get_space(id="image-1-uuid", type_="image")
    video_space_2 = label_row.get_space(id="image-2-uuid", type_="image")

    # Assert
    assert video_space_1.space_id == "image-1-uuid"
    assert video_space_1.space_type == SpaceType.IMAGE
    assert video_space_1.layout_key == "front"

    assert video_space_2.space_id == "image-2-uuid"
    assert video_space_2.space_type == SpaceType.IMAGE
    assert video_space_2.layout_key == "back"


def test_get_space_by_layout_key(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)

    # Act
    video_space_1 = label_row.get_space(layout_key="front", type_="image")
    video_space_2 = label_row.get_space(layout_key="back", type_="image")

    # Assert
    assert video_space_1.space_id == "image-1-uuid"
    assert video_space_1.space_type == SpaceType.IMAGE
    assert video_space_1.layout_key == "front"

    assert video_space_2.space_id == "image-2-uuid"
    assert video_space_2.space_type == SpaceType.IMAGE
    assert video_space_2.layout_key == "back"
