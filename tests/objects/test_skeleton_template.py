import pytest
from deepdiff import DeepDiff

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


def test_skeleton_template_round_trip_internal():
    dict_template = SKELETON_TEMPLATE_LINE.to_dict()
    assert SkeletonTemplate.from_dict(dict_template) == SKELETON_TEMPLATE_LINE

SKELETON_TEMPLATE_TRIANGLE_JSON = {"name": "Triangle",
        "shape": "skeleton",
        "width": 0.235,
        "height": 0.25,
        "skeleton": {
            "0": {
                "x": 0.5148689289969273,
                "y": 0.5,
                "name": "point_0",
                "color": "#000000",
                "value": "point_0",
                "featureHash": "A9sGmBcx"
            },
            "1": {
                "x": 0.75,
                "y": 0.5,
                "name": "point_1",
                "color": "#000000",
                "value": "point_1",
                "featureHash": "UWKgC/Dy"
            },
            "2": {
                "x": 0.675,
                "y": 0.25,
                "name": "point_2",
                "color": "#000000",
                "value": "point_2",
                "featureHash": "mBt9AAhC"
            }
        },
        "skeletonEdges": {
            "0": {
                "1": {
                    "color": "#000000"
                }
            },
            "1": {
                "2": {
                    "color": "#000000"
                }
            },
            "2": {
                "0": {
                    "color": "#000000"
                }
            }
        },
        "feature_node_hash": "GSc3nz5D"
    }

def test_skeleton_template_round_trip_external():
    st = SkeletonTemplate.from_dict(SKELETON_TEMPLATE_TRIANGLE_JSON)
    assert not DeepDiff(st.to_dict(), SKELETON_TEMPLATE_TRIANGLE_JSON, ignore_order=True)
