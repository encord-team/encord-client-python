import datetime

from encord.constants.enums import DataType, SpaceType
from encord.orm.label_row import AnnotationTaskStatus, LabelRowMetadata, LabelStatus

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

DATA_GROUP_TWO_VIDEOS_NO_LABELS = {
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
            "space_type": SpaceType.VIDEO,
            "number_of_frames": 10,
            "labels": {},
        },
        "video-2-uuid": {
            "space_type": SpaceType.VIDEO,
            "number_of_frames": 10,
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

DATA_GROUP_WITH_TWO_VIDEOS_LABELS = {
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
        "dynamicPoint1": {"classifications": [], "objectHash": "dynamicPoint1"},
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
    },
    "object_actions": {
        "dynamicPoint1": {
            "objectHash": "dynamicPoint1",
            "actions": [
                {
                    "name": "First name",
                    "range": [[0, 0]],
                    "value": "first_name",
                    "answers": "Some dynamic Text",
                    "dynamic": True,
                    "featureHash": "OTkxMjU1",
                    "shouldPropagate": False,
                    "manualAnnotation": True,
                },
                {
                    "name": "First name",
                    "range": [[1, 1]],
                    "value": "first_name",
                    "answers": "Another dynamic text",
                    "dynamic": True,
                    "featureHash": "OTkxMjU1",
                    "shouldPropagate": False,
                    "manualAnnotation": True,
                },
            ],
        },
    },
    "label_status": "LABEL_IN_PROGRESS",
    "spaces": {
        "video-1-uuid": {
            "space_type": SpaceType.VIDEO,
            "number_of_frames": 10,
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
                        {
                            "name": "Keypoint Dynamic Answers",
                            "color": "#FE9200",
                            "shape": "point",
                            "value": "keypoint_dynamic_answers",
                            "createdAt": "Tue, 17 Jan 2023 17:23:10 UTC",
                            "createdBy": "denis@cord.tech",
                            "confidence": 1,
                            "objectHash": "dynamicPoint1",
                            "lastEditedAt": "Wed, 18 Jan 2023 17:23:24 UTC",
                            "featureHash": "MTY2MTQx",
                            "manualAnnotation": True,
                            "point": {"0": {"x": 0.5, "y": 0.5}},
                        },
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
                        {
                            "name": "Keypoint Dynamic Answers",
                            "color": "#FE9200",
                            "shape": "point",
                            "value": "keypoint_dynamic_answers",
                            "createdAt": "Tue, 17 Jan 2023 17:23:10 UTC",
                            "createdBy": "denis@cord.tech",
                            "confidence": 1,
                            "objectHash": "dynamicPoint1",
                            "lastEditedAt": "Wed, 18 Jan 2023 17:23:24 UTC",
                            "featureHash": "MTY2MTQx",
                            "manualAnnotation": True,
                            "point": {"0": {"x": 0.6, "y": 0.6}},
                        },
                    ],
                    "classifications": [],
                },
            },
        },
        "video-2-uuid": {
            "space_type": SpaceType.VIDEO,
            "number_of_frames": 10,
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
