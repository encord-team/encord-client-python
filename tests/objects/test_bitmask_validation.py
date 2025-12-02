from datetime import datetime
from unittest.mock import Mock, PropertyMock

import numpy as np
import pytest

from encord.objects import LabelRowV2, Object, ObjectInstance, Shape
from encord.objects.bitmask import BitmaskCoordinates
from encord.orm.label_row import AnnotationTaskStatus, LabelRowMetadata, LabelStatus

bitmask_object = Object(
    uid=1, name="Mask", color="#D33115", shape=Shape.BITMASK, feature_node_hash="bitmask123", attributes=[]
)
get_child_by_hash = PropertyMock(return_value=bitmask_object)
ontology_structure = Mock(get_child_by_hash=get_child_by_hash)
ontology = Mock(structure=ontology_structure)


def test_image_bitmask_dimension_validation():
    # Create label row metadata with specific dimensions (512x512)
    metadata = LabelRowMetadata(
        label_hash="test_label",
        branch_name="main",
        created_at=datetime.now(),
        last_edited_at=datetime.now(),
        data_hash="test_data",
        data_title="Test Image",
        data_type="IMAGE",
        data_link="",
        dataset_hash="test_dataset",
        dataset_title="Test Dataset",
        label_status=LabelStatus.NOT_LABELLED,
        annotation_task_status=AnnotationTaskStatus.QUEUED,
        workflow_graph_node=None,
        is_shadow_data=False,
        duration=None,
        frames_per_second=None,
        number_of_frames=1,
        height=512,
        width=512,
        audio_codec=None,
        audio_sample_rate=None,
        audio_num_channels=None,
        audio_bit_depth=None,
        spaces={},
    )

    # Create empty labels dict
    empty_labels = {
        "label_hash": "test_label",
        "branch_name": "main",
        "created_at": "Thu, 09 Feb 2023 14:12:03 UTC",
        "last_edited_at": "Thu, 09 Feb 2023 14:12:03 UTC",
        "data_hash": "test_data",
        "annotation_task_status": "QUEUED",
        "is_shadow_data": False,
        "dataset_hash": "test_dataset",
        "dataset_title": "Test Dataset",
        "data_title": "Test Image",
        "data_type": "image",
        "data_units": {
            "test_data": {
                "data_hash": "test_data",
                "data_title": "Test Image",
                "data_link": "",
                "data_type": "image/png",
                "data_sequence": "0",
                "width": 512,
                "height": 512,
                "labels": {"objects": [], "classifications": []},
            }
        },
        "object_answers": {},
        "classification_answers": {},
        "object_actions": {},
        "label_status": "LABEL_IN_PROGRESS",
    }

    # Correct dimensions (512x512) should succeed
    label_row = LabelRowV2(metadata, Mock(), ontology)
    label_row.from_labels_dict(empty_labels)

    correct_bitmask_coords = BitmaskCoordinates(np.zeros((512, 512), dtype=bool))
    correct_obj_instance = ObjectInstance(bitmask_object)
    correct_obj_instance.set_for_frames(coordinates=correct_bitmask_coords, frames=0)
    label_row.add_object_instance(correct_obj_instance)
    assert len(label_row.get_object_instances()) == 1
    label_row.to_encord_dict()  # Serialization should also succeed

    # Incorrect dimensions (256x256) should raise ValueError
    incorrect_bitmask_coords = BitmaskCoordinates(np.zeros((256, 256), dtype=bool))
    incorrect_obj_instance = ObjectInstance(bitmask_object)
    incorrect_obj_instance.set_for_frames(coordinates=incorrect_bitmask_coords, frames=0)
    label_row.add_object_instance(incorrect_obj_instance)
    assert len(label_row.get_object_instances()) == 2

    with pytest.raises(ValueError, match="Bitmask dimensions don't match the media dimensions"):
        label_row.to_encord_dict()


