from math import ceil

import pytest

from encord.constants.enums import DataType
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
    label_row = LabelRowV2.from_media_metadata(all_types_ontology, metadata)

    assert label_row.data_type.value == "video"
    assert label_row.number_of_frames == ceil(25.0 * 4.0)
    assert label_row.is_labelling_initialised


def test_detached_image_label_row(all_types_ontology):
    metadata = CustomerProvidedImageMetadata(width=640, height=480, file_size=0, mime_type="image/jpeg")
    label_row = LabelRowV2.from_media_metadata(all_types_ontology, metadata)

    assert label_row.data_type.value == "image"
    assert label_row.number_of_frames == 1
    assert label_row.is_labelling_initialised


def test_detached_img_group_label_row(all_types_ontology):
    images = [
        CustomerProvidedImageMetadata(width=640, height=480, file_size=0, mime_type="image/jpeg"),
        CustomerProvidedImageMetadata(width=800, height=600, file_size=0, mime_type="image/png"),
        CustomerProvidedImageMetadata(width=1024, height=768, file_size=0, mime_type="image/jpeg"),
    ]
    label_row = LabelRowV2.from_media_metadata(all_types_ontology, images)

    assert label_row.data_type.value == "img_group"
    assert label_row.number_of_frames == 3
    assert label_row.is_labelling_initialised


def test_detached_audio_label_row(all_types_ontology):
    metadata = CustomerProvidedAudioMetadata(
        duration=10.0, file_size=0, mime_type="audio/mpeg", sample_rate=44100, bit_depth=16, codec="mp3", num_channels=2
    )
    label_row = LabelRowV2.from_media_metadata(all_types_ontology, metadata)

    assert label_row.data_type.value == "audio"
    assert label_row.number_of_frames == ceil(10.0 * 44100)
    assert label_row.is_labelling_initialised


def test_detached_plain_text_label_row(all_types_ontology):
    metadata = CustomerProvidedTextMetadata(file_size=0, mime_type="text/plain")
    label_row = LabelRowV2.from_media_metadata(all_types_ontology, metadata)

    assert label_row.data_type.value == "plain_text"
    assert label_row.number_of_frames == 1
    assert label_row.is_labelling_initialised


def test_detached_pdf_label_row(all_types_ontology):
    metadata = CustomerProvidedPdfMetadata(file_size=0, num_pages=5)
    label_row = LabelRowV2.from_media_metadata(all_types_ontology, metadata)

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

    # Verify object_answers references the annotated object instance
    object_answer = list(label_dict["object_answers"].values())[0]
    assert object_answer["objectHash"] == instance.object_hash

    # Verify featureHash is present in the per-frame data unit annotations
    objects_in_frame = data_unit["labels"]["0"]["objects"]
    assert len(objects_in_frame) > 0
    assert objects_in_frame[0]["featureHash"] == box_ontology.feature_node_hash


def test_from_labels_dict_preserve_identity(all_types_ontology):
    """Loading an offline dict into a live row with preserve_identity=True keeps the live row's identity."""
    from dataclasses import asdict
    from unittest.mock import Mock

    from tests.objects.common import BASE_LABEL_ROW_METADATA

    # 1. Create a detached label row with annotations
    detached = LabelRowV2.from_media_metadata(
        all_types_ontology,
        CustomerProvidedVideoMetadata(
            fps=25.0, duration=4.0, width=1920, height=1080, file_size=0, mime_type="video/mp4"
        ),
    )
    box_ontology = all_types_ontology.structure.get_child_by_title("Box", type_=Object)
    instance = box_ontology.create_instance()
    instance.set_for_frames(
        BoundingBoxCoordinates(top_left_x=0.1, top_left_y=0.2, width=0.3, height=0.4),
        frames=[0, 1],
    )
    detached.add_object_instance(instance)
    offline_dict = detached.to_encord_dict()

    # 2. Create a "live" label row with real identity
    live_label_hash = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    live_data_hash = "11111111-2222-3333-4444-555555555555"
    live_dataset_hash = "66666666-7777-8888-9999-000000000000"
    metadata_dict = asdict(BASE_LABEL_ROW_METADATA)
    metadata_dict["label_hash"] = live_label_hash
    metadata_dict["data_hash"] = live_data_hash
    metadata_dict["dataset_hash"] = live_dataset_hash
    from encord.orm.label_row import LabelRowMetadata

    live_row = LabelRowV2(LabelRowMetadata(**metadata_dict), Mock(), all_types_ontology)

    # 3. Load offline content with preserve_identity=True
    live_row.from_labels_dict(offline_dict, preserve_identity=True)

    # Identity should be the live row's, not the offline dict's
    assert live_row.label_hash == live_label_hash
    assert live_row.data_hash == live_data_hash
    assert live_row.dataset_hash == live_dataset_hash

    # Content should be from the offline dict
    assert len(live_row.get_object_instances()) == 1
    obj = live_row.get_object_instances()[0]
    assert len(obj.get_annotations()) == 2


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


