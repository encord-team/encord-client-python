import datetime

from encord.constants.enums import DataType, SpaceType
from encord.objects.spaces.types import AudioSpaceInfo, HtmlSpaceInfo, ImageSpaceInfo, TextSpaceInfo, VideoSpaceInfo
from encord.orm.label_row import AnnotationTaskStatus, LabelRowMetadata, LabelStatus

DATA_GROUP_DATA_HASH = "all-modalities-data-hash"

VIDEO_SPACE_INFO: VideoSpaceInfo = {
    "space_type": SpaceType.VIDEO,
    "child_info": {"layout_key": "main-video", "file_name": "video.mp4"},
    "number_of_frames": 10,
    "width": 100,
    "height": 100,
    "labels": {},
}

IMAGE_SPACE_INFO: ImageSpaceInfo = {
    "space_type": SpaceType.IMAGE,
    "child_info": {"layout_key": "main-image", "file_name": "image.png"},
    "width": 100,
    "height": 100,
    "labels": {},
}

TEXT_SPACE_INFO: TextSpaceInfo = {
    "space_type": SpaceType.TEXT,
    "child_info": {"layout_key": "main-text", "file_name": "text.txt"},
    "labels": {},
}

AUDIO_SPACE_INFO: AudioSpaceInfo = {
    "space_type": SpaceType.AUDIO,
    "child_info": {"layout_key": "main-audio", "file_name": "audio.mp3"},
    "duration_ms": 10000,
    "labels": {},
}

HTML_SPACE_INFO: HtmlSpaceInfo = {
    "space_type": SpaceType.HTML,
    "child_info": {"layout_key": "main-html", "file_name": "document.html"},
    "labels": {},
}

