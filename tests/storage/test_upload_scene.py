from uuid import UUID

import encord.orm.storage as orm_storage
from encord.beta.scene.builder import SceneBuilder
from encord.beta.scene.internal.upload import InputEntityType
from encord.orm.dataset import LongPollingStatus
from encord.storage import StorageFolder


def test_upload_scene_registers_scene_data() -> None:
    scene = SceneBuilder()
    scene.add_pcd_stream("lidar").add_pcd(uri="s3://bucket/frame0.pcd", timestamp=0)
    scene_uuid = UUID("00000000-0000-0000-0000-000000000001")
    captured: dict = {}

    def fake_add_data(integration_id, private_files, ignore_errors=False):
        captured["integration_id"] = integration_id
        captured["private_files"] = private_files
        captured["ignore_errors"] = ignore_errors
        return orm_storage.UploadLongPollingState(
            status=LongPollingStatus.DONE,
            items_with_names=[orm_storage.StorageItemWithName(item_uuid=scene_uuid, name="scene-001")],
            errors=[],
            units_pending_count=0,
            units_done_count=1,
            units_error_count=0,
            units_cancelled_count=0,
            unit_errors=[],
        )

    storage_folder = StorageFolder.__new__(StorageFolder)
    storage_folder._add_data = fake_add_data

    result = storage_folder.upload_scene(
        scene=scene,
        title="scene-001",
        integration_id="00000000-0000-0000-0000-000000000002",
        client_metadata={"split": "train"},
    )

    assert result == scene_uuid
    assert captured["integration_id"] == "00000000-0000-0000-0000-000000000002"
    assert captured["ignore_errors"] is False
    scene_upload = captured["private_files"].scenes[0]
    assert scene_upload.title == "scene-001"
    assert scene_upload.client_metadata == {"split": "train"}
    assert scene_upload.scene == {
        "lidar": {
            "type": InputEntityType.POINT_CLOUD,
            "events": [{"timestamp": 0, "uri": "s3://bucket/frame0.pcd"}],
            "frame_of_reference": None,
            "pose": None,
        }
    }


def test_data_upload_scene_serializes_for_api() -> None:
    data_upload_items = orm_storage.DataUploadItems(
        scenes=[
            orm_storage.DataUploadScene(
                title="scene-001",
                scene={"lidar": {"type": "point_cloud", "events": []}},
                client_metadata={"split": "train"},
            )
        ]
    )

    assert data_upload_items.to_dict() == {
        "videos": [],
        "imageGroups": [],
        "dicomSeries": [],
        "images": [],
        "imageGroupsFromItems": [],
        "audio": [],
        "nifti": [],
        "text": [],
        "pdf": [],
        "scenes": [
            {
                "title": "scene-001",
                "scene": {"lidar": {"type": "point_cloud", "events": []}},
                "clientMetadata": {"split": "train"},
                "externalFileType": "SCENE",
            }
        ],
        "skipDuplicateUrls": False,
        "upsertMetadata": False,
    }
