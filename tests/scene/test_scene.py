"""Unit tests for the Scene SDK."""

import numpy as np
import pytest

from encord.orm.scene import AxisDirection, SceneData
from encord.scene.pcd_loader import PointCloud
from encord.scene.scene import Scene
from tests.scene.conftest import MINIMAL_SCENE_JSON


def test_parse_scene_data() -> None:
    scene_data = SceneData.model_validate(MINIMAL_SCENE_JSON)

    # Check top-level fields
    assert scene_data.type == "composite"
    assert scene_data.worldConvention.x == AxisDirection.FORWARD
    assert scene_data.worldConvention.y == AxisDirection.LEFT
    assert scene_data.worldConvention.z == AxisDirection.UP
    assert len(scene_data.streams) == 4

    # Check point cloud streams
    pc_streams = scene_data.get_streams("point_cloud")
    assert "LIDAR_TOP" in pc_streams
    assert len(pc_streams) == 1
    assert pc_streams["LIDAR_TOP"].frameOfReferenceId == "LIDAR_TOP-calibration"
    assert len(pc_streams["LIDAR_TOP"].events) == 2

    # Check image streams
    img_streams = scene_data.get_streams("image")
    assert "CAM_FRONT" in img_streams
    assert len(img_streams) == 1
    assert img_streams["CAM_FRONT"].cameraId == "CAM_FRONT-camera"

    # Check FOR streams
    for_streams = scene_data.get_streams("frame_of_reference")
    assert "ego_vehicle" in for_streams
    assert "LIDAR_TOP-calibration" in for_streams
    assert len(for_streams) == 2
    assert for_streams["LIDAR_TOP-calibration"].events[0].parent_FOR == "ego_vehicle"


def test_scene_stream_methods() -> None:
    scene = Scene.from_dict(MINIMAL_SCENE_JSON)
    pc_streams = scene.get_streams("point_cloud")
    assert len(pc_streams) == 1
    assert pc_streams[0].stream_id == "LIDAR_TOP"
    assert pc_streams[0].num_events == 2
    assert pc_streams[0].get_event_url(0) == "https://example.com/pc1.pcd"

    img_streams = scene.get_streams("image")
    assert len(img_streams) == 1
    assert img_streams[0].stream_id == "CAM_FRONT"
    assert img_streams[0].camera_id == "CAM_FRONT-camera"

    graph = scene.get_for_graph()
    assert len(graph) == 2
    assert graph.has_frame("ego_vehicle")
    assert graph.has_frame("LIDAR_TOP-calibration")

    pc_streams = scene.get_streams("point_cloud")
    with pytest.raises(IndexError):
        pc_streams[0].get_event_url(99)


class TestPointCloud:
    def test_create_point_cloud(self):
        points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        pc = PointCloud(points=points)
        assert pc.num_points == 4
        assert pc.colors is None
        assert pc.intensities is None

    def test_point_cloud_transform(self):
        points = np.array([[1, 0, 0], [0, 1, 0]])
        pc = PointCloud(points=points)

        transform = np.eye(4)
        transform[:3, 3] = [1, 2, 3]

        transformed_pc = pc.transform(transform)
        expected = np.array([[2, 2, 3], [1, 3, 3]])
        np.testing.assert_array_almost_equal(transformed_pc.points, expected)


def test_parse_nuscenes_scene(nuscenes_scene: Scene) -> None:
    scene = nuscenes_scene
    assert scene.scene_type == "composite"

    pc_streams = scene.get_streams("point_cloud")
    stream_ids = [s.stream_id for s in pc_streams]
    assert "LIDAR_TOP" in stream_ids

    graph = scene.get_for_graph()
    assert graph.has_frame("ego_vehicle")
    assert graph.has_frame("LIDAR_TOP-calibration")

    points = np.array([[0, 0, 0]])
    world_points = graph.transform_points_to_world(points, "LIDAR_TOP-calibration")
    assert not np.allclose(world_points, points)
