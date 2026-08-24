from types import SimpleNamespace
from typing import cast
from unittest.mock import ANY, Mock, patch
from uuid import UUID

import encord.orm.storage as orm_storage
from encord.beta.scene.builder import SceneBuilder
from encord.beta.scene.internal.upload import InputEntityType
from encord.beta.scene.layout import Scene3DViewerTile, SceneLayout
from encord.beta.scene.settings import SceneSolidColouring, SceneViewSettings
from encord.orm.dataset import LongPollingStatus
from encord.storage import StorageFolder, StorageItem


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
    with patch.object(storage_folder, "_add_data", side_effect=fake_add_data):
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


def test_upload_scene_file_uploads_to_encord_storage() -> None:
    scene_uuid = UUID("00000000-0000-0000-0000-000000000001")
    placeholder_uuid = UUID("00000000-0000-0000-0000-000000000002")
    captured: dict = {}

    def fake_add_data(integration_id, private_files, ignore_errors=False):
        captured["integration_id"] = integration_id
        captured["private_files"] = private_files
        captured["ignore_errors"] = ignore_errors
        return orm_storage.UploadLongPollingState(
            status=LongPollingStatus.DONE,
            items_with_names=[orm_storage.StorageItemWithName(item_uuid=scene_uuid, name="capture.mcap")],
            errors=[],
            units_pending_count=0,
            units_done_count=1,
            units_error_count=0,
            units_cancelled_count=0,
            unit_errors=[],
        )

    storage_folder = StorageFolder.__new__(StorageFolder)
    with (
        patch.object(
            storage_folder,
            "_get_scene_upload_signed_urls",
            return_value=[
                orm_storage.UploadSignedUrl(
                    item_uuid=placeholder_uuid,
                    object_key="gs://encord-scenes/scene-object",
                    signed_url="https://upload.example/scene-object",
                    upload_headers={"x-ms-blob-type": "BlockBlob"},
                )
            ],
        ) as get_signed_urls,
        patch.object(storage_folder, "_upload_local_file") as upload_local_file,
        patch.object(storage_folder, "_add_data", side_effect=fake_add_data),
    ):
        result = storage_folder.upload_scene_file(
            file_path="capture.mcap",
            client_metadata={"split": "train"},
        )

    assert result == scene_uuid
    get_signed_urls.assert_called_once_with(count=1)
    upload_local_file.assert_called_once_with(
        "capture.mcap",
        "capture.mcap",
        orm_storage.StorageItemType.SCENE,
        "https://upload.example/scene-object",
        ANY,
        upload_headers={"x-ms-blob-type": "BlockBlob"},
    )
    assert captured["integration_id"] is None
    assert captured["ignore_errors"] is False
    scene_upload = captured["private_files"].scenes[0]
    assert scene_upload.title == "capture.mcap"
    assert scene_upload.scene == {"url": "gs://encord-scenes/scene-object", "format": "mcap"}
    assert scene_upload.client_metadata == {"split": "train"}
    assert scene_upload.placeholder_item_uuid is None


def test_scene_upload_urls_use_public_octet_stream_compatible_presign() -> None:
    upload_url = orm_storage.UploadSignedUrl(
        item_uuid=UUID("00000000-0000-0000-0000-000000000002"),
        object_key="gs://encord-scenes/scene-object",
        signed_url="https://upload.example/scene-object",
    )
    api_client = Mock()
    api_client.get.return_value = SimpleNamespace(results=[upload_url])
    storage_folder = StorageFolder.__new__(StorageFolder)
    storage_folder._api_client = api_client

    assert storage_folder._get_scene_upload_signed_urls(count=1) == [upload_url]

    call = api_client.get.call_args
    assert call.args == ("presigned-urls",)
    assert call.kwargs["params"].to_dict() == {"count": 1, "uploadItemType": "scene"}


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
        "timeSeries": [],
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


def test_time_series_upload_serializes_with_dev_wire_type() -> None:
    settings = orm_storage.TimeSeriesViewSettings(
        channels={
            "temperature": orm_storage.TimeSeriesLineChannelViewSettings(
                label="Temperature",
                color="#ff6600",
                hidden=False,
                line_width=2,
            ),
            "events": orm_storage.TimeSeriesPointsChannelViewSettings(
                label="Events",
                color="#3366ff",
                hidden=True,
                point_radius=4,
            ),
        }
    )
    time_series = orm_storage.DataUploadItems(
        time_series=[
            orm_storage.DataUploadTimeSeries(
                object_url="gs://bucket/pump.csv",
                title="pump.csv",
                client_metadata={"asset_id": "PUMP-042"},
                settings=settings,
            )
        ]
    )

    assert time_series.to_dict()["timeSeries"] == [
        {
            "objectUrl": "gs://bucket/pump.csv",
            "title": "pump.csv",
            "clientMetadata": {"asset_id": "PUMP-042"},
            "settings": {
                "channels": {
                    "temperature": {
                        "label": "Temperature",
                        "color": "#ff6600",
                        "hidden": False,
                        "style": "line",
                        "lineWidth": 2.0,
                    },
                    "events": {
                        "label": "Events",
                        "color": "#3366ff",
                        "hidden": True,
                        "style": "points",
                        "pointRadius": 4.0,
                    },
                }
            },
            "externalFileType": "TIMESERIES",
        }
    ]
    assert (
        orm_storage.UploadSignedUrlsPayload(
            item_type=orm_storage.StorageItemType.TIMESERIES,
            count=1,
            frames_subfolder_name=None,
        ).to_dict()["itemType"]
        == "timeseries"
    )