def test_attach_to_project(all_types_ontology):
    """attach_to_project replaces identity with server values and enables save()."""
    from unittest.mock import Mock

    # Create a detached label row with an annotation
    detached = LabelRowV2.from_media_metadata(
        all_types_ontology,
        CustomerProvidedVideoMetadata(
            fps=25.0, duration=4.0, width=1920, height=1080, file_size=0, mime_type="video/mp4"
        ),
    )
    box_ontology = all_types_ontology.structure.get_child_by_title("Box", type_=Object)
    instance = box_ontology.create_instance()
    instance.set_for_frames(
        BoundingBoxCoordinates(top_left_x=0.1, top_left_y=0.2, width=0.3, height=0.4),
        frames=[0],
    )
    detached.add_object_instance(instance)
    assert detached.is_detached

    # Mock a project that returns a real label row with label_hash already set
    server_label_hash = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    server_data_hash = "11111111-2222-3333-4444-555555555555"
    server_dataset_hash = "66666666-7777-8888-9999-000000000000"

    mock_real_row = Mock()
    mock_real_row.label_hash = server_label_hash
    mock_real_row.data_hash = server_data_hash
    mock_real_row.dataset_hash = server_dataset_hash
    mock_real_row.branch_name = "main"
    mock_real_row.data_type = DataType.VIDEO
    mock_real_row._extract_identity.side_effect = lambda: {
        "label_hash": mock_real_row.label_hash,
        "data_hash": mock_real_row.data_hash,
        "dataset_hash": mock_real_row.dataset_hash,
        "branch_name": mock_real_row.branch_name,
    }

    mock_project = Mock()
    mock_project.list_label_rows_v2.return_value = [mock_real_row]
    mock_project._client = Mock()

    detached.attach_to_project(mock_project, server_data_hash)

    # Identity should now be the server's
    assert detached.label_hash == server_label_hash
    assert detached.data_hash == server_data_hash
    assert detached.dataset_hash == server_dataset_hash
    assert not detached.is_detached

    # Annotation content should be preserved
    assert len(detached.get_object_instances()) == 1

    # save() should no longer raise
    mock_project._client.save_label_rows = Mock()
    detached.save()
    # initialise_labels should NOT have been called (label_hash was already set)
    mock_real_row.initialise_labels.assert_not_called()


def test_attach_to_project_auto_initialises(all_types_ontology):
    """attach_to_project calls initialise_labels on the server row when label_hash is None."""
    from unittest.mock import Mock

    detached = LabelRowV2.from_media_metadata(
        all_types_ontology,
        CustomerProvidedImageMetadata(width=640, height=480, file_size=0, mime_type="image/jpeg"),
    )

    server_data_hash = "11111111-2222-3333-4444-555555555555"
    server_label_hash = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

    mock_real_row = Mock()
    mock_real_row.label_hash = None  # not yet initialised
    mock_real_row.data_hash = server_data_hash
    mock_real_row.dataset_hash = "66666666-7777-8888-9999-000000000000"
    mock_real_row.branch_name = "main"
    mock_real_row.data_type = DataType.IMAGE
    mock_real_row._extract_identity.side_effect = lambda: {
        "label_hash": mock_real_row.label_hash,
        "data_hash": mock_real_row.data_hash,
        "dataset_hash": mock_real_row.dataset_hash,
        "branch_name": mock_real_row.branch_name,
    }

    # After initialise_labels is called, label_hash should be set
    def fake_initialise():
        mock_real_row.label_hash = server_label_hash

    mock_real_row.initialise_labels.side_effect = fake_initialise

    mock_project = Mock()
    mock_project.list_label_rows_v2.return_value = [mock_real_row]
    mock_project._client = Mock()

    detached.attach_to_project(mock_project, server_data_hash)

    mock_real_row.initialise_labels.assert_called_once()
    assert detached.label_hash == server_label_hash
    assert not detached.is_detached