def test_image_group_bitmask_dimension_validation():
    metadata = LabelRowMetadata(
        label_hash="test_label",
        branch_name="main",
        created_at=datetime.now(),
        last_edited_at=datetime.now(),
        data_hash="test_data",
        data_title="Test Image Group",
        data_type="IMG_GROUP",
        data_link="",
        dataset_hash="test_dataset",
        dataset_title="Test Dataset",
        label_status=LabelStatus.NOT_LABELLED,
        annotation_task_status=AnnotationTaskStatus.QUEUED,
        workflow_graph_node=None,
        is_shadow_data=False,
        duration=None,
        frames_per_second=None,
        number_of_frames=2,
        height=None,
        width=None,
        audio_codec=None,
        audio_sample_rate=None,
        audio_num_channels=None,
        audio_bit_depth=None,
        spaces={},
    )

    # Create empty labels dict for image group with different dimensions per frame
    empty_labels = {
        "label_hash": "test_label",
        "branch_name": "main",
        "created_at": "Thu, 09 Feb 2023 14:12:03 UTC",
        "last_edited_at": "Thu, 09 Feb 2023 14:12:03 UTC",
        "data_hash": "test_data",
        "annotation_task_status": "QUEUED",
        "is_shadow_data": False,
        "dataset_hash": "test_dataset",
        "dataset_title": "Test Dataset",
        "data_title": "Test Image Group",
        "data_type": "img_group",
        "data_units": {
            "frame_0_hash": {
                "data_hash": "frame_0_hash",
                "data_title": "Frame 0",
                "data_link": "",
                "data_type": "image/png",
                "data_sequence": "0",
                "width": 512,
                "height": 512,
                "labels": {"objects": [], "classifications": []},
            },
            "frame_1_hash": {
                "data_hash": "frame_1_hash",
                "data_title": "Frame 1",
                "data_link": "",
                "data_type": "image/png",
                "data_sequence": "1",
                "width": 1024,
                "height": 768,
                "labels": {"objects": [], "classifications": []},
            },
        },
        "object_answers": {},
        "classification_answers": {},
        "object_actions": {},
        "label_status": "LABEL_IN_PROGRESS",
    }

    label_row = LabelRowV2(metadata, Mock(), ontology)
    label_row.from_labels_dict(empty_labels)

    # Add bitmask with correct dimensions for frame 0 (512x512)
    frame_0_correct_mask = BitmaskCoordinates(np.zeros((512, 512), dtype=bool))
    frame_0_correct_instance = ObjectInstance(bitmask_object)
    frame_0_correct_instance.set_for_frames(coordinates=frame_0_correct_mask, frames=0)
    label_row.add_object_instance(frame_0_correct_instance)

    # Add bitmask with correct dimensions for frame 1 (1024x768)
    frame_1_correct_mask = BitmaskCoordinates(np.zeros((768, 1024), dtype=bool))
    frame_1_correct_instance = ObjectInstance(bitmask_object)
    frame_1_correct_instance.set_for_frames(coordinates=frame_1_correct_mask, frames=1)
    label_row.add_object_instance(frame_1_correct_instance)
    assert len(label_row.get_object_instances()) == 2
    label_row.to_encord_dict()  # Both correct dimensions should serialize successfully

    # Add bitmask with incorrect dimensions for frame 0 (256x256 instead of 512x512)
    frame_0_incorrect_mask = BitmaskCoordinates(np.zeros((256, 256), dtype=bool))
    frame_0_incorrect_instance = ObjectInstance(bitmask_object)
    frame_0_incorrect_instance.set_for_frames(coordinates=frame_0_incorrect_mask, frames=0)
    label_row.add_object_instance(frame_0_incorrect_instance)

    # Should fail on serialization
    with pytest.raises(ValueError, match="Bitmask dimensions don't match the media dimensions"):
        label_row.to_encord_dict()

    # Fix frame 0, then add incorrect dimensions for frame 1
    label_row.remove_object(frame_0_incorrect_instance)
    label_row.to_encord_dict()  # back to a valid serializable state

    frame_1_incorrect_mask = BitmaskCoordinates(np.zeros((512, 512), dtype=bool))
    frame_1_incorrect_instance = ObjectInstance(bitmask_object)
    frame_1_incorrect_instance.set_for_frames(coordinates=frame_1_incorrect_mask, frames=1)
    label_row.add_object_instance(frame_1_incorrect_instance)

    # Should fail on serialization due to frame 1
    with pytest.raises(ValueError, match="Bitmask dimensions don't match the media dimensions"):
        label_row.to_encord_dict()


