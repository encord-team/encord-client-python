import pytest
from pydantic import ValidationError
from typing_extensions import cast

from encord.beta.scene import (
    CompositeScene,
    Direction,
    SceneBuilder,
    SceneRead,
    identity_pose,
    intrinsics_advanced,
    intrinsics_pinhole,
    translation_only,
)
from encord.beta.scene.internal.scene import Scene as InternalScene
from encord.beta.scene.internal.scene import SceneResponse
from encord.beta.scene.internal.upload import InputPCDStream, InputScene, InputURIEvent, SceneContent, Streams
from encord.beta.scene.reader import scene_from_internal
from encord.exceptions import EncordException
from encord.orm.storage import StorageItemType
from encord.storage import StorageItem


class _FakeApiClient:
    def get(self, path: str, *, params: None, result_type: type[SceneResponse]) -> SceneResponse:
        assert path == "scene/scene-uuid"
        assert params is None
        assert result_type is SceneResponse
        return SceneResponse.model_validate(
            {
                "type": "composite",
                "streams": {
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
                    }
                },
            }
        )


class _FakeStorageItem:
    uuid = "scene-uuid"
    item_type = StorageItemType.SCENE
    _api_client = _FakeApiClient()


def test_build_minimal_pcd_scene() -> None:
    scene_builder = SceneBuilder()
    scene_builder.add_pcd_stream("lidar").add_pcd(uri="gs://bucket/frame0.pcd", timestamp=0)

    scene = scene_builder._build()

    assert scene == {
        "lidar": {
            "type": "point_cloud",
            "events": [{"timestamp": 0, "uri": "gs://bucket/frame0.pcd"}],
            "frame_of_reference": None,
            "pose": None,
        }
    }


def test_build_scene_preserves_explicit_timestamps() -> None:
    scene_builder = SceneBuilder()
    scene_builder.add_pcd_stream("lidar").add_pcd(uri="gs://bucket/frame100.pcd", timestamp=100).add_pcd(
        uri="gs://bucket/frame250.pcd", timestamp=250
    )

    scene = scene_builder._build()

    assert scene["lidar"]["events"] == [
        {"timestamp": 100, "uri": "gs://bucket/frame100.pcd"},
        {"timestamp": 250, "uri": "gs://bucket/frame250.pcd"},
    ]


