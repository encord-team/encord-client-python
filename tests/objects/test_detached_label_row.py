from math import ceil

import pytest

from encord.exceptions import LabelRowError
from encord.objects import LabelRowV2, Object
from encord.objects.coordinates import BoundingBoxCoordinates
from encord.orm.storage import (
    CustomerProvidedAudioMetadata,
    CustomerProvidedImageMetadata,
    CustomerProvidedPdfMetadata,
    CustomerProvidedTextMetadata,
    CustomerProvidedVideoMetadata,
)


def test_detached_video_label_row(all_types_ontology):
    metadata = CustomerProvidedVideoMetadata(
        fps=25.0, duration=4.0, width=1920, height=1080, file_size=0, mime_type="video/mp4"
    )
    label_row = LabelRowV2.from_media_metadata(all_types_ontology, metadata, data_title="test.mp4")

    assert label_row.data_type.value == "video"
    assert label_row.number_of_frames == ceil(25.0 * 4.0)
    assert label_row.is_labelling_initialised
    assert label_row.data_title == "test.mp4"


def test_detached_image_label_row(all_types_ontology):
    metadata = CustomerProvidedImageMetadata(width=640, height=480, file_size=0, mime_type="image/jpeg")
    label_row = LabelRowV2.from_media_metadata(all_types_ontology, metadata, data_title="test.jpg")

    assert label_row.data_type.value == "image"
    assert label_row.number_of_frames == 1
    assert label_row.is_labelling_initialised


def test_detached_img_group_label_row(all_types_ontology):
    images = [
        CustomerProvidedImageMetadata(width=640, height=480, file_size=0, mime_type="image/jpeg"),
        CustomerProvidedImageMetadata(width=800, height=600, file_size=0, mime_type="image/png"),
        CustomerProvidedImageMetadata(width=1024, height=768, file_size=0, mime_type="image/jpeg"),
    ]
    label_row = LabelRowV2.from_media_metadata(all_types_ontology, images, data_title="group")

    assert label_row.data_type.value == "img_group"
    assert label_row.number_of_frames == 3
    assert label_row.is_labelling_initialised


def test_detached_audio_label_row(all_types_ontology):
    metadata = CustomerProvidedAudioMetadata(
        duration=10.0, file_size=0, mime_type="audio/mpeg", sample_rate=44100, bit_depth=16, codec="mp3", num_channels=2
    )
    label_row = LabelRowV2.from_media_metadata(all_types_ontology, metadata, data_title="test.mp3")

    assert label_row.data_type.value == "audio"
    assert label_row.number_of_frames == ceil(10.0 * 44100)
    assert label_row.is_labelling_initialised


def test_detached_plain_text_label_row(all_types_ontology):
    metadata = CustomerProvidedTextMetadata(file_size=0, mime_type="text/plain")
    label_row = LabelRowV2.from_media_metadata(all_types_ontology, metadata, data_title="test.txt")

    assert label_row.data_type.value == "plain_text"
    assert label_row.number_of_frames == 1
    assert label_row.is_labelling_initialised


def test_detached_pdf_label_row(all_types_ontology):
    metadata = CustomerProvidedPdfMetadata(file_size=0, num_pages=5)
    label_row = LabelRowV2.from_media_metadata(all_types_ontology, metadata, data_title="test.pdf")

    assert label_row.data_type.value == "pdf"
    assert label_row.number_of_frames == 5
    assert label_row.is_labelling_initialised


def test_detached_label_row_add_object_and_export(all_types_ontology):
    metadata = CustomerProvidedVideoMetadata(
        fps=25.0, duration=4.0, width=1920, height=1080, file_size=0, mime_type="video/mp4"
    )
    label_row = LabelRowV2.from_media_metadata(all_types_ontology, metadata)

    box_ontology = all_types_ontology.structure.get_child_by_title("Box", type_=Object)
    instance = box_ontology.create_instance()
    instance.set_for_frames(
        BoundingBoxCoordinates(top_left_x=0.1, top_left_y=0.2, width=0.3, height=0.4),
        frames=[0, 1, 2],
    )
    label_row.add_object_instance(instance)

    label_dict = label_row.to_encord_dict()

    assert label_dict["label_hash"] is not None
    assert label_dict["data_type"] == "video"
    assert label_dict["object_answers"] != {}
    # Check that data_units has proper structure
    assert len(label_dict["data_units"]) == 1
    data_unit = list(label_dict["data_units"].values())[0]
    assert data_unit["width"] == 1920
    assert data_unit["height"] == 1080


