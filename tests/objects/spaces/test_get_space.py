from unittest.mock import Mock

from encord.objects import LabelRowV2
from tests.objects.data.data_group.all_modalities import DATA_GROUP_METADATA


def test_get_space_by_id(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)

    video_space = label_row.get_space(id="video-uuid", type_="video")
    assert video_space.space_id == "video-uuid"

    image_space = label_row.get_space(id="image-uuid", type_="image")
    assert image_space.space_id == "image-uuid"

    text_space = label_row.get_space(id="text-uuid", type_="text")
    assert text_space.space_id == "text-uuid"

    audio_space = label_row.get_space(id="audio-uuid", type_="audio")
    assert audio_space.space_id == "audio-uuid"


def test_get_space_by_layout_key(ontology):
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)

    video_space = label_row.get_space(layout_key="main-video", type_="video")
    assert video_space.space_id == "video-uuid"

    image_space = label_row.get_space(layout_key="main-image", type_="image")
    assert image_space.space_id == "image-uuid"

    text_space = label_row.get_space(layout_key="main-text", type_="text")
    assert text_space.space_id == "text-uuid"

    audio_space = label_row.get_space(layout_key="main-audio", type_="audio")
    assert audio_space.space_id == "audio-uuid"
