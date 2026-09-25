"""Label blob for a self-contained (MCAP) scene.

Such a scene is continuous: it has no frame grid, positions are nanosecond offsets and the enriched label row
response marks it with ``scene.isContinuous``. It carries no space metadata, so point cloud labels sit in the
data unit under ``stream@timestamp_ns`` keys. Root classifications are range based.
"""

BOX_HASH = "MjI2NzEy"  # "Box" in all_types_structure
OBJECT_HASH = "mcapObj01"
DATA_HASH = "0d0c3c8e-2f75-4b9e-9a7d-4c1a1b2c3d4e"

TEXT_CLASSIFICATION_HASH = "jPOcEsbw"  # a text classification in all_types_structure
CLASSIFICATION_INSTANCE_HASH = "mcapCls01"
CLASSIFICATION_RANGE = [0, 3_000_000_000]

KEYFRAME_NS = 1_000_000_000
DELETE_NS = 2_000_000_000  # the editor closes every object with a `delete`, one past its last nanosecond

BOX = {"h": 0.1, "w": 0.1, "x": 0.2, "y": 0.2}
ZERO_BOX = {"h": 0, "w": 0, "x": 0, "y": 0}

BOX_ENTRY = {
    "name": "Box",
    "color": "#D33115",
    "shape": "bounding_box",
    "value": "box",
    "createdAt": "Mon, 11 Jul 2022 17:10:51 UTC",
    "createdBy": "annotator@encord.com",
    "lastEditedAt": "Mon, 11 Jul 2022 17:10:51 UTC",
    "lastEditedBy": "annotator@encord.com",
    "confidence": 1,
    "objectHash": OBJECT_HASH,
    "featureHash": BOX_HASH,
    "manualAnnotation": True,
    "boundingBox": BOX,
}

BOX_DELETE_ENTRY = {**BOX_ENTRY, "boundingBox": ZERO_BOX, "event": "delete"}

MCAP_SCENE_LABELS = {
    "label_hash": "5f1a6e2e-0b7a-4a3e-9e1a-2b3c4d5e6f70",
    "branch_name": "main",
    "created_at": "2026-09-01 10:00:00",
    "last_edited_at": "2026-09-01 10:00:00",
    "data_hash": DATA_HASH,
    "dataset_hash": "b0d93919-a5e8-4418-8dd5-2c51e3977de8",
    "dataset_title": "Scenes",
    "data_title": "recording.mcap",
    "data_type": "scene",
    "annotation_task_status": "QUEUED",
    "is_shadow_data": False,
    "scene": {"isContinuous": True},
    "object_answers": {
        OBJECT_HASH: {
            "objectHash": OBJECT_HASH,
            "featureHash": BOX_HASH,
            "classifications": [],
            "range": None,
        }
    },
    "classification_answers": {
        CLASSIFICATION_INSTANCE_HASH: {
            "classificationHash": CLASSIFICATION_INSTANCE_HASH,
            "featureHash": TEXT_CLASSIFICATION_HASH,
            "classifications": [
                {
                    "name": "Text classification",
                    "value": "text_classification",
                    "answers": "Text Answer",
                    "featureHash": "OxrtEM+v",
                    "manualAnnotation": True,
                }
            ],
            "range": [CLASSIFICATION_RANGE],
            "spaces": {},
            "createdAt": "Wed, 02 Sep 2026 13:58:07 GMT",
            "createdBy": "annotator@encord.com",
            "lastEditedAt": "Wed, 02 Sep 2026 13:58:07 GMT",
            "lastEditedBy": "annotator@encord.com",
            "confidence": 1.0,
            "manualAnnotation": True,
        }
    },
    "object_actions": {},
    "label_status": "LABEL_IN_PROGRESS",
    "data_units": {
        DATA_HASH: {
            "data_hash": DATA_HASH,
            "data_title": "recording.mcap",
            "data_link": "",
            "data_type": "application/mcap",
            "data_sequence": 0,
            "width": 0,
            "height": 0,
            "data_fps": 0,
            "labels": {
                str(KEYFRAME_NS): {"objects": [BOX_ENTRY], "classifications": []},
                str(DELETE_NS): {"objects": [BOX_DELETE_ENTRY], "classifications": []},
            },
        }
    },
    "spaces": {},
}
