import datetime

from encord.constants.enums import DataType, SpaceType
from encord.orm.label_row import AnnotationTaskStatus, LabelRowMetadata, LabelStatus
from encord.orm.label_space import SpaceInfo

DATA_GROUP_DATA_HASH = "28f0e9d2-51e0-459d-8ffa-2e214da653a9"

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
)

INPUT_DATA_GROUP_LABELS = {
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
        "0gCzNuLS": {
            "objectHash": "0gCzNuLS",
            "featureHash": "MjI2NzEy",
            "classifications": [],
            "spaces": {
                "child-1-uuid": {"range": [[0, 1]]},
            },
            "range": [
                {"space": "child-1-uuid", "frames": [[0, 1]]},
                {"space": "child-2-uuid", "frames": [[0, 0], [2, 2]]},
            ],
            "createdAt": "Tue, 22 Oct 2024 09:43:47 GMT",
            "createdBy": "denis@cord.tech",
            "lastEditedAt": "Tue, 22 Oct 2024 09:43:47 GMT",
            "lastEditedBy": "denis@cord.tech",
        },
    },
    "classification_answers": {},
    "object_actions": {},
    "label_status": "LABEL_IN_PROGRESS",
    "spaces": {
        "child-1-uuid": {
            "space_type": "data-group-child",
            "data_type": "video",
        },
        "child-2-uuid": {
            "space_type": "data-group-child",
            "data_type": "video",
        },
    },
    "data_units": {
        DATA_GROUP_DATA_HASH: {
            "data_hash": DATA_GROUP_DATA_HASH,
            "data_sequence": 0,
            "data_title": "",
            "data_type": DataType.GROUP,
            "labels": {
                "child-1-uuid#0": {
                    "objects": [
                        {
                            "name": "box",
                            "color": "#D33115",
                            "shape": "bounding_box",
                            "value": "box",
                            "createdAt": "Tue, 17 Jan 2023 17:23:10 UTC",
                            "createdBy": "denis@cord.tech",
                            "confidence": 1,
                            "objectHash": "0gCzNuLS",
                            "lastEditedAt": "Wed, 18 Jan 2023 17:23:24 UTC",
                            "featureHash": "MjI2NzEy",
                            "manualAnnotation": True,
                            "boundingBox": {"h": 0.1291, "w": 0.1296, "x": 0.4287, "y": 0.2615},
                        },
                    ],
                    "classifications": [],
                },
                "child-1-uuid#1": {
                    "objects": [
                        {
                            "name": "box",
                            "color": "#D33115",
                            "shape": "bounding_box",
                            "value": "box",
                            "createdAt": "Tue, 17 Jan 2023 17:23:10 UTC",
                            "createdBy": "denis@cord.tech",
                            "confidence": 1,
                            "objectHash": "0gCzNuLS",
                            "lastEditedAt": "Wed, 18 Jan 2023 17:23:24 UTC",
                            "featureHash": "MjI2NzEy",
                            "manualAnnotation": True,
                            "boundingBox": {"h": 0.1291, "w": 0.1296, "x": 0.4287, "y": 0.2615},
                        },
                    ],
                    "classifications": [],
                },
                "child-2-uuid#0": {
                    "objects": [
                        {
                            "name": "box",
                            "color": "#D33115",
                            "shape": "bounding_box",
                            "value": "box",
                            "createdAt": "Tue, 17 Jan 2023 17:23:10 UTC",
                            "createdBy": "denis@cord.tech",
                            "confidence": 1,
                            "objectHash": "0gCzNuLS",
                            "lastEditedAt": "Wed, 18 Jan 2023 17:23:24 UTC",
                            "featureHash": "MjI2NzEy",
                            "manualAnnotation": True,
                            "boundingBox": {"h": 0.1291, "w": 0.1296, "x": 0.4287, "y": 0.2615},
                        },
                    ],
                    "classifications": [],
                },
                "child-2-uuid#2": {
                    "objects": [
                        {
                            "name": "box",
                            "color": "#D33115",
                            "shape": "bounding_box",
                            "value": "box",
                            "createdAt": "Tue, 17 Jan 2023 17:23:10 UTC",
                            "createdBy": "denis@cord.tech",
                            "confidence": 1,
                            "objectHash": "0gCzNuLS",
                            "lastEditedAt": "Wed, 18 Jan 2023 17:23:24 UTC",
                            "featureHash": "MjI2NzEy",
                            "manualAnnotation": True,
                            "boundingBox": {"h": 0.1291, "w": 0.1296, "x": 0.4287, "y": 0.2615},
                        },
                    ],
                    "classifications": [],
                },
            },
        }
    },
}