def test_build_scene_with_frame_of_reference_inline_camera_and_config() -> None:
    scene_builder = (
        SceneBuilder()
        .set_world_convention(x=Direction.RIGHT, y=Direction.FORWARD, z=Direction.UP)
        .set_camera_convention(x=Direction.RIGHT, y=Direction.DOWN, z=Direction.FORWARD)
    )
    scene_builder.add_for_stream("ego").add_pose(identity_pose(), timestamp=0)
    scene_builder.add_pcd_stream("lidar", frame_of_reference="ego", pose=translation_only(1, 2, 3)).add_pcd(
        uri="gs://bucket/lidar-0.pcd", timestamp=0
    )
    scene_builder.add_image_stream(
        "front",
        width=1920,
        height=1080,
        intrinsics=intrinsics_pinhole(fx=1000, fy=1001, ox=960, oy=540),
        timestamp=0,
        frame_of_reference="ego",
    ).add_image(uri="gs://bucket/front-0.jpg", timestamp=0)

    scene = scene_builder._build()

    result = scene

    assert result["world_convention"] == {"x": "right", "y": "forward", "z": "up"}
    assert result["camera_convention"] == {"x": "right", "y": "down", "z": "forward"}
    assert result["content"]["ego"] == {
        "type": "frame_of_reference",
        "id": "ego",
        "parent_FoR_id": "root",
        "events": [
            {
                "timestamp": 0,
                "pose": {
                    "rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
                    "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                },
            }
        ],
    }
    assert result["content"]["lidar"]["frame_of_reference"] == "ego"
    assert result["content"]["lidar"]["pose"]["position"] == {"x": 1, "y": 2, "z": 3}
    assert result["content"]["front/camera"]["type"] == "camera_parameters"
    assert result["content"]["front/camera"]["events"][0]["intrinsics"] == {
        "type": "simple",
        "model": {"type": "pinhole"},
        "fx": 1000,
        "fy": 1001,
        "ox": 960,
        "oy": 540,
        "dfx": None,
        "dfy": None,
        "dox": None,
        "doy": None,
        "skew": None,
    }
    assert result["content"]["front"] == {
        "type": "image",
        "camera": "front/camera",
        "events": [{"timestamp": 0, "uri": "gs://bucket/front-0.jpg"}],
    }


def test_build_reports_multiple_validation_errors() -> None:
    scene_builder = SceneBuilder()
    scene_builder.add_pcd_stream("lidar", frame_of_reference="missing_for").add_pcd(
        uri="gs://bucket/lidar-0.pcd", timestamp=0
    ).add_pcd(uri="gs://bucket/lidar-1.pcd", timestamp=1)
    scene_builder.add_image_stream("front", camera="missing_camera").add_image(
        uri="gs://bucket/front-0.jpg", timestamp=0
    ).add_image(uri="gs://bucket/front-1.jpg", timestamp=1)

    with pytest.raises(EncordException) as exc_info:
        scene_builder._build()

    message = str(exc_info.value)
    assert "Image stream 'front' references camera 'missing_camera' which does not exist" in message
    assert "Stream 'lidar' references frame of reference 'missing_for' which does not exist" in message


def test_raw_streams_reject_missing_frame_of_reference() -> None:
    streams = Streams(
        root={
            "lidar": InputPCDStream(
                events=[InputURIEvent(uri="gs://bucket/lidar-0.pcd", timestamp=0)],
                frame_of_reference="missing_for",
            )
        }
    )

    with pytest.raises(ValidationError, match="references non-existent frame of reference ID: 'missing_for'"):
        InputScene(root=SceneContent(root=streams))


def test_build_rejects_frame_of_reference_cycles() -> None:
    scene_builder = SceneBuilder()
    scene_builder.add_for_stream("ego", parent_for_id="lidar").add_pose(identity_pose(), timestamp=0)
    scene_builder.add_for_stream("lidar", parent_for_id="ego").add_pose(identity_pose(), timestamp=0)
    scene_builder.add_pcd_stream("pcd", frame_of_reference="ego").add_pcd(uri="gs://bucket/lidar-0.pcd", timestamp=0)

    with pytest.raises(EncordException, match="FoR parent chain contains a cycle"):
        scene_builder._build()


def test_build_rejects_invalid_advanced_intrinsics_lengths() -> None:
    scene_builder = SceneBuilder()

    with pytest.raises(EncordException) as exc_info:
        scene_builder.add_camera_stream("front").add_camera_params(
            1920,
            1080,
            intrinsics_advanced(k=[1, 0, 0], r=[1, 0, 0], p=[1, 0, 0]),
            timestamp=0,
        )

    message = str(exc_info.value)
    assert "'k' must have 9 elements, got 3" in message
    assert "'r' must have 9 elements, got 3" in message
    assert "'p' must have 12 elements, got 3" in message


def test_add_image_stream_requires_exactly_one_camera_mode() -> None:
    with pytest.raises(EncordException, match="Must specify either 'camera' or inline camera parameters"):
        SceneBuilder().add_image_stream("front")  # type: ignore[call-overload]

    with pytest.raises(EncordException, match="Cannot specify both 'camera' and inline camera parameters"):
        SceneBuilder().add_image_stream(  # type: ignore[call-overload]
            "front",
            camera="front_camera",
            width=1920,
            height=1080,
            intrinsics=intrinsics_pinhole(fx=1000, fy=1000, ox=960, oy=540),
            timestamp=0,
        )


def test_stream_builders_reject_empty_uris_immediately() -> None:
    scene_builder = SceneBuilder()

    with pytest.raises(EncordException, match="PCD stream 'lidar' event has an empty URI"):
        scene_builder.add_pcd_stream("lidar").add_pcd(uri="", timestamp=0)

    scene_builder.add_camera_stream("front/camera").add_camera_params(
        1920,
        1080,
        intrinsics_pinhole(fx=1000, fy=1000, ox=960, oy=540),
        timestamp=0,
    )
    with pytest.raises(EncordException, match="Image stream 'front' event has an empty URI"):
        scene_builder.add_image_stream("front", camera="front/camera").add_image(uri="", timestamp=0)


def test_scene_from_internal_ignores_image_camera_id() -> None:
    response = SceneResponse.model_validate(
        {
            "type": "composite",
            "streams": {
                "front": {
                    "type": "event",
                    "id": "front",
                    "stream": {
                        "entityType": "image",
                        "cameraId": "legacy-camera",
                        "events": [
                            {
                                "timestamp": 0,
                                "url": "gs://bucket/front-0.jpg",
                                "signedUrl": "https://signed.example/front-0.jpg",
                            }
                        ],
                    },
                }
            },
        }
    )

    scene = scene_from_internal(cast(InternalScene, response.root))

    assert isinstance(scene, CompositeScene)
    image_stream = scene.get_stream("front", kind="image")
    assert not hasattr(image_stream, "camera_id")
    assert image_stream.get_event(0).url == "gs://bucket/front-0.jpg"


def test_scene_read_fetches_scene_from_storage_item() -> None:
    scene = SceneRead(cast(StorageItem, _FakeStorageItem())).read()

    assert isinstance(scene, CompositeScene)
    assert scene.get_stream("front", kind="image").get_event(0).signed_url == "https://signed.example/front-0.jpg"
    assert scene.get_images_at_timestamp(0)[0][1].timestamp == 0


def test_scene_from_internal_requires_timestamps() -> None:
    response = SceneResponse.model_validate(
        {
            "type": "composite",
            "streams": {
                "front": {
                    "type": "event",
                    "id": "front",
                    "stream": {
                        "entityType": "image",
                        "events": [
                            {
                                "url": "gs://bucket/front-0.jpg",
                                "signedUrl": "https://signed.example/front-0.jpg",
                            }
                        ],
                    },
                }
            },
        }
    )

    with pytest.raises(ValueError, match="Scene stream 'front' contains an event without a timestamp"):
        scene_from_internal(cast(InternalScene, response.root))


def test_scene_from_internal_rejects_self_contained_scenes_with_clear_error() -> None:
    response = SceneResponse.model_validate(
        {
            "type": "self_contained",
            "format": "pcd",
            "url": "gs://bucket/scene.pcd",
            "signedUrl": "https://signed.example/scene.pcd",
        }
    )

    with pytest.raises(ValueError, match="Single-file scenes are not supported in the SDK yet"):
        scene_from_internal(cast(InternalScene, response.root))