def test_upload_time_series_passes_settings_to_cord_upload() -> None:
    item_uuid = UUID("00000000-0000-0000-0000-000000000003")
    captured: dict = {}
    settings = orm_storage.TimeSeriesViewSettings(
        channels={
            "temperature": orm_storage.TimeSeriesLineChannelViewSettings(
                label="Temperature",
                color="#ff6600",
                hidden=False,
                line_width=2,
            )
        }
    )

    storage_folder = StorageFolder.__new__(StorageFolder)

    def fake_add_data(integration_id, private_files, ignore_errors=False):
        captured["private_files"] = private_files
        return orm_storage.UploadLongPollingState(
            status=LongPollingStatus.DONE,
            items_with_names=[orm_storage.StorageItemWithName(item_uuid=item_uuid, name="pump.csv")],
            errors=[],
            units_pending_count=0,
            units_done_count=1,
            units_error_count=0,
            units_cancelled_count=0,
            unit_errors=[],
        )

    with (
        patch.object(
            storage_folder,
            "_get_upload_signed_urls",
            return_value=[
                orm_storage.UploadSignedUrl(
                    item_uuid=item_uuid,
                    object_key="uploads/pump.csv",
                    signed_url="https://upload.example/pump.csv",
                )
            ],
        ),
        patch.object(storage_folder, "_upload_local_file"),
        patch.object(storage_folder, "_add_data", side_effect=fake_add_data),
    ):
        assert (
            storage_folder.upload_time_series(
                file_path="pump.csv",
                settings=settings,
            )
            == item_uuid
        )
    upload = captured["private_files"].time_series[0]
    assert upload.settings == settings


def test_time_series_settings_parse_from_storage_item_and_serialize_for_patch() -> None:
    settings = {
        "channels": {
            "temperature": {
                "label": "Temperature",
                "color": "#ff6600",
                "hidden": False,
                "style": "line",
                "lineWidth": 2,
            }
        }
    }

    payload = orm_storage.PatchItemPayload(
        timeseries_settings=orm_storage.TimeSeriesViewSettings.from_dict(settings),
    )

    assert payload.to_dict() == {"timeseriesSettings": settings}


def test_storage_item_update_patches_timeseries_settings() -> None:
    item_uuid = UUID("00000000-0000-0000-0000-000000000005")
    folder_uuid = UUID("00000000-0000-0000-0000-000000000006")
    api_client = Mock()
    orm_item = cast(orm_storage.StorageItem, SimpleNamespace(uuid=item_uuid, parent=folder_uuid))
    api_client.patch.return_value = orm_item
    item = StorageItem(api_client, orm_item)
    settings = orm_storage.TimeSeriesViewSettings(
        channels={
            "left": orm_storage.TimeSeriesLineChannelViewSettings(
                label="Left",
                color="#ff6600",
                hidden=False,
                line_width=2,
            )
        }
    )

    item.update(timeseries_settings=settings)

    payload = api_client.patch.call_args.kwargs["payload"]
    assert payload.timeseries_settings == settings


def test_storage_item_update_patches_scene_view_settings() -> None:
    item_uuid = UUID("00000000-0000-0000-0000-000000000005")
    folder_uuid = UUID("00000000-0000-0000-0000-000000000006")
    api_client = Mock()
    orm_item = cast(orm_storage.StorageItem, SimpleNamespace(uuid=item_uuid, parent=folder_uuid))
    api_client.patch.return_value = orm_item
    item = StorageItem(api_client, orm_item)
    settings = SceneViewSettings(point_cloud_colouring=SceneSolidColouring(), point_radius=10)

    item.update(scene_view_settings=settings)

    payload = api_client.patch.call_args.kwargs["payload"]
    assert payload.to_dict() == {
        "sceneViewSettings": {"pointCloudColouring": {"colorMode": "solid"}, "pointRadius": 10.0},
    }


def test_storage_item_update_patches_scene_layout() -> None:
    item_uuid = UUID("00000000-0000-0000-0000-000000000005")
    folder_uuid = UUID("00000000-0000-0000-0000-000000000006")
    api_client = Mock()
    orm_item = cast(orm_storage.StorageItem, SimpleNamespace(uuid=item_uuid, parent=folder_uuid))
    api_client.patch.return_value = orm_item
    item = StorageItem(api_client, orm_item)
    scene_layout = SceneLayout(
        tiles={"0": Scene3DViewerTile(has_side_view=True, show_camera_switcher=False)},
        layout="0",
    )

    item.update(scene_layout=scene_layout)

    payload = api_client.patch.call_args.kwargs["payload"]
    assert payload.to_dict() == {
        "sceneLayout": {
            "tiles": {"0": {"type": "3d", "hasSideView": True, "showCameraSwitcher": False}},
            "layout": "0",
            "timeline": [],
        }
    }
