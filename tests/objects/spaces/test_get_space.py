from unittest.mock import Mock

import pytest

from encord.exceptions import LabelRowError
from encord.objects import LabelRowV2
from tests.objects.data.data_group.all_modalities import DATA_GROUP_METADATA


def test_get_space_by_id(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)

    video_space = label_row._get_space(id="video-uuid", type_="video")
    assert video_space.space_id == "video-uuid"

    image_space = label_row._get_space(id="image-uuid", type_="image")
    assert image_space.space_id == "image-uuid"

    text_space = label_row._get_space(id="text-uuid", type_="text")
    assert text_space.space_id == "text-uuid"

    audio_space = label_row._get_space(id="audio-uuid", type_="audio")
    assert audio_space.space_id == "audio-uuid"


def test_get_space_by_layout_key(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)

    video_space = label_row._get_space(layout_key="main-video", type_="video")
    assert video_space.space_id == "video-uuid"

    image_space = label_row._get_space(layout_key="main-image", type_="image")
    assert image_space.space_id == "image-uuid"

    text_space = label_row._get_space(layout_key="main-text", type_="text")
    assert text_space.space_id == "text-uuid"

    audio_space = label_row._get_space(layout_key="main-audio", type_="audio")
    assert audio_space.space_id == "audio-uuid"


def test_get_space_that_do_not_exist(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)

    with pytest.raises(LabelRowError) as no_such_space_error:
        label_row._get_space(id="non-existent-video", type_="video")
    assert (
        no_such_space_error.value.message
        == "Could not find space with given id 'non-existent-video'. Available space ids: ['video-uuid', 'image-uuid', 'text-uuid', 'audio-uuid', 'html-uuid']"
    )

    with pytest.raises(LabelRowError) as no_such_layout_key_error:
        label_row._get_space(layout_key="non-existent-layout", type_="video")
    assert (
        no_such_layout_key_error.value.message
        == "Could not find space with given layout key 'non-existent-layout'. Available layout keys: ['main-video', 'main-image', 'main-text', 'main-audio', 'main-html']"
    )

    with pytest.raises(LabelRowError) as incorrect_type_error:
        label_row._get_space(id="image-uuid", type_="video")
    assert (
        incorrect_type_error.value.message
        == "Space with id 'image-uuid' is not of expected type 'video'. Found ImageSpace instead of VideoSpace."
    )
