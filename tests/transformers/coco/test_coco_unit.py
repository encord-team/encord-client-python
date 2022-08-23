from typing import List

import pytest

from encord.transformers.coco.coco_encoder import CocoEncoder


@pytest.mark.parametrize(
    "input, expected",
    [
        ([], []),
        ([10, 10], [10, 10, 10, 10]),
        (
            [10, 13, 15, 18],
            [10, 13, 15, 18, 15, 18, 10, 13],
        ),
    ],
)
def test_polyline_from_polygon(input: List[float], expected: List[float]):
    assert CocoEncoder.join_polyline_from_polygon(input) == expected


@pytest.mark.parametrize("input", [([1]), ([1, 2, 3])])
def test_polyline_from_polygon_throws(input: List[float]):
    with pytest.raises(RuntimeError):
        CocoEncoder.join_polyline_from_polygon(input)
