import numpy as np

from encord.orm.scene import SceneData
from encord.scene.transformations import FORGraph, FrameOfReference, rotation_matrix_to_quaternion
from tests.scene.conftest import MINIMAL_SCENE_JSON


def test_identity_transform():
    frame = FrameOfReference(
        for_id="test",
        parent_id=None,
        position=np.array([0, 0, 0]),
        rotation=np.eye(3),
    )
    matrix = frame.get_transformation_matrix()
    np.testing.assert_array_almost_equal(matrix, np.eye(4))


def test_translation_only():
    frame = FrameOfReference(
        for_id="test",
        parent_id=None,
        position=np.array([1, 2, 3]),
        rotation=np.eye(3),
    )
    matrix = frame.get_transformation_matrix()
    expected = np.eye(4)
    expected[:3, 3] = [1, 2, 3]
    np.testing.assert_array_almost_equal(matrix, expected)


def test_transform_points():
    frame = FrameOfReference(
        for_id="test",
        parent_id=None,
        position=np.array([1, 2, 3]),
        rotation=np.eye(3),
    )
    points = np.array([[0, 0, 0], [1, 1, 1]])
    transformed = frame.transform_points(points)
    expected = np.array([[1, 2, 3], [2, 3, 4]])
    np.testing.assert_array_almost_equal(transformed, expected)


def test_rotation_90_degrees_z():
    rotation = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]], dtype=np.float64)
    frame = FrameOfReference(
        for_id="test",
        parent_id=None,
        position=np.array([0, 0, 0]),
        rotation=rotation,
    )
    points = np.array([[1, 0, 0]])
    transformed = frame.transform_points(points)
    expected = np.array([[0, 1, 0]])
    np.testing.assert_array_almost_equal(transformed, expected)


def test_graph_hierarchical_transform() -> None:
    graph = FORGraph()

    root = FrameOfReference(
        for_id="ego",
        parent_id=None,
        position=np.array([10, 0, 0]),
        rotation=np.eye(3),
    )
    graph.add_frame(root)

    sensor = FrameOfReference(
        for_id="sensor",
        parent_id="ego",
        position=np.array([0, 1, 2]),
        rotation=np.eye(3),
    )
    graph.add_frame(sensor)

    points = np.array([[0, 0, 0]])
    world_points = graph.transform_points_to_world(points, "sensor")
    expected = np.array([[10, 1, 2]])
    np.testing.assert_array_almost_equal(world_points, expected)


def test_graph_transform_between_frames() -> None:
    graph = FORGraph()

    root = FrameOfReference(for_id="root", parent_id=None, position=np.array([0, 0, 0]), rotation=np.eye(3))
    graph.add_frame(root)

    left = FrameOfReference(for_id="left", parent_id="root", position=np.array([-1, 0, 0]), rotation=np.eye(3))
    graph.add_frame(left)

    right = FrameOfReference(for_id="right", parent_id="root", position=np.array([1, 0, 0]), rotation=np.eye(3))
    graph.add_frame(right)

    points = np.array([[0, 0, 0]])
    transformed = graph.transform_points(points, "left", "right")
    expected = np.array([[-2, 0, 0]])
    np.testing.assert_array_almost_equal(transformed, expected)


def test_graph_from_scene_data() -> None:
    scene_data = SceneData.model_validate(MINIMAL_SCENE_JSON)
    graph = FORGraph.from_scene_data(scene_data)

    assert graph.has_frame("ego_vehicle")
    assert graph.has_frame("LIDAR_TOP-calibration")
    assert graph.get_frame("LIDAR_TOP-calibration").parent_id == "ego_vehicle"


def test_identity_rotation() -> None:
    rotation = np.eye(3)
    quat = rotation_matrix_to_quaternion(rotation)
    np.testing.assert_array_almost_equal(quat, [1, 0, 0, 0])
