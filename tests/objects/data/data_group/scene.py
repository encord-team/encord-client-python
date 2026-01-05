import datetime

from encord.constants.enums import DataType, SpaceType
from encord.orm.label_row import AnnotationTaskStatus, LabelRowMetadata, LabelStatus

SCENE_DATA_HASH = "28f0e9d2-51e0-459d-8ffa-2e214da653a0"

SCENE_METADATA = LabelRowMetadata(
    label_hash="",
    branch_name="main",
    created_at=datetime.datetime.now(),
    last_edited_at=datetime.datetime.now(),
    data_hash=SCENE_DATA_HASH,
    data_title="Scene",
    data_type=DataType.SCENE,
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
        "path/to/file1.pcd": {
            "space_type": SpaceType.POINT_CLOUD,
            "labels": {"objects": [], "classifications": []},
            "scene_info": {"event_index": 0, "stream_id": "lidar1", "uri": "path/to/file1.pcd"},
        },
        "path/to/file2.pcd": {
            "space_type": SpaceType.POINT_CLOUD,
            "labels": {"objects": [], "classifications": []},
            "scene_info": {"event_index": 0, "stream_id": "lidar1", "uri": "path/to/file2.pcd"},
        },
    },
)

SCENE_NO_LABELS = {
    "label_hash": "28f0e9d2-51e0-459d-8ffa-2e214da653a9",
    "branch_name": "main",
    "created_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "last_edited_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "data_hash": SCENE_DATA_HASH,
    "dataset_hash": "b0d93919-a5e8-4418-8dd5-2c51e3977de8",
    "dataset_title": "Dataset with Scene",
    "data_title": "scene",
    "data_type": "scene",
    "annotation_task_status": "QUEUED",
    "is_shadow_data": False,
    "object_answers": {},
    "classification_answers": {},
    "object_actions": {},
    "label_status": "LABEL_IN_PROGRESS",
    "spaces": {
        "path/to/file1.pcd": {
            "space_type": SpaceType.POINT_CLOUD,
        },
        "path/to/file2.pcd": {
            "space_type": SpaceType.POINT_CLOUD,
        },
    },
    "data_units": {
        SCENE_DATA_HASH: {
            "data_hash": SCENE_DATA_HASH,
            "data_sequence": 0,
            "data_title": "",
            "data_type": DataType.SCENE,
            "labels": {},
        }
    },
}
