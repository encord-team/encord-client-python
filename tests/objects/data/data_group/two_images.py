import datetime

from encord.constants.enums import DataType, SpaceType
from encord.orm.label_row import AnnotationTaskStatus, LabelRowMetadata, LabelStatus

DATA_GROUP_DATA_HASH = "data-group-with-two-images-data-hash"

DATA_GROUP_METADATA = LabelRowMetadata(
    label_hash="",
    branch_name="main",
    created_at=datetime.datetime.now(),
    last_edited_at=datetime.datetime.now(),
    data_hash=DATA_GROUP_DATA_HASH,
    data_title="",
    data_type=DataType.GROUP,
    data_link="",
    dataset_hash="",
    dataset_title="",
    label_status=LabelStatus.NOT_LABELLED,
    annotation_task_status=AnnotationTaskStatus.QUEUED,
    workflow_graph_node=None,
    is_shadow_data=False,
    duration=100,
    frames_per_second=25,
    number_of_frames=100 * 25,
    height=None,
    width=None,
    audio_codec=None,
    audio_bit_depth=None,
    audio_num_channels=None,
    audio_sample_rate=None,
    spaces={
        "image-1-uuid": {
            "space_type": SpaceType.IMAGE,
            "child_info": {"layout_key": "front", "is_readonly": False, "file_name": "front.jpg"},
            "number_of_frames": 10,
            "width": 100,
            "height": 100,
            "labels": {},
        },
        "image-2-uuid": {
            "space_type": SpaceType.IMAGE,
            "child_info": {"layout_key": "back", "is_readonly": False, "file_name": "back.jpg"},
            "number_of_frames": 10,
            "width": 100,
            "height": 100,
            "labels": {},
        },
    },
)

DATA_GROUP_TWO_IMAGES_NO_LABELS = {
    "label_hash": "28f0e9d2-51e0-459d-8ffa-2e214da653a9",
    "branch_name": "main",
    "created_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "last_edited_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "data_hash": DATA_GROUP_DATA_HASH,
    "dataset_hash": "b0d93919-a5e8-4418-8dd5-2c51e3977de8",
    "dataset_title": "Dataset with 2 frame video",
    "data_title": "two-frame-video.mp4",
    "data_type": "group",
    "annotation_task_status": "QUEUED",
    "is_shadow_data": False,
    "object_answers": {},
    "classification_answers": {},
    "object_actions": {},
    "label_status": "LABEL_IN_PROGRESS",
    "spaces": {
        "image-1-uuid": {
            "space_type": SpaceType.IMAGE,
            "title": "Image 1",
            "width": 100,
            "height": 100,
            "labels": {},
        },
        "image-2-uuid": {
            "space_type": SpaceType.IMAGE,
            "title": "Image 2",
            "width": 100,
            "height": 100,
            "labels": {},
        },
    },
    "data_units": {
        DATA_GROUP_DATA_HASH: {
            "data_hash": DATA_GROUP_DATA_HASH,
            "data_sequence": 0,
            "data_title": "",
            "data_type": DataType.GROUP,
            "labels": {},
        }
    },
}

DATA_GROUP_WITH_TWO_IMAGES_LABELS = {
    "label_hash": "28f0e9d2-51e0-459d-8ffa-2e214da653a9",
    "branch_name": "main",
    "created_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "last_edited_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "data_hash": DATA_GROUP_DATA_HASH,
    "dataset_hash": "b0d93919-a5e8-4418-8dd5-2c51e3977de8",
    "dataset_title": "Dataset with 2 frame video",
    "data_title": "two-frame-video.mp4",
    "data_type": "group",
    "annotation_task_status": "QUEUED",
    "is_shadow_data": False,
    "object_answers": {
        "object1": {
            "objectHash": "object1",
            "classifications": [],
        },
    },
    "classification_answers": {
        "classification1": {
            "classificationHash": "classification1",
            "featureHash": "jPOcEsbw",
            "classifications": [
                {
                    "name": "Text classification",
                    "value": "text_classification",
                    "answers": "Rousseau",
                    "featureHash": "OxrtEM+v",
                    "manualAnnotation": True,
                }
            ],
        },
        "checklist_classification_hash": {
            "classifications": [
                {
                    "name": "Checklist classification",
                    "value": "checklist_classification",
                    "answers": [
                        {
                            "name": "Checklist classification answer 1",
                            "value": "checklist_classification_answer_1",
                            "featureHash": "fvLjF0qZ",
                        }
                    ],
                    "featureHash": "9mwWr3OE",
                    "manualAnnotation": True,
                }
            ],
            "classificationHash": "checklist_classification_hash",
            "featureHash": "3DuQbFxo",
        },
    },
    "object_actions": {},
    "label_status": "LABEL_IN_PROGRESS",
    "spaces": {
        "image-1-uuid": {
            "space_type": SpaceType.IMAGE,
            "child_info": {"layout_key": "front", "is_readonly": False, "file_name": "front.jpg"},
            "width": 100,
            "height": 100,
            "labels": {
                "0": {
                    "objects": [
                        {
                            "name": "Box",
                            "color": "#D33115",
                            "shape": "bounding_box",
                            "value": "box",
                            "createdAt": "Tue, 17 Jan 2023 17:23:10 UTC",
                            "createdBy": "denis@cord.tech",
                            "confidence": 1,
                            "objectHash": "object1",
                            "lastEditedAt": "Wed, 18 Jan 2023 17:23:24 UTC",
                            "featureHash": "MjI2NzEy",
                            "manualAnnotation": True,
                            "boundingBox": {"h": 0.1, "w": 0.1, "x": 0.1, "y": 0.1},
                        }
                    ],
                    "classifications": [
                        {
                            "name": "Text classification",
                            "value": "text_classification",
                            "createdAt": "Tue, 17 Jan 2023 11:45:01 UTC",
                            "createdBy": "denis@cord.tech",
                            "confidence": 1,
                            "featureHash": "jPOcEsbw",
                            "lastEditedAt": "Tue, 17 Jan 2023 11:45:01 UTC",
                            "lastEditedBy": "denis@cord.tech",
                            "classificationHash": "classification1",
                            "manualAnnotation": True,
                        },
                    ],
                },
            },
        },
        "image-2-uuid": {
            "space_type": SpaceType.IMAGE,
            "child_info": {"layout_key": "back", "is_readonly": False, "file_name": "back.jpg"},
            "width": 100,
            "height": 100,
            "labels": {
                "0": {
                    "objects": [],
                    "classifications": [
                        {
                            "classificationHash": "checklist_classification_hash",
                            "featureHash": "3DuQbFxo",
                            "name": "Checklist classification",
                            "value": "checklist_classification",
                            "createdAt": "Wed, 26 Nov 2025 13:41:34 UTC",
                            "confidence": 1.0,
                            "manualAnnotation": True,
                            "lastEditedAt": "Mon, 04 May 2020 23:00:00 UTC",
                            "lastEditedBy": "timmy",
                        }
                    ],
                }
            },
        },
    },
    "data_units": {
        DATA_GROUP_DATA_HASH: {
            "data_hash": DATA_GROUP_DATA_HASH,
            "data_title": "",
            "data_type": DataType.GROUP,
            "labels": {
                "objects": [],
                "classifications": [],
            },
            "data_sequence": 0,
        }
    },
}
