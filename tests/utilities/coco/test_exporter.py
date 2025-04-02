from typing import Any, Dict, List

import pytest
from deepdiff import DeepDiff
from shapely.geometry import MultiPolygon

from encord.utilities.coco.exporter import CocoExporter, OntologyStructure
from tests.utilities.coco.data.exporter import (
    COCO_EXPORTER_EXPECTED_RES,
    LABELS_LIST,
    MULTIPOLYGON,
    MULTIPOLYGON_EXPECTED_COCO_SEGMENTATION,
    MULTIPOLYGON_WITH_ENCLOSED_POLYGONS,
    MULTIPOLYGON_WITH_ENCLOSED_POLYGONS_EXPECTED_COCO_SEGMENTATION,
    ONTOLOGY_STRUCTURE_DICT,
)


@pytest.fixture
def coco_exporter() -> CocoExporter:
    return CocoExporter(
        labels_list=LABELS_LIST,
        ontology=OntologyStructure.from_dict(ONTOLOGY_STRUCTURE_DICT),
        include_videos=True,
    )


def test_coco_exporter_extra_complex_nested_ontology_all_data_types(coco_exporter: CocoExporter) -> None:
    coco_dict = coco_exporter.export()
    assert not DeepDiff(COCO_EXPORTER_EXPECTED_RES, coco_dict)


def test_get_polygon_from_dict_or_list(coco_exporter: CocoExporter) -> None:
    w, h = 100, 100

    polygon_list: List = [{"x": 1, "y": 2}, {"x": 2, "y": 3}]
    polygon_dict: Dict = {str(i): point for i, point in enumerate(polygon_list)}

    expected = [(100, 200), (200, 300)]

    points_dict = coco_exporter.get_polygon_from_dict_or_list(polygon_dict, w, h)
    points_list = coco_exporter.get_polygon_from_dict_or_list(polygon_list, w, h)

    assert points_list == expected
    assert points_dict == expected
    assert points_dict == points_list


def test_get_multipolygon_from_list(coco_exporter: CocoExporter) -> None:
    w, h = 100, 100

    polygons = [
        [
            # Polygon 1 - outer ring
            [0.1, 0.1, 0.2, 0.1, 0.2, 0.2, 0.1, 0.2],
            # Polygon 1 - hole
            [0.12, 0.12, 0.18, 0.12, 0.18, 0.18, 0.12, 0.18],
        ],
        [
            # Polygon 2 - outer ring
            [0.1, 0.4, 0.2, 0.4, 0.2, 0.5, 0.1, 0.5]
        ],
    ]

    points = coco_exporter.get_multipolygon_from_polygons(polygons, w, h)

    expected = [
        (
            # Polygon 1 - outer ring
            ((10, 10), (20, 10), (20, 20), (10, 20)),
            # Polygon 1 - holes
            [((12, 12), (18, 12), (18, 18), (12, 18))],
        ),
        (
            # Polygon 2 - outer ring
            ((10, 40), (20, 40), (20, 50), (10, 50)),
        ),
    ]

    assert points == expected


@pytest.mark.parametrize(
    "polygons, expected_segmentation",
    [
        (MULTIPOLYGON, MULTIPOLYGON_EXPECTED_COCO_SEGMENTATION),
        (MULTIPOLYGON_WITH_ENCLOSED_POLYGONS, MULTIPOLYGON_WITH_ENCLOSED_POLYGONS_EXPECTED_COCO_SEGMENTATION),
    ],
)
def test_get_rle_segmentation_from_multipolygon(
    coco_exporter: CocoExporter,
    polygons,
    expected_segmentation: Dict[str, Any],
) -> None:
    w, h = 4032, 3024

    multipolygon = MultiPolygon(coco_exporter.get_multipolygon_from_polygons(polygons, w, h))
    segmentation = coco_exporter.get_rle_segmentation_from_multipolygon(multipolygon, w, h)

    assert not DeepDiff(segmentation, expected_segmentation)
