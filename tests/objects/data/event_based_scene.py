"""Label blob for a continuous (event-based) scene: one cuboid object with sparse events.

The enriched response marks the scene continuous, and every stored entry but the first carries an `event` tag
(the first is untagged, which reads as an upsert). `dense_scene_labels()` is the same geometry as a frame-based
scene: no scene metadata and no tags, since a tag on a frame-based row is refused at parse.
"""

from copy import deepcopy
from typing import Optional

CUBOID_HASH = "cuboidFeatureNodeHash"
OBJECT_HASH = "evtObj01"
DATA_HASH = "0d0c3c8e-2f75-4b9e-9a7d-4c1a1b2c3d4e"

CUBOID_A = {"position": (0.2, 0.2, 0.2), "orientation": (0.0, 0.0, 0.0), "size": (0.1, 0.1, 0.1)}
CUBOID_B = {"position": (0.3, 0.3, 0.3), "orientation": (0.1, 0.2, 0.3), "size": (0.2, 0.2, 0.2)}
CUBOID_C = {"position": (0.4, 0.4, 0.4), "orientation": (0.2, 0.3, 0.4), "size": (0.3, 0.3, 0.3)}
ZERO_CUBOID = {"position": (0, 0, 0), "orientation": (0, 0, 0), "size": (0, 0, 0)}

UPSERT_0 = 0
UPSERT_1 = 1_000_000_000
DELETE_2 = 2_000_000_000
UPSERT_3 = 3_000_000_000
DELETE_4 = 4_000_000_000  # the editor closes the trailing stretch on the frame after the timeline ends


def _entry(cuboid: dict, event: Optional[str]) -> dict:
    entry = {
        "name": "Cuboid object",
        "color": "#4904a5",
        "shape": "cuboid",
        "value": "cuboid_object",
        "createdAt": "Mon, 11 Jul 2022 17:10:51 UTC",
        "createdBy": "annotator@encord.com",
        "lastEditedAt": "Mon, 11 Jul 2022 17:10:51 UTC",
        "lastEditedBy": "annotator@encord.com",
        "confidence": 1,
        "objectHash": OBJECT_HASH,
        "featureHash": CUBOID_HASH,
        "manualAnnotation": True,
        "cuboid": cuboid,
    }
    if event is not None:
        entry["event"] = event
    return entry


EVENT_BASED_SCENE_LABELS = {
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
    "object_answers": {OBJECT_HASH: {"objectHash": OBJECT_HASH, "classifications": []}},
    "classification_answers": {},
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
                str(UPSERT_0): {"objects": [_entry(CUBOID_A, None)], "classifications": []},
                str(UPSERT_1): {"objects": [_entry(CUBOID_B, "upsert")], "classifications": []},
                str(DELETE_2): {"objects": [_entry(ZERO_CUBOID, "delete")], "classifications": []},
                str(UPSERT_3): {"objects": [_entry(CUBOID_C, "upsert")], "classifications": []},
                str(DELETE_4): {"objects": [_entry(ZERO_CUBOID, "delete")], "classifications": []},
            },
        }
    },
    "spaces": {},
}


def dense_scene_labels(labels: Optional[dict] = None) -> dict:
    """The same stored entries read as frame labels: no scene metadata, and no `event` tags anywhere."""
    dense = deepcopy(EVENT_BASED_SCENE_LABELS if labels is None else labels)
    dense.pop("scene", None)
    for data_unit in dense["data_units"].values():
        for frame_labels in data_unit["labels"].values():
            for entry in frame_labels["objects"]:
                entry.pop("event", None)
    return dense
