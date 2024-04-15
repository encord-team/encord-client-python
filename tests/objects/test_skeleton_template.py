import pytest

import encord.objects
import encord.objects.skeleton_template
from encord.objects.skeleton_template import SkeletonTemplate, SkeletonTemplateCoordinate

SKELETON_TEMPLATE_COORDINATES = [
    SkeletonTemplateCoordinate(x=0, y=0, name="point_0"),
    SkeletonTemplateCoordinate(x=1, y=1, name="point_1"),
]
SKELETON_TEMPLATE_LINE = SkeletonTemplate.from_dict(
    {
        "name": "Line",
        "width": 100,
        "height": 100,
        "skeleton": {str(i): x for (i, x) in enumerate(SKELETON_TEMPLATE_COORDINATES)},
        "skeletonEdges": {"0": {"1": {"color": "#00000"}}},
        "feature_node_hash": "c67522ee",
        "shape": "skeleton",
    }
)


def test_skeleton_template_round_trip():
    print(SKELETON_TEMPLATE_LINE)
    dict_template = SKELETON_TEMPLATE_LINE.to_dict()
    print(type(dict_template))
    print(dict_template)
    assert SkeletonTemplate.from_dict(dict_template) == SKELETON_TEMPLATE_LINE
