import pytest
from pydantic import ValidationError

from encord.beta.scene.builder import (
    Direction,
    SceneBuilder,
    identity_pose,
    intrinsics_advanced,
    intrinsics_pinhole,
    translation_only,
)
from encord.beta.scene.internal.upload import InputPCDStream, InputScene, InputURIEvent, SceneContent, Streams
from encord.exceptions import EncordException


def test_build_minimal_pcd_scene() -> None:
    scene_builder = SceneBuilder()
    scene_builder.add_pcd_stream("lidar").add_pcd(uri="gs://bucket/frame0.pcd")

    scene = scene_builder._build()

    assert scene == {
        "lidar": {
            "type": "point_cloud",
            "events": [{"timestamp": 0, "uri": "gs://bucket/frame0.pcd"}],
            "frame_of_reference": None,
            "pose": None,
        }
    }


def test_build_scene_with_frame_of_reference_inline_camera_and_config() -> None:
    scene_builder = (
        SceneBuilder()
        .set_world_convention(x=Direction.RIGHT, y=Direction.FORWARD, z=Direction.UP)
        .set_camera_convention(x=Direction.RIGHT, y=Direction.DOWN, z=Direction.FORWARD)
    )
    scene_builder.add_for_stream("ego").add_pose(identity_pose())
    scene_builder.add_pcd_stream("lidar", frame_of_reference="ego", pose=translation_only(1, 2, 3)).add_pcd(
        uri="gs://bucket/lidar-0.pcd"
    )
    scene_builder.add_image_stream(
        "front",
        width=1920,
        height=1080,
        intrinsics=intrinsics_pinhole(fx=1000, fy=1001, ox=960, oy=540),
        frame_of_reference="ego",
    ).add_image(uri="gs://bucket/front-0.jpg")

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
        uri="gs://bucket/lidar-0.pcd"
    ).add_pcd(uri="gs://bucket/lidar-1.pcd")
    scene_builder.add_image_stream("front", camera="missing_camera").add_image(uri="gs://bucket/front-0.jpg").add_image(
        uri="gs://bucket/front-1.jpg"
    )

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
    scene_builder.add_for_stream("ego", parent_for_id="lidar").add_pose(identity_pose())
    scene_builder.add_for_stream("lidar", parent_for_id="ego").add_pose(identity_pose())
    scene_builder.add_pcd_stream("pcd", frame_of_reference="ego").add_pcd(uri="gs://bucket/lidar-0.pcd")

    with pytest.raises(EncordException, match="FoR parent chain contains a cycle"):
        scene_builder._build()


def test_build_rejects_invalid_advanced_intrinsics_lengths() -> None:
    scene_builder = SceneBuilder()

    with pytest.raises(EncordException) as exc_info:
        scene_builder.add_camera_stream("front").add_camera_params(
            1920,
            1080,
            intrinsics_advanced(k=[1, 0, 0], r=[1, 0, 0], p=[1, 0, 0]),
        )

    message = str(exc_info.value)
    assert "'k' must have 9 elements, got 3" in message
    assert "'r' must have 9 elements, got 3" in message
    assert "'p' must have 12 elements, got 3" in message


def test_add_image_stream_requires_exactly_one_camera_mode() -> None:
    with pytest.raises(EncordException, match="Must specify either 'camera' or inline camera parameters"):
        SceneBuilder().add_image_stream("front")

    with pytest.raises(EncordException, match="Cannot specify both 'camera' and inline camera parameters"):
        SceneBuilder().add_image_stream(
            "front",
            camera="front_camera",
            width=1920,
            height=1080,
            intrinsics=intrinsics_pinhole(fx=1000, fy=1000, ox=960, oy=540),
        )


def test_stream_builders_reject_empty_uris_immediately() -> None:
    scene_builder = SceneBuilder()

    with pytest.raises(EncordException, match="PCD stream 'lidar' event has an empty URI"):
        scene_builder.add_pcd_stream("lidar").add_pcd(uri="")

    scene_builder.add_camera_stream("front/camera").add_camera_params(
        1920,
        1080,
        intrinsics_pinhole(fx=1000, fy=1000, ox=960, oy=540),
    )
    with pytest.raises(EncordException, match="Image stream 'front' event has an empty URI"):
        scene_builder.add_image_stream("front", camera="front/camera").add_image(uri="")
