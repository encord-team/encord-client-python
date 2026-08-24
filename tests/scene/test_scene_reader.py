from typing import Any

import pytest
from deepdiff import DeepDiff
from typing_extensions import cast

from encord.beta.scene import (
    CompositeScene,
    ImageStream,
    PointCloudStream,
    Scene3DViewerTile,
    SceneEvent,
    SceneHeightColouring,
    SceneLayout,
    SceneReader,
    SceneTimeSeriesTile,
    SceneViewSettings,
    TimeSeriesStream,
)
from encord.beta.scene.internal.scene import Scene as InternalScene
from encord.beta.scene.internal.scene import SceneResponse
from encord.beta.scene.reader import scene_from_internal
from encord.orm.storage import StorageItemType
from encord.storage import StorageItem


class _FakeApiClient:
    def __init__(self, response: dict) -> None:
        self._response = response
        self.requests = 0

    def get(self, path: str, *, params: None, result_type: type[SceneResponse]) -> SceneResponse:
        assert path == "scene/scene-uuid"
        assert params is None
        assert result_type is SceneResponse
        self.requests += 1
        return SceneResponse.model_validate(self._response)


class _FakeStorageItem:
    uuid = "scene-uuid"
    item_type = StorageItemType.SCENE
    name = "source-scene"
    client_metadata = {"split": "train"}

    def __init__(self, response: dict) -> None:
        self._api_client = _FakeApiClient(response)


def test_scene_reader_converts_internal_streams() -> None:
    response = SceneResponse.model_validate(
        {
            "type": "composite",
            "streams": {
                "lidar": {
                    "type": "event",
                    "id": "lidar",
                    "stream": {
                        "entityType": "point_cloud",
                        "events": [
                            {
                                "timestamp": 0,
                                "url": "gs://bucket/lidar-0.pcd",
                                "signedUrl": "https://signed.example/lidar-0.pcd",
                            }
                        ],
                    },
                },
                "front": {
                    "type": "event",
                    "id": "front",
                    "stream": {
                        "entityType": "image",
                        "events": [
                            {
                                "timestamp": 0,
                                "url": "gs://bucket/front-0.jpg",
                                "signedUrl": "https://signed.example/front-0.jpg",
                            }
                        ],
                    },
                },
                "telemetry": {
                    "type": "self_contained",
                    "id": "telemetry",
                    "entityType": "time_series",
                    "url": "gs://bucket/telemetry.csv",
                    "signedUrl": "https://signed.example/telemetry.csv",
                },
            },
            "viewSettings": {
                "pointCloudColouring": {"colorMode": "solid"},
                "pointRadius": 10,
            },
            "layout": {
                "tiles": {
                    "0": {"type": "3d", "hasSideView": True, "showCameraSwitcher": True},
                    "speed": {
                        "type": "timeseries",
                        "streamName": "telemetry",
                        "timeseriesSettings": {"channels": {}},
                    },
                },
                "layout": "0",
                "timeline": ["speed"],
            },
        }
    )

    scene = scene_from_internal(cast(InternalScene, response.root))

    assert isinstance(scene, CompositeScene)
    point_cloud_stream = scene.get_stream("lidar", kind="point_cloud")
    image_stream = scene.get_stream("front", kind="image")
    time_series_stream = scene.get_stream("telemetry", kind="time_series")
    assert isinstance(point_cloud_stream, PointCloudStream)
    assert isinstance(image_stream, ImageStream)
    assert isinstance(time_series_stream, TimeSeriesStream)
    assert point_cloud_stream.get_event(0).signed_url == "https://signed.example/lidar-0.pcd"
    assert image_stream.get_event(0).signed_url == "https://signed.example/front-0.jpg"
    assert scene.view_settings is not None
    assert scene.view_settings.point_radius == 10
    assert time_series_stream.url == "gs://bucket/telemetry.csv"
    assert time_series_stream.signed_url == "https://signed.example/telemetry.csv"
    assert scene.layout is not None
    assert isinstance(scene.layout.tiles["speed"], SceneTimeSeriesTile)