def test_dicom_bitmask_dimension_validation():
    # Create label row metadata for DICOM with series-level dimensions (512x512)
    metadata = LabelRowMetadata(
        label_hash="test_label",
        branch_name="main",
        created_at=datetime.now(),
        last_edited_at=datetime.now(),
        data_hash="test_dicom_hash",
        data_title="Test DICOM",
        data_type="DICOM",
        data_link="",
        dataset_hash="test_dataset",
        dataset_title="Test Dataset",
        label_status=LabelStatus.NOT_LABELLED,
        annotation_task_status=AnnotationTaskStatus.QUEUED,
        workflow_graph_node=None,
        is_shadow_data=False,
        duration=None,
        frames_per_second=None,
        number_of_frames=2,
        height=512,
        width=512,
        audio_codec=None,
        audio_sample_rate=None,
        audio_num_channels=None,
        audio_bit_depth=None,
        spaces={},
    )

    dicom_labels = {
        "label_hash": "test_label",
        "branch_name": "main",
        "created_at": "Thu, 09 Feb 2023 14:12:03 UTC",
        "last_edited_at": "Thu, 09 Feb 2023 14:12:03 UTC",
        "data_hash": "test_dicom_hash",
        "annotation_task_status": "QUEUED",
        "is_shadow_data": False,
        "dataset_hash": "test_dataset",
        "dataset_title": "Test Dataset",
        "data_title": "Test DICOM",
        "data_type": "dicom",
        "data_units": {
            "test_dicom_hash": {
                "data_hash": "test_dicom_hash",
                "data_title": "Test DICOM",
                "data_type": "application/dicom",
                "data_sequence": 0,
                "labels": {
                    "0": {
                        "objects": [],
                        "classifications": [],
                        "metadata": {
                            "dicom_instance_uid": "1.2.3.4.5.6.7.8.9.0",
                            "multiframe_frame_number": None,
                            "file_uri": "test/slice_0",
                            "width": 512,
                            "height": 512,
                        },
                    },
                    "1": {
                        "objects": [],
                        "classifications": [],
                        "metadata": {
                            "dicom_instance_uid": "1.2.3.4.5.6.7.8.9.1",
                            "multiframe_frame_number": None,
                            "file_uri": "test/slice_1",
                            "width": 10,
                            "height": 10,
                        },
                    },
                },
                "metadata": {
                    "patient_id": "test_patient",
                    "study_uid": "1.2.3.4.5",
                    "series_uid": "1.2.3.4.6",
                },
                "data_links": ["test/slice_0", "test/slice_1"],
                "width": 512,
                "height": 512,
            }
        },
        "object_answers": {},
        "classification_answers": {},
        "object_actions": {},
        "label_status": "LABEL_IN_PROGRESS",
    }

    label_row = LabelRowV2(metadata, Mock(), ontology)
    label_row.from_labels_dict(dicom_labels)

    slice_0_metadata = label_row.get_frame_view(0).metadata
    assert slice_0_metadata is not None
    assert slice_0_metadata.model_dump() == {
        "width": 512,
        "height": 512,
        "dicom_instance_uid": "1.2.3.4.5.6.7.8.9.0",
        "multiframe_frame_number": None,
        "file_uri": "test/slice_0",
    }

    slice_1_metadata = label_row.get_frame_view(1).metadata
    assert slice_1_metadata is not None
    assert slice_1_metadata.model_dump() == {
        "width": 10,
        "height": 10,
        "dicom_instance_uid": "1.2.3.4.5.6.7.8.9.1",
        "multiframe_frame_number": None,
        "file_uri": "test/slice_1",
    }

    # Add bitmask with correct dimensions for slice 0
    slice_0_correct_mask = BitmaskCoordinates(np.zeros((512, 512), dtype=bool))
    slice_0_correct_instance = ObjectInstance(bitmask_object)
    slice_0_correct_instance.set_for_frames(coordinates=slice_0_correct_mask, frames=0)
    label_row.add_object_instance(slice_0_correct_instance)
    assert len(label_row.get_object_instances()) == 1

    # Add bitmask with correct dimensions for slice 1
    slice_1_correct_mask = BitmaskCoordinates(np.zeros((10, 10), dtype=bool))
    slice_1_correct_instance = ObjectInstance(bitmask_object)
    slice_1_correct_instance.set_for_frames(coordinates=slice_1_correct_mask, frames=1)
    label_row.add_object_instance(slice_1_correct_instance)
    assert len(label_row.get_object_instances()) == 2

    # Both correct dimensions should serialize successfully
    label_row.to_encord_dict()

    # Add bitmask with incorrect dimensions for slice 0 (256x256 instead of 512x512)
    slice_0_incorrect_mask = BitmaskCoordinates(np.zeros((256, 256), dtype=bool))
    slice_0_incorrect_instance = ObjectInstance(bitmask_object)
    slice_0_incorrect_instance.set_for_frames(coordinates=slice_0_incorrect_mask, frames=0)
    label_row.add_object_instance(slice_0_incorrect_instance)

    # Should fail on serialization
    with pytest.raises(ValueError, match="Bitmask dimensions don't match the media dimensions"):
        label_row.to_encord_dict()
