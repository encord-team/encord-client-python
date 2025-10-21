from encord.constants.enums import DataType, SpaceType

DATA_GROUP_DATA_HASH = "data-group-with-two-audio-data-hash"

DATA_GROUP_TWO_AUDIO_NO_LABELS = {
    "label_hash": "28f0e9d2-51e0-459d-8ffa-2e214da653a9",
    "branch_name": "main",
    "created_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "last_edited_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "data_hash": DATA_GROUP_DATA_HASH,
    "dataset_hash": "b0d93919-a5e8-4418-8dd5-2c51e3977de8",
    "dataset_title": "Dataset with 2 audio",
    "data_title": "two-audio.group",
    "data_type": "group",
    "annotation_task_status": "QUEUED",
    "is_shadow_data": False,
    "object_answers": {},
    "classification_answers": {},
    "object_actions": {},
    "label_status": "LABEL_IN_PROGRESS",
    "spaces": {
        "audio-1-uuid": {
            "space_type": SpaceType.AUDIO,
            "duration_ms": 5 * 60 * 1000,
            "labels": {},
        },
        "audio-2-uuid": {
            "space_type": SpaceType.AUDIO,
            "duration_ms": 5 * 60 * 1000,
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

DATA_GROUP_WITH_TWO_AUDIO_LABELS = {
    "label_hash": "28f0e9d2-51e0-459d-8ffa-2e214da653a9",
    "branch_name": "main",
    "created_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "last_edited_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "data_hash": DATA_GROUP_DATA_HASH,
    "dataset_hash": "b0d93919-a5e8-4418-8dd5-2c51e3977de8",
    "dataset_title": "Dataset with 2 audio",
    "data_title": "two-audio.group",
    "data_type": "group",
    "annotation_task_status": "QUEUED",
    "is_shadow_data": False,
    "object_answers": {
        "speaker1": {
            "objectHash": "speaker1",
            "classifications": [],
            "range": [[100, 200]],
            "createdBy": "NlZNOzo0M5fqmHAPHiNiYs0UQYo2",
            "createdAt": "Thu, 05 Dec 2024 15:24:19 UTC",
            "lastEditedBy": "NlZNOzo0M5fqmHAPHiNiYs0UQYo2",
            "lastEditedAt": "Thu, 05 Dec 2024 15:24:44 UTC",
            "manualAnnotation": True,
            "featureHash": "KVfzNkFy",
            "name": "audio object",
            "color": "#A4FF00",
            "shape": "audio",
            "value": "audio_object",
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
                    "answers": "Text Answer",
                    "featureHash": "OxrtEM+v",
                    "manualAnnotation": True,
                },
            ],
            "range": [],
            "createdBy": "user1Hash",
            "createdAt": "Tue, 05 Nov 2024 09:41:37 UTC",
            "lastEditedBy": "user1Hash",
            "lastEditedAt": "Tue, 05 Nov 2024 09:41:37 UTC",
            "manualAnnotation": True,
        },
    },
    "object_actions": {},
    "label_status": "LABEL_IN_PROGRESS",
    "spaces": {
        "audio-1-uuid": {
            "space_type": SpaceType.AUDIO,
            "duration_ms": 5 * 60 * 1000,
            "labels": {},
        },
        "audio-2-uuid": {
            "space_type": SpaceType.AUDIO,
            "duration_ms": 5 * 60 * 1000,
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