DATA_GROUP_NO_LABELS = {
    "label_hash": "28f0e9d2-51e0-459d-8ffa-2e214da653a9",
    "branch_name": "main",
    "created_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "last_edited_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "data_hash": DATA_GROUP_DATA_HASH,
    "dataset_hash": "b0d93919-a5e8-4418-8dd5-2c51e3977de8",
    "dataset_title": "Dataset with all modalities",
    "data_title": "all-modalities-group",
    "data_type": "group",
    "annotation_task_status": "QUEUED",
    "is_shadow_data": False,
    "object_answers": {},
    "classification_answers": {},
    "object_actions": {},
    "label_status": "LABEL_IN_PROGRESS",
    "spaces": {
        "video-uuid": {
            "space_type": SpaceType.VIDEO,
            "title": "Video",
            "width": 100,
            "height": 100,
            "number_of_frames": 10,
            "labels": {},
        },
        "image-uuid": {
            "space_type": SpaceType.IMAGE,
            "title": "Image",
            "width": 100,
            "height": 100,
            "labels": {},
        },
        "text-uuid": {
            "space_type": SpaceType.TEXT,
            "title": "Text",
            "labels": {},
        },
        "audio-uuid": {
            "space_type": SpaceType.AUDIO,
            "title": "Audio",
            "duration_ms": 10000,
            "labels": {},
        },
        "html-uuid": {
            "space_type": SpaceType.HTML,
            "title": "HTML",
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


DATA_GROUP_WITH_LABELS = {
    "label_hash": "28f0e9d2-51e0-459d-8ffa-2e214da653a9",
    "branch_name": "main",
    "created_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "last_edited_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "data_hash": DATA_GROUP_DATA_HASH,
    "dataset_hash": "b0d93919-a5e8-4418-8dd5-2c51e3977de8",
    "dataset_title": "Dataset with all modalities",
    "data_title": "all-modalities-group",
    "data_type": "group",
    "annotation_task_status": "QUEUED",
    "is_shadow_data": False,
    "object_answers": {
        # Video/Image object (frame-based)
        "video-box-object": {
            "objectHash": "video-box-object",
            "classifications": [],
        },
        "image-box-object": {
            "objectHash": "image-box-object",
            "classifications": [],
        },
        # Audio object (range-based)
        "audio-object": {
            "objectHash": "audio-object",
            "classifications": [],
            "range": [],
            "createdBy": "user@example.com",
            "createdAt": "Thu, 05 Dec 2024 15:24:19 UTC",
            "lastEditedBy": "user@example.com",
            "lastEditedAt": "Thu, 05 Dec 2024 15:24:44 UTC",
            "manualAnnotation": True,
            "featureHash": "KVfzNkFy",
            "name": "audio object 1",
            "color": "#A4FF00",
            "shape": "audio",
            "value": "audio_object_1",
            "spaces": {
                "audio-uuid": {
                    "range": [[100, 200]],
                    "type": "frame",
                },
            },
        },
        # Text object (range-based)
        "text-object": {
            "objectHash": "text-object",
            "classifications": [],
            "range": [],
            "createdBy": "user@example.com",
            "createdAt": "Thu, 05 Dec 2024 15:24:19 UTC",
            "lastEditedBy": "user@example.com",
            "lastEditedAt": "Thu, 05 Dec 2024 15:24:44 UTC",
            "manualAnnotation": True,
            "featureHash": "textFeatureNodeHash",
            "name": "text object",
            "color": "#A4FF00",
            "shape": "text",
            "value": "text_object",
            "spaces": {
                "text-uuid": {
                    "range": [[0, 4]],
                    "type": "frame",
                },
            },
        },
    },
    "classification_answers": {
        # Video classification (frame-based)
        "video-classification": {
            "classificationHash": "video-classification",
            "featureHash": "jPOcEsbw",
            "classifications": [
                {
                    "name": "Text classification",
                    "value": "text_classification",
                    "answers": "Video answer",
                    "featureHash": "OxrtEM+v",
                    "manualAnnotation": True,
                }
            ],
            "spaces": {
                "video-uuid": {
                    "range": [[0, 0]],
                    "type": "frame",
                },
            },
        },
        # Image classification (frame-based, uses checklist)
        "image-classification": {
            "classificationHash": "image-classification",
            "featureHash": "3DuQbFxo",
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
            "spaces": {
                "image-uuid": {
                    "range": [[0, 0]],
                    "type": "frame",
                },
            },
        },
        # Audio classification (range-based)
        "audio-classification": {
            "classificationHash": "audio-classification",
            "featureHash": "NzIxNTU1",
            "classifications": [],
            "createdBy": "user@example.com",
            "createdAt": "Tue, 05 Nov 2024 09:41:37 UTC",
            "lastEditedBy": "user@example.com",
            "lastEditedAt": "Tue, 05 Nov 2024 09:41:37 UTC",
            "manualAnnotation": True,
            "range": [],
            "spaces": {
                "audio-uuid": {
                    "range": [],
                    "type": "frame",
                },
            },
        },
        # Text classification (range-based)
        "text-classification": {
            "classificationHash": "text-classification",
            "featureHash": "textClass2",
            "classifications": [
                {
                    "name": "Text classification 2",
                    "value": "text_classification_2",
                    "answers": "Text space answer",
                    "featureHash": "textAttr2",
                    "manualAnnotation": True,
                }
            ],
            "createdBy": "user@example.com",
            "createdAt": "Tue, 05 Nov 2024 09:41:37 UTC",
            "lastEditedBy": "user@example.com",
            "lastEditedAt": "Tue, 05 Nov 2024 09:41:37 UTC",
            "manualAnnotation": True,
            "range": [],
            "spaces": {
                "text-uuid": {
                    "range": [],
                    "type": "frame",
                },
            },
        },
    },
    "object_actions": {},
    "label_status": "LABEL_IN_PROGRESS",
    "spaces": {
        "video-uuid": {
            "space_type": SpaceType.VIDEO,
            "child_info": {"layout_key": "main-video", "file_name": "video.mp4"},
            "number_of_frames": 10,
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
                            "createdBy": "user@example.com",
                            "confidence": 1,
                            "objectHash": "video-box-object",
                            "lastEditedAt": "Wed, 18 Jan 2023 17:23:24 UTC",
                            "featureHash": "MjI2NzEy",
                            "manualAnnotation": True,
                            "boundingBox": {"h": 0.1, "w": 0.1, "x": 0.1, "y": 0.1},
                        },
                    ],
                    "classifications": [
                        {
                            "name": "Text classification",
                            "value": "text_classification",
                            "createdAt": "Tue, 17 Jan 2023 11:45:01 UTC",
                            "createdBy": "user@example.com",
                            "confidence": 1,
                            "featureHash": "jPOcEsbw",
                            "lastEditedAt": "Tue, 17 Jan 2023 11:45:01 UTC",
                            "lastEditedBy": "user@example.com",
                            "classificationHash": "video-classification",
                            "manualAnnotation": True,
                        },
                    ],
                },
            },
        },
        "image-uuid": {
            "space_type": SpaceType.IMAGE,
            "child_info": {"layout_key": "main-image", "file_name": "image.png"},
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
                            "createdBy": "user@example.com",
                            "confidence": 1,
                            "objectHash": "image-box-object",
                            "lastEditedAt": "Wed, 18 Jan 2023 17:23:24 UTC",
                            "featureHash": "MjI2NzEy",
                            "manualAnnotation": True,
                            "boundingBox": {"h": 0.2, "w": 0.2, "x": 0.2, "y": 0.2},
                        },
                    ],
                    "classifications": [
                        {
                            "name": "Checklist classification",
                            "value": "checklist_classification",
                            "createdAt": "Tue, 17 Jan 2023 11:45:01 UTC",
                            "createdBy": "user@example.com",
                            "confidence": 1,
                            "featureHash": "3DuQbFxo",
                            "lastEditedAt": "Tue, 17 Jan 2023 11:45:01 UTC",
                            "lastEditedBy": "user@example.com",
                            "classificationHash": "image-classification",
                            "manualAnnotation": True,
                        },
                    ],
                },
            },
        },
        "text-uuid": {
            "space_type": SpaceType.TEXT,
            "child_info": {"layout_key": "main-text", "file_name": "text.txt"},
            "labels": {},
        },
        "audio-uuid": {
            "space_type": SpaceType.AUDIO,
            "child_info": {"layout_key": "main-audio", "file_name": "audio.mp3"},
            "duration_ms": 10000,
            "labels": {},
        },
        "html-uuid": {
            "space_type": SpaceType.HTML,
            "child_info": {"layout_key": "main-html", "file_name": "document.html"},
            "labels": {},
        },
    },
    "data_units": {
        DATA_GROUP_DATA_HASH: {
            "data_hash": DATA_GROUP_DATA_HASH,
            "data_sequence": 0,
            "data_title": "",
            "data_type": DataType.GROUP,
            "labels": {
                "objects": [],
                "classifications": [],
            },
        }
    },
}


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
        "video-uuid": VIDEO_SPACE_INFO,
        "image-uuid": IMAGE_SPACE_INFO,
        "text-uuid": TEXT_SPACE_INFO,
        "audio-uuid": AUDIO_SPACE_INFO,
        "html-uuid": HTML_SPACE_INFO,
    },
)
