from copy import deepcopy
from typing import Any, Dict, List

import pytest
from deepdiff import DeepDiff
from shapely.geometry import MultiPolygon

from encord.utilities.coco.exporter import CocoExporter, OntologyStructure
from tests.objects.data import video_with_classifications
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


@pytest.mark.parametrize(
    "data_type, mime_type, prefix",
    [
        ("video", "video/mp4", "videos"),
        ("dicom", "application/dicom", "dicom"),
        ("nifti", "application/nifti1", "nifti"),
        ("nifti", "application/nifti2", "nifti"),
    ],
)
def test_compact_classification_ranges_preserve_coco_images(
    coco_exporter: CocoExporter, data_type: str, mime_type: str, prefix: str
) -> None:
    label = deepcopy(video_with_classifications.labels)
    label["data_type"] = data_type
    data_unit = next(iter(label["data_units"].values()))
    data_unit["data_type"] = mime_type
    data_unit["labels"] = {"0": {"objects": [], "classifications": []}}
    if data_type == "dicom":
        data_unit["labels"]["0"]["metadata"] = {
            "dicom_instance_uid": "slice-uid",
            "multiframe_frame_number": None,
            "file_uri": "slice-uri",
            "width": 100,
            "height": 200,
        }
    answer = next(iter(label["classification_answers"].values()))
    answer["classifications"] = []
    answer["range"] = [[0, 1], [3, 3]]
    label["classification_answers"]["overlapping"] = {**answer, "classificationHash": "overlapping"}
    original = deepcopy(label)

    result = CocoExporter([label], coco_exporter._ontology).export()

    suffix = ".jpg" if data_type == "video" else ""
    expected_files = [f"{prefix}/{data_unit['data_hash']}/{frame}{suffix}" for frame in (0, 1, 3)]
    if data_type == "dicom":
        expected_files[0] = f"dicom/{data_unit['data_hash']}/slice-uid"
        assert result["images"][0] == {
            "id": 0,
            "coco_url": "slice-uri",
            "file_name": expected_files[0],
            "width": 100,
            "height": 200,
        }
    assert [image["file_name"] for image in result["images"]] == expected_files
    assert [image["id"] for image in result["images"]] == [0, 1, 2]
    assert result["annotations"] == []
    assert label == original


@pytest.mark.parametrize("placement", ["global", "child-space", "root-space", "video-excluded"])
def test_coco_does_not_add_unplaced_or_excluded_video_frames(coco_exporter: CocoExporter, placement: str) -> None:
    label = deepcopy(video_with_classifications.labels)
    next(iter(label["data_units"].values()))["labels"] = {}
    answer = next(iter(label["classification_answers"].values()))
    if placement in ("global", "child-space"):
        answer["range"] = []
    if placement == "child-space":
        answer["spaces"] = {"child": {"type": "frame", "range": [[0, 1]]}}
    if placement == "root-space":
        label["spaces"] = {"root": {"space_type": "video", "labels": {}}}

    result = CocoExporter([label], coco_exporter._ontology, include_videos=placement != "video-excluded").export()

    assert result["images"] == []
    assert result["annotations"] == []


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