OUTPUT_DATA_GROUP_LABELS = {
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
        "0gCzNuLS": {
            "objectHash": "0gCzNuLS",
            "classifications": [],
        },
    },
    "classification_answers": {},
    "object_actions": {},
    "label_status": "LABEL_IN_PROGRESS",
    ## TODO:
    # "spaces": {
    #     "child-1-uuid": {
    #         "space_type": "data-group-child",
    #         "data_type": "video",
    #     }
    # },
    "data_units": {
        DATA_GROUP_DATA_HASH: {
            "data_hash": DATA_GROUP_DATA_HASH,
            "labels": {
                "child-1-uuid#0": {
                    "objects": [
                        {
                            "name": "Box",
                            "color": "#D33115",
                            "shape": "bounding_box",
                            "value": "box",
                            "createdAt": "Tue, 17 Jan 2023 17:23:10 UTC",
                            "createdBy": "denis@cord.tech",
                            "confidence": 1,
                            "objectHash": "0gCzNuLS",
                            "lastEditedAt": "Wed, 18 Jan 2023 17:23:24 UTC",
                            "featureHash": "MjI2NzEy",
                            "manualAnnotation": True,
                            "boundingBox": {"h": 0.1291, "w": 0.1296, "x": 0.4287, "y": 0.2615},
                        },
                    ],
                    "classifications": [],
                },
                "child-1-uuid#1": {
                    "objects": [
                        {
                            "name": "Box",
                            "color": "#D33115",
                            "shape": "bounding_box",
                            "value": "box",
                            "createdAt": "Tue, 17 Jan 2023 17:23:10 UTC",
                            "createdBy": "denis@cord.tech",
                            "confidence": 1,
                            "objectHash": "0gCzNuLS",
                            "lastEditedAt": "Wed, 18 Jan 2023 17:23:24 UTC",
                            "featureHash": "MjI2NzEy",
                            "manualAnnotation": True,
                            "boundingBox": {"h": 0.1291, "w": 0.1296, "x": 0.4287, "y": 0.2615},
                        },
                    ],
                    "classifications": [],
                },
                "child-2-uuid#0": {
                    "objects": [
                        {
                            "name": "Box",
                            "color": "#D33115",
                            "shape": "bounding_box",
                            "value": "box",
                            "createdAt": "Tue, 17 Jan 2023 17:23:10 UTC",
                            "createdBy": "denis@cord.tech",
                            "confidence": 1,
                            "objectHash": "0gCzNuLS",
                            "lastEditedAt": "Wed, 18 Jan 2023 17:23:24 UTC",
                            "featureHash": "MjI2NzEy",
                            "manualAnnotation": True,
                            "boundingBox": {"h": 0.1291, "w": 0.1296, "x": 0.4287, "y": 0.2615},
                        },
                    ],
                    "classifications": [],
                },
                "child-2-uuid#2": {
                    "objects": [
                        {
                            "name": "Box",
                            "color": "#D33115",
                            "shape": "bounding_box",
                            "value": "box",
                            "createdAt": "Tue, 17 Jan 2023 17:23:10 UTC",
                            "createdBy": "denis@cord.tech",
                            "confidence": 1,
                            "objectHash": "0gCzNuLS",
                            "lastEditedAt": "Wed, 18 Jan 2023 17:23:24 UTC",
                            "featureHash": "MjI2NzEy",
                            "manualAnnotation": True,
                            "boundingBox": {"h": 0.1291, "w": 0.1296, "x": 0.4287, "y": 0.2615},
                        },
                    ],
                    "classifications": [],
                },
            },
        }
    },
}

EMPTY_DATA_GROUP_LABELS = {
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
        "video-1-uuid": {
            "space_type": SpaceType.VISION,
            "data_type": "video",
            "labels": {},
        },
        "video-2-uuid": {
            "space_type": SpaceType.VISION,
            "data_type": "video",
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

EXPECTED_DATA_GROUP_WITH_LABELS = {
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
    "classification_answers": {},
    "object_actions": {},
    "label_status": "LABEL_IN_PROGRESS",
    "spaces": {
        "video-1-uuid": {
            "space_type": SpaceType.VISION,
            "data_type": DataType.VIDEO,
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
                        },
                    ],
                    "classifications": [],
                },
                "1": {
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
                            "boundingBox": {"h": 0.2, "w": 0.2, "x": 0.2, "y": 0.2},
                        },
                    ],
                    "classifications": [],
                }
            }
        },
        "video-2-uuid": {
            "space_type": SpaceType.VISION,
            "data_type": DataType.VIDEO,
            "labels": {},
        },
    },
    "data_units": {
        DATA_GROUP_DATA_HASH: {
            "data_hash": DATA_GROUP_DATA_HASH,
            "data_title": "",
            "data_type": DataType.GROUP,
            "labels": {},
        }
    },
}