@pytest.mark.parametrize(
    ("internal", "expected"),
    [
        pytest.param(
            {
                "type": "composite",
                "worldConvention": {"x": "right", "y": "forward", "z": "up"},
                "cameraConvention": {"x": "right", "y": "down", "z": "forward"},
                "streams": {
                    "lidar": {
                        "type": "event",
                        "id": "lidar",
                        "stream": {
                            "entityType": "point_cloud",
                            "frameOfReferenceId": "ego",
                            "events": [
                                {
                                    "timestamp": 0,
                                    "url": "gs://source/lidar-0.pcd",
                                    "signedUrl": "https://signed.example/lidar-0.pcd",
                                }
                            ],
                        },
                    },
                    "front/camera": {
                        "type": "event",
                        "id": "front/camera",
                        "stream": {
                            "entityType": "camera_parameters",
                            "frameOfReferenceId": "ego",
                            "events": [
                                {
                                    "timestamp": 0,
                                    "widthPx": 1920,
                                    "heightPx": 1080,
                                    "intrinsics": {
                                        "type": "simple",
                                        "model": {"type": "pinhole"},
                                        "fx": 1000,
                                        "fy": 1001,
                                        "ox": 960,
                                        "oy": 540,
                                    },
                                }
                            ],
                        },
                    },
                    "front": {
                        "type": "event",
                        "id": "front",
                        "stream": {
                            "entityType": "image",
                            "cameraId": "front/camera",
                            "events": [
                                {
                                    "timestamp": 0,
                                    "url": "gs://source/front-0.jpg",
                                    "signedUrl": "https://signed.example/front-0.jpg",
                                }
                            ],
                        },
                    },
                    "ego": {
                        "type": "event",
                        "id": "ego",
                        "stream": {
                            "entityType": "frame_of_reference",
                            "events": [
                                {
                                    "id": "ego",
                                    "parentFor": "root",
                                    "timestamp": 0,
                                    "rotation": [1, 0, 0, 0, 1, 0, 0, 0, 1],
                                    "position": [1, 2, 3],
                                }
                            ],
                        },
                    },
                    "telemetry": {
                        "type": "self_contained",
                        "id": "telemetry",
                        "entityType": "time_series",
                        "url": "gs://source/telemetry.csv",
                        "signedUrl": "https://signed.example/telemetry.csv",
                    },
                },
            },
            {
                "title": "source-scene",
                "scene": {
                    "content": {
                        "lidar": {
                            "type": "point_cloud",
                            "events": [{"timestamp": 0.0, "uri": "s3://target/lidar-0.pcd"}],
                            "frame_of_reference": "ego",
                            "pose": None,
                        },
                        "front/camera": {
                            "type": "camera_parameters",
                            "events": [
                                {
                                    "timestamp": 0.0,
                                    "width_px": 1920,
                                    "height_px": 1080,
                                    "intrinsics": {
                                        "type": "simple",
                                        "model": {"type": "pinhole"},
                                        "fx": 1000.0,
                                        "fy": 1001.0,
                                        "ox": 960.0,
                                        "oy": 540.0,
                                        "dox": None,
                                        "doy": None,
                                        "dfx": None,
                                        "dfy": None,
                                        "skew": None,
                                    },
                                }
                            ],
                            "frame_of_reference": "ego",
                            "pose": None,
                        },
                        "front": {
                            "type": "image",
                            "camera": "front/camera",
                            "events": [{"timestamp": 0.0, "uri": "s3://target/front-0.jpg"}],
                        },
                        "ego": {
                            "type": "frame_of_reference",
                            "id": "ego",
                            "parent_FoR_id": "root",
                            "events": [
                                {
                                    "timestamp": 0.0,
                                    "pose": {
                                        "rotation": [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
                                        "position": {"x": 1.0, "y": 2.0, "z": 3.0},
                                    },
                                }
                            ],
                        },
                        "telemetry": {
                            "type": "time_series",
                            "uri": "s3://target/telemetry.csv",
                        },
                    },
                    "default_ground_height": None,
                    "world_convention": {"x": "right", "y": "forward", "z": "up"},
                    "camera_convention": {"x": "right", "y": "down", "z": "forward"},
                },
                "client_metadata": {"split": "train"},
                "external_file_type": "SCENE",
            },
            id="composite",
        ),
        pytest.param(
            {
                "type": "self_contained",
                "format": "pcd",
                "url": "gs://source/scene-object",
                "signedUrl": "https://signed.example/scene-object",
                "defaultGroundHeight": 2.5,
            },
            {
                "title": "source-scene",
                "scene": {
                    "content": {"url": "s3://target/scene-object", "format": "pcd"},
                    "default_ground_height": 2.5,
                    "world_convention": {"x": "forward", "y": "left", "z": "up"},
                    "camera_convention": {"x": "forward", "y": "left", "z": "up"},
                },
                "client_metadata": {"split": "train"},
                "external_file_type": "SCENE",
            },
            id="self-contained",
        ),
    ],
)
def test_scene_read_to_upload_payload_converts_scene(
    internal: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    payload = SceneReader(cast(StorageItem, _FakeStorageItem(internal))).to_upload_payload(
        uri_mapper=lambda uri: uri.replace("gs://source", "s3://target")
    )

    assert not DeepDiff(payload.to_dict(by_alias=False), expected)


def test_scene_reader_reuploads_modified_settings() -> None:
    response = {
        "type": "composite",
        "streams": {
            "lidar": {
                "type": "event",
                "id": "lidar",
                "stream": {
                    "entityType": "point_cloud",
                    "events": [
                        {
                            "timestamp": 0,
                            "url": "gs://bucket/lidar.pcd",
                            "signedUrl": "https://signed.example/lidar.pcd",
                        }
                    ],
                },
            }
        },
    }
    reader = SceneReader(cast(StorageItem, _FakeStorageItem(response)))
    reader.view_settings = SceneViewSettings(point_cloud_colouring=SceneHeightColouring())
    reader.layout = SceneLayout(
        tiles={"0": Scene3DViewerTile(has_side_view=True, show_camera_switcher=True)},
        layout="0",
    )

    payload = reader.to_upload_payload()

    assert isinstance(reader.view_settings, SceneViewSettings)
    assert reader.read().view_settings == reader.view_settings
    assert payload.scene["view_settings"] == {"point_cloud_colouring": {"color_mode": "height"}}
    assert payload.scene["layout"] == {
        "tiles": {"0": {"type": "3d", "has_side_view": True, "show_camera_switcher": True}},
        "layout": "0",
        "timeline": [],
    }


def test_scene_read_caches_internal_scene_response() -> None:
    response = {
        "type": "composite",
        "streams": {
            "lidar": {
                "type": "event",
                "id": "lidar",
                "stream": {
                    "entityType": "point_cloud",
                    "events": [
                        {
                            "timestamp": 0,
                            "url": "gs://source/lidar-0.pcd",
                            "signedUrl": "https://signed.example/lidar-0.pcd",
                        }
                    ],
                },
            },
        },
    }
    item = _FakeStorageItem(response)
    scene_read = SceneReader(cast(StorageItem, item))

    scene_read.read()
    scene_read.to_upload_payload(uri_mapper=lambda uri: uri.replace("gs://source", "s3://target"))
    scene_read.read()

    assert item._api_client.requests == 1


def test_get_stream_raises_for_unknown_stream_id() -> None:
    scene = CompositeScene(point_cloud_streams=[], image_streams=[])

    with pytest.raises(KeyError, match="No point cloud stream with id 'lidar'"):
        scene.get_stream("lidar", kind="point_cloud")

    with pytest.raises(KeyError, match="No image stream with id 'front'"):
        scene.get_stream("front", kind="image")

    with pytest.raises(KeyError, match="No time series stream with id 'telemetry'"):
        scene.get_stream("telemetry", kind="time_series")


def test_find_stream_returns_none_for_unknown_stream_id() -> None:
    scene = CompositeScene(point_cloud_streams=[], image_streams=[])

    assert scene.find_stream("lidar", kind="point_cloud") is None
    assert scene.find_stream("front", kind="image") is None
    assert scene.find_stream("telemetry", kind="time_series") is None


def test_get_event_raises_when_event_missing() -> None:
    stream = ImageStream(stream_id="front", events=[])

    with pytest.raises(KeyError, match="No event with timestamp 0 for stream 'front'"):
        stream.get_event(0)


def test_find_event_returns_none_when_event_missing() -> None:
    stream = ImageStream(stream_id="front", events=[])

    assert stream.find_event(0) is None


def test_get_images_at_timestamp_skips_streams_without_matching_event() -> None:
    scene = CompositeScene(
        point_cloud_streams=[],
        image_streams=[
            ImageStream(
                stream_id="front",
                events=[
                    SceneEvent(
                        timestamp=0, url="gs://bucket/front-0.jpg", signed_url="https://signed.example/front-0.jpg"
                    )
                ],
            ),
            ImageStream(
                stream_id="rear",
                events=[
                    SceneEvent(
                        timestamp=1, url="gs://bucket/rear-1.jpg", signed_url="https://signed.example/rear-1.jpg"
                    )
                ],
            ),
        ],
    )

    images = scene.get_images_at_timestamp(0)

    assert [(stream_id, event.url) for stream_id, event in images] == [("front", "gs://bucket/front-0.jpg")]
