from typing import get_args
from unittest.mock import Mock

import pytest

from encord.exceptions import LabelRowError
from encord.objects import LabelRowV2
from encord.objects.ontology_labels_impl import SpaceLiteral
from encord.objects.spaces.types import DataGroupMetadata, SceneMetadata, SpaceMetadata
from encord.utilities.type_utilities import exhaustive_guard
from tests.objects.data.data_group.all_modalities import DATA_GROUP_METADATA


def _get_space_id_from_space_literal(space_literal: SpaceLiteral) -> str:
    if space_literal == "video":
        return "video-uuid"
    elif space_literal == "image":
        return "image-uuid"
    elif space_literal == "image_sequence":
        return "image-sequence-uuid"
    elif space_literal == "audio":
        return "audio-uuid"
    elif space_literal == "text":
        return "text-uuid"
    elif space_literal == "html":
        return "html-uuid"
    elif space_literal == "medical":
        return "dicom-uuid"
    elif space_literal == "pdf":
        return "pdf-uuid"
    elif space_literal == "point_cloud":
        return "point-cloud-uuid"
    else:
        exhaustive_guard(space_literal, message=f"Missing implementation for space {space_literal}")


def _get_space_layout_key_from_space_literal(space_literal: SpaceLiteral) -> str:
    if space_literal == "video":
        return "main-video"
    elif space_literal == "image":
        return "main-image"
    elif space_literal == "image_sequence":
        return "main-image-sequence"
    elif space_literal == "audio":
        return "main-audio"
    elif space_literal == "text":
        return "main-text"
    elif space_literal == "html":
        return "main-html"
    elif space_literal == "medical":
        return "left-shoulder"
    elif space_literal == "pdf":
        return "main-pdf"
    elif space_literal == "point_cloud":
        return "main-point-cloud"
    else:
        exhaustive_guard(space_literal, message=f"Missing implementation for space {space_literal}")


def _get_expected_metadata_for_space_literal(space_literal: SpaceLiteral) -> SpaceMetadata:
    if space_literal == "video":
        return DataGroupMetadata(layout_key="main-video", file_name="video.mp4")
    elif space_literal == "image":
        return DataGroupMetadata(layout_key="main-image", file_name="image.png")
    elif space_literal == "image_sequence":
        return DataGroupMetadata(layout_key="main-image-sequence", file_name="image_sequence.mp4")
    elif space_literal == "audio":
        return DataGroupMetadata(layout_key="main-audio", file_name="audio.mp3")
    elif space_literal == "text":
        return DataGroupMetadata(layout_key="main-text", file_name="text.txt")
    elif space_literal == "html":
        return DataGroupMetadata(layout_key="main-html", file_name="document.html")
    elif space_literal == "medical":
        return DataGroupMetadata(layout_key="left-shoulder", file_name="left-shoulder.dcm")
    elif space_literal == "pdf":
        return DataGroupMetadata(layout_key="main-pdf", file_name="document.pdf")
    elif space_literal == "point_cloud":
        return SceneMetadata(
            stream_id="lidar-top",
            event_index=0,
            uri="https://mybucket/files/point_clouds/lidar-top.pcd",
            file_name="lidar-top.pcd",
            layout_key=None,
        )
    else:
        exhaustive_guard(space_literal, message=f"Missing implementation for space {space_literal}")


def test_space_metadata_is_populated_for_data_group(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)

    spaces = label_row.get_spaces()
    assert len(spaces) == 10  # number of modalities in DATA_GROUP_METADATA

    for space_literal in get_args(SpaceLiteral):
        space_id = _get_space_id_from_space_literal(space_literal)
        space = label_row.get_space(id=space_id, type_=space_literal)

        expected_metadata = _get_expected_metadata_for_space_literal(space_literal)

        assert space.metadata is not None
        assert space.metadata.layout_key == expected_metadata.layout_key
        assert space.metadata.file_name == expected_metadata.file_name


def test_get_space_by_id(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    for space_literal in get_args(SpaceLiteral):
        space_id = _get_space_id_from_space_literal(space_literal)
        space = label_row.get_space(id=space_id, type_=space_literal)
        assert space.space_id == space_id


def test_get_space_by_layout_key(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    for space_literal in get_args(SpaceLiteral):
        if space_literal == "point_cloud":
            continue  # point clouds belongs to scenes which don't have layout keys
        space_layout_key = _get_space_layout_key_from_space_literal(space_literal)
        space = label_row.get_space(layout_key=space_layout_key, type_=space_literal)
        assert space is not None


def test_get_space_that_do_not_exist(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)

    with pytest.raises(LabelRowError) as no_such_space_error:
        label_row.get_space(id="non-existent-video", type_="video")
    assert (
        no_such_space_error.value.message
        == "Could not find space with given id 'non-existent-video'. Available space ids: ['video-uuid', 'image-uuid', 'text-uuid', 'audio-uuid', 'html-uuid', 'dicom-uuid', 'dicom-stack-uuid', 'image-sequence-uuid', 'pdf-uuid']"
    )

    with pytest.raises(LabelRowError) as no_such_layout_key_error:
        label_row.get_space(layout_key="non-existent-layout", type_="video")
    assert (
        no_such_layout_key_error.value.message
        == "Could not find space with given layout key 'non-existent-layout'. Available layout keys: ['main-video', 'main-image', 'main-text', 'main-audio', 'main-html', 'left-shoulder', 'xray-stack', 'main-image-sequence', 'main-pdf']"
    )

    with pytest.raises(LabelRowError) as incorrect_type_error:
        label_row.get_space(id="image-uuid", type_="video")
    assert (
        incorrect_type_error.value.message
        == "Space with id 'image-uuid' is not of expected type 'video'. Found ImageSpace instead of VideoSpace."
    )