def test_img_group_identity_remapping(all_types_ontology):
    """IMG_GROUP frame hashes are remapped by sequence index when identity is applied."""
    detached = LabelRowV2.from_media_metadata(
        all_types_ontology,
        [
            CustomerProvidedImageMetadata(width=640, height=480, file_size=0, mime_type="image/jpeg"),
            CustomerProvidedImageMetadata(width=800, height=600, file_size=0, mime_type="image/png"),
        ],
    )

    # Capture the original (offline-generated) frame hashes
    original_frame_0_hash = detached._label_row_read_only_data.frame_to_image_hash[0]
    original_frame_1_hash = detached._label_row_read_only_data.frame_to_image_hash[1]

    # Apply new identity with different frame hashes
    new_frame_hashes = ["real-hash-frame-0", "real-hash-frame-1"]
    detached._apply_identity(
        label_hash="new-label-hash",
        data_hash="new-data-hash",
        dataset_hash="new-dataset-hash",
        branch_name="main",
        frame_hashes=new_frame_hashes,
    )

    # Verify frame hashes were remapped
    assert detached._label_row_read_only_data.frame_to_image_hash[0] == "real-hash-frame-0"
    assert detached._label_row_read_only_data.frame_to_image_hash[1] == "real-hash-frame-1"
    assert detached._label_row_read_only_data.image_hash_to_frame["real-hash-frame-0"] == 0
    assert detached._label_row_read_only_data.image_hash_to_frame["real-hash-frame-1"] == 1
    assert detached._label_row_read_only_data.frame_level_data[0].image_hash == "real-hash-frame-0"
    assert detached._label_row_read_only_data.frame_level_data[1].image_hash == "real-hash-frame-1"

    # Old hashes should be gone
    assert original_frame_0_hash not in detached._label_row_read_only_data.image_hash_to_frame
    assert original_frame_1_hash not in detached._label_row_read_only_data.image_hash_to_frame


def test_apply_identity_remaps_data_unit_hash_for_non_img_group(all_types_ontology):
    """For non-IMG_GROUP types, _apply_identity remaps the single data unit hash to match data_hash."""
    detached = LabelRowV2.from_media_metadata(
        all_types_ontology,
        CustomerProvidedVideoMetadata(
            fps=25.0, duration=4.0, width=1920, height=1080, file_size=0, mime_type="video/mp4"
        ),
    )

    new_data_hash = "real-server-data-hash"
    detached._apply_identity(
        label_hash="real-label-hash",
        data_hash=new_data_hash,
        dataset_hash="real-dataset-hash",
        branch_name="main",
    )

    # The data unit's image_hash should now match the new data_hash
    rod = detached._label_row_read_only_data
    assert rod.data_hash == new_data_hash
    assert rod.frame_level_data[0].image_hash == new_data_hash
    assert rod.frame_to_image_hash[0] == new_data_hash
    assert rod.image_hash_to_frame[new_data_hash] == 0

    # Serialized dict should be consistent
    label_dict = detached.to_encord_dict()
    assert label_dict["data_hash"] == new_data_hash
    data_units = label_dict["data_units"]
    assert new_data_hash in data_units
    assert data_units[new_data_hash]["data_hash"] == new_data_hash


def test_empty_img_group_rejected(all_types_ontology):
    """An empty list of images should raise LabelRowError."""
    with pytest.raises(LabelRowError, match="empty"):
        LabelRowV2.from_media_metadata(all_types_ontology, [])