def test_detached_label_row_round_trip(all_types_ontology):
    metadata = CustomerProvidedVideoMetadata(
        fps=25.0, duration=4.0, width=1920, height=1080, file_size=0, mime_type="video/mp4"
    )
    label_row = LabelRowV2.from_media_metadata(all_types_ontology, metadata)

    box_ontology = all_types_ontology.structure.get_child_by_title("Box", type_=Object)
    instance = box_ontology.create_instance()
    instance.set_for_frames(
        BoundingBoxCoordinates(top_left_x=0.1, top_left_y=0.2, width=0.3, height=0.4),
        frames=[0, 1],
    )
    label_row.add_object_instance(instance)

    # Export
    label_dict = label_row.to_encord_dict()

    # Re-import into a new label row
    from dataclasses import asdict

    from tests.objects.common import BASE_LABEL_ROW_METADATA

    metadata_dict = asdict(BASE_LABEL_ROW_METADATA)
    metadata_dict["data_hash"] = label_dict["data_hash"]
    metadata_dict["label_hash"] = label_dict["label_hash"]
    label_row_metadata = __import__("encord.orm.label_row", fromlist=["LabelRowMetadata"]).LabelRowMetadata(
        **metadata_dict
    )

    from unittest.mock import Mock

    label_row_2 = LabelRowV2(label_row_metadata, Mock(), all_types_ontology)
    label_row_2.from_labels_dict(label_dict)

    assert len(label_row_2.get_object_instances()) == 1
    obj = label_row_2.get_object_instances()[0]
    assert len(obj.get_annotations()) == 2


def test_detached_label_row_custom_data_hash(all_types_ontology):
    metadata = CustomerProvidedImageMetadata(width=640, height=480, file_size=0, mime_type="image/jpeg")
    custom_hash = "12345678-1234-1234-1234-123456789abc"
    label_row = LabelRowV2.from_media_metadata(
        all_types_ontology, metadata, data_hash=custom_hash, data_title="custom.jpg"
    )

    assert label_row.data_hash == custom_hash


def test_detached_label_row_save_raises(all_types_ontology):
    metadata = CustomerProvidedImageMetadata(width=640, height=480, file_size=0, mime_type="image/jpeg")
    label_row = LabelRowV2.from_media_metadata(all_types_ontology, metadata)

    with pytest.raises(LabelRowError, match="detached"):
        label_row.save()


def test_detached_label_row_initialise_labels_raises(all_types_ontology):
    metadata = CustomerProvidedImageMetadata(width=640, height=480, file_size=0, mime_type="image/jpeg")
    label_row = LabelRowV2.from_media_metadata(all_types_ontology, metadata)

    with pytest.raises(LabelRowError, match="detached"):
        label_row.initialise_labels()


def test_detached_label_row_workflow_reopen_raises(all_types_ontology):
    metadata = CustomerProvidedImageMetadata(width=640, height=480, file_size=0, mime_type="image/jpeg")
    label_row = LabelRowV2.from_media_metadata(all_types_ontology, metadata)

    with pytest.raises(LabelRowError, match="detached"):
        label_row.workflow_reopen()


def test_detached_label_row_workflow_complete_raises(all_types_ontology):
    metadata = CustomerProvidedImageMetadata(width=640, height=480, file_size=0, mime_type="image/jpeg")
    label_row = LabelRowV2.from_media_metadata(all_types_ontology, metadata)

    with pytest.raises(LabelRowError, match="detached"):
        label_row.workflow_complete()


def test_detached_label_row_get_storage_item_raises(all_types_ontology):
    metadata = CustomerProvidedImageMetadata(width=640, height=480, file_size=0, mime_type="image/jpeg")
    label_row = LabelRowV2.from_media_metadata(all_types_ontology, metadata)

    with pytest.raises(LabelRowError, match="detached"):
        label_row.get_storage_item()


def test_detached_label_row_initialise_storage_item_raises(all_types_ontology):
    metadata = CustomerProvidedImageMetadata(width=640, height=480, file_size=0, mime_type="image/jpeg")
    label_row = LabelRowV2.from_media_metadata(all_types_ontology, metadata)

    with pytest.raises(LabelRowError, match="detached"):
        label_row.initialise_storage_item()


def test_detached_label_row_get_validation_errors_raises(all_types_ontology):
    metadata = CustomerProvidedImageMetadata(width=640, height=480, file_size=0, mime_type="image/jpeg")
    label_row = LabelRowV2.from_media_metadata(all_types_ontology, metadata)

    with pytest.raises(LabelRowError, match="detached"):
        label_row.get_validation_errors()
