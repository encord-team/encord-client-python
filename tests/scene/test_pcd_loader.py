import numpy as np

from encord.scene.pcd_loader import PointCloud
from tests.scene.conftest import FIXTURES_DIR


def test_parse_ascii_pcd_file():
    pcd_path = FIXTURES_DIR / "simple_ascii.pcd"
    pc = PointCloud.from_file(str(pcd_path))
    assert pc.num_points == 4
    np.testing.assert_array_almost_equal(
        pc.points,
        [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]],
        decimal=5,
    )
    assert pc.intensities is not None
    np.testing.assert_array_almost_equal(pc.intensities, [1.0, 0.8, 0.6, 0.4], decimal=5)


def test_parse_binary_pcd_file():
    pcd_path = FIXTURES_DIR / "simple_binary.pcd"
    pc = PointCloud.from_file(str(pcd_path))
    assert pc.num_points == 3
    np.testing.assert_array_almost_equal(
        pc.points,
        [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
        decimal=5,
    )
