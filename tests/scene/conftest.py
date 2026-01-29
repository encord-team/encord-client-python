import json
from pathlib import Path

import pytest

from encord.scene import Scene

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Test fixture - minimal scene data
MINIMAL_SCENE_JSON = {
    "type": "composite",
    "worldConvention": {"x": "forward", "y": "left", "z": "up"},
    "cameraConvention": {"x": "forward", "y": "left", "z": "up"},
    "defaultGroundHeight": None,
    "streams": {
        "LIDAR_TOP": {
            "type": "event",
            "id": "LIDAR_TOP",
            "stream": {
                "frameOfReferenceId": "LIDAR_TOP-calibration",
                "entityType": "point_cloud",
                "events": [
                    {"uri": "https://example.com/pc1.pcd", "timestamp": 0.0},
                    {"uri": "https://example.com/pc2.pcd", "timestamp": 1.0},
                ],
            },
        },
        "CAM_FRONT": {
            "type": "event",
            "id": "CAM_FRONT",
            "stream": {
                "entityType": "image",
                "events": [
                    {"uri": "https://example.com/img1.jpg", "timestamp": 0.0},
                    {"uri": "https://example.com/img2.jpg", "timestamp": 1.0},
                ],
                "cameraId": "CAM_FRONT-camera",
            },
        },
        "ego_vehicle": {
            "type": "event",
            "id": "ego_vehicle",
            "stream": {
                "entityType": "frame_of_reference",
                "events": [
                    {
                        "id": "ego_vehicle",
                        "parent_FOR": "root",
                        "rotation": [1, 0, 0, 0, 1, 0, 0, 0, 1],
                        "position": [0, 0, 0],
                        "timestamp": 0.0,
                    }
                ],
            },
        },
        "LIDAR_TOP-calibration": {
            "type": "event",
            "id": "LIDAR_TOP-calibration",
            "stream": {
                "entityType": "frame_of_reference",
                "events": [
                    {
                        "id": "LIDAR_TOP-calibration",
                        "parent_FOR": "ego_vehicle",
                        "rotation": [0, -1, 0, 1, 0, 0, 0, 0, 1],
                        "position": [1.0, 0.0, 1.8],
                        "timestamp": None,
                    }
                ],
            },
        },
    },
}


@pytest.fixture
def nuscenes_scene() -> Scene:
    fixture_path = Path(__file__).parent.parent.parent / "encord" / "nuscenes.json"
    with open(fixture_path) as f:
        return Scene.from_dict(json.load(f))
