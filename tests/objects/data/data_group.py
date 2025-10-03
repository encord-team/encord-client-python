from encord.constants.enums import DataType

INPUT_DATA_GROUP_LABELS = {
    "label_hash": "28f0e9d2-51e0-459d-8ffa-2e214da653a9",
    "branch_name": "main",
    "created_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "last_edited_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "data_hash": "cd57cf5c-2541-4a46-a836-444540ee987a",
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
            "range": [{"space": "child-1-uuid", "frames": [[0, 1]]}, {"space": "child-2-uuid", "frames": [[0, 0], [2, 2]]}],
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
        }
    },
    "data_units": {
        "cd57cf5c-2541-4a46-a836-444540ee987a": {
            "data_hash": "cd57cf5c-2541-4a46-a836-444540ee987a",
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
                    "classifications": []
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
                    "classifications": []
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
                    "classifications": []
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
                    "classifications": []
                }
            },
        }
    },
}

OUTPUT_DATA_GROUP_LABELS = {
    "label_hash": "28f0e9d2-51e0-459d-8ffa-2e214da653a9",
    "branch_name": "main",
    "created_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "last_edited_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "data_hash": "cd57cf5c-2541-4a46-a836-444540ee987a",
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
    "data_units": {
        "cd57cf5c-2541-4a46-a836-444540ee987a": {
            "data_hash": "cd57cf5c-2541-4a46-a836-444540ee987a",
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
                    "classifications": []
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
                    "classifications": []
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
                    "classifications": []
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
                    "classifications": []
                }
            },
        }
    },
}
