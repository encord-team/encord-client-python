import datetime

from encord.constants.enums import DataType, SpaceType
from encord.orm.label_row import AnnotationTaskStatus, LabelRowMetadata, LabelStatus

DATA_GROUP_DATA_HASH = "data-group-with-two-text-data-hash"

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
    duration=500,
    frames_per_second=25,
    number_of_frames=500 * 25,
    height=None,
    width=None,
    audio_codec=None,
    audio_bit_depth=None,
    audio_num_channels=None,
    audio_sample_rate=None,
    spaces={
        "text-1-uuid": {
            "space_type": SpaceType.TEXT,
            "child_info": {"layout_key": "main transcript", "is_readonly": False, "file_name": "english.txt"},
            "labels": {},
        },
        "text-2-uuid": {
            "space_type": SpaceType.TEXT,
            "child_info": {"layout_key": "chinese translation", "is_readonly": False, "file_name": "chinese.txt"},
            "labels": {},
        },
    },
)

DATA_GROUP_TWO_TEXT_NO_LABELS = {
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
        "text-1-uuid": {
            "space_type": SpaceType.TEXT,
            "child_info": {"layout_key": "main transcript", "is_readonly": False, "file_name": "english.txt"},
            "labels": {},
        },
        "text-2-uuid": {
            "space_type": SpaceType.TEXT,
            "child_info": {"layout_key": "chinese translation", "is_readonly": False, "file_name": "chinese.txt"},
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

DATA_GROUP_WITH_TWO_TEXT_LABELS = {
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
        "text1": {
            "objectHash": "text1",
            "classifications": [],
            "range": [],
            "createdBy": "NlZNOzo0M5fqmHAPHiNiYs0UQYo2",
            "createdAt": "Thu, 05 Dec 2024 15:24:19 UTC",
            "lastEditedBy": "NlZNOzo0M5fqmHAPHiNiYs0UQYo2",
            "lastEditedAt": "Thu, 05 Dec 2024 15:24:44 UTC",
            "manualAnnotation": True,
            "featureHash": "textFeatureNodeHash",
            "name": "text object",
            "color": "#A4FF00",
            "shape": "text",
            "value": "text_object",
            "spaces": {
                "text-1-uuid": {
                    "range": [[100, 200]],
                },
                "text-2-uuid": {
                    "range": [[300, 500]],
                },
            },
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
            "createdBy": "user1Hash",
            "createdAt": "Tue, 05 Nov 2024 09:41:37 UTC",
            "lastEditedBy": "user1Hash",
            "lastEditedAt": "Tue, 05 Nov 2024 09:41:37 UTC",
            "manualAnnotation": True,
            "range": [],
            "spaces": {
                "text-1-uuid": {
                    "range": [],
                },
                "text-2-uuid": {
                    "range": [],
                },
            },
        },
    },
    "object_actions": {},
    "label_status": "LABEL_IN_PROGRESS",
    "spaces": {
        "text-1-uuid": {
            "space_type": SpaceType.TEXT,
            "child_info": {"layout_key": "main transcript", "is_readonly": False, "file_name": "english.txt"},
            "labels": {},
        },
        "text-2-uuid": {
            "space_type": SpaceType.TEXT,
            "child_info": {"layout_key": "chinese translation", "is_readonly": False, "file_name": "chinese.txt"},
            "labels": {},
        },
    },
    "data_units": {
        DATA_GROUP_DATA_HASH: {
            "data_hash": DATA_GROUP_DATA_HASH,
            "data_title": "",
            "data_sequence": 0,
            "data_type": DataType.GROUP,
            "labels": {
                "objects": [],
                "classifications": [],
            },
        }
    },
}
