import datetime

from encord.constants.enums import DataType, SpaceType
from encord.objects.spaces.types import AudioSpaceInfo, ImageSpaceInfo, TextSpaceInfo, VideoSpaceInfo
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
    },
)
