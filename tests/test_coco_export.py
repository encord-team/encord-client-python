from typing import Any, Dict
from unittest.mock import patch

import pytest

from encord.objects.ontology_structure import OntologyStructure
from tests.objects.data.data_1 import labels as BASE_LABEL_DICT
from tests.objects.data.data_1 import ontology as BASE_ONTOLOGY_DICT

ontology_structure = OntologyStructure.from_dict(BASE_ONTOLOGY_DICT)
EXPECTED_COCO_RESULT: Dict[str, Any] = {
    "info": {
        "description": "failing_video_new.mp4",
        "contributor": None,
        "date_created": None,
        "url": None,
        "version": None,
        "year": None,
    },
    "categories": [
        {"supercategory": "bounding_box", "id": 1, "name": "Epiglottis "},
        {"supercategory": "bounding_box", "id": 2, "name": "Larynx"},
        {"supercategory": "bounding_box", "id": 3, "name": "Oesophagus "},
        {"supercategory": "polyline", "id": 4, "name": "Z-line "},
        {"supercategory": "bounding_box", "id": 5, "name": "Stomach"},
        {"supercategory": "bounding_box", "id": 6, "name": "Antrum "},
        {"supercategory": "polygon", "id": 7, "name": "Incisura "},
        {"supercategory": "bounding_box", "id": 8, "name": "D1"},
        {"supercategory": "bounding_box", "id": 9, "name": "D2"},
        {"supercategory": "bounding_box", "id": 10, "name": "LES"},
        {"supercategory": "bounding_box", "id": 11, "name": "Pyloric opening "},
        {"supercategory": "bounding_box", "id": 12, "name": "Fundus "},
        {"supercategory": "point", "id": 13, "name": "point", "keypoints": "keypoint", "skeleton": []},
    ],
    "images": [
        {
            "coco_url": "cord-videos-dev/lFW59RQ9jcT4vHZeG14m8QWJKug1/cd63592b-a9e4-47d7-8563-aaed75c5afdc",
            "id": 0,
            "video_title": "failing_video_new.mp4",
            "file_name": "videos/cd63592b-a9e4-47d7-8563-aaed75c5afdc/0.jpg",
            "height": 480,
            "width": 640,
        },
        {
            "coco_url": "cord-videos-dev/lFW59RQ9jcT4vHZeG14m8QWJKug1/cd63592b-a9e4-47d7-8563-aaed75c5afdc",
            "id": 1,
            "video_title": "failing_video_new.mp4",
            "file_name": "videos/cd63592b-a9e4-47d7-8563-aaed75c5afdc/1.jpg",
            "height": 480,
            "width": 640,
        },
        {
            "coco_url": "cord-videos-dev/lFW59RQ9jcT4vHZeG14m8QWJKug1/cd63592b-a9e4-47d7-8563-aaed75c5afdc",
            "id": 2,
            "video_title": "failing_video_new.mp4",
            "file_name": "videos/cd63592b-a9e4-47d7-8563-aaed75c5afdc/2.jpg",
            "height": 480,
            "width": 640,
        },
        {
            "coco_url": "cord-videos-dev/lFW59RQ9jcT4vHZeG14m8QWJKug1/cd63592b-a9e4-47d7-8563-aaed75c5afdc",
            "id": 3,
            "video_title": "failing_video_new.mp4",
            "file_name": "videos/cd63592b-a9e4-47d7-8563-aaed75c5afdc/3.jpg",
            "height": 480,
            "width": 640,
        },
    ],
    "annotations": [
        {
            "area": 2601.9041279999997,
            "bbox": [189.696, 120.768, 54.976, 47.327999999999996],
            "category_id": 1,
            "image_id": 0,
            "iscrowd": 0,
            "segmentation": [[189.696, 120.768, 244.672, 120.768, 244.672, 168.096, 189.696, 168.096]],
            "keypoints": None,
            "num_keypoints": None,
            "id": 0,
            "attributes": {
                "track_id": 0,
                "encord_track_uuid": "428fba2b",
                "classifications": {},
                "manual_annotation": True,
            },
        },
        {
            "area": 0.0,
            "bbox": [271.552, 165.984, 0.0, 0.0],
            "category_id": 13,
            "image_id": 0,
            "iscrowd": 0,
            "segmentation": [[271.552, 165.984]],
            "keypoints": [271.552, 165.984, 2.0],
            "num_keypoints": 1,
            "id": 1,
            "attributes": {
                "track_id": 1,
                "encord_track_uuid": "82724bb2",
                "classifications": {},
                "manual_annotation": True,
            },
        },
        {
            "area": 999.9974399999999,
            "bbox": [195.32800000000003, 238.512, 40.064, 24.959999999999997],
            "category_id": 1,
            "image_id": 0,
            "iscrowd": 0,
            "segmentation": [
                [
                    195.32800000000003,
                    238.512,
                    235.39200000000002,
                    238.512,
                    235.39200000000002,
                    263.472,
                    195.32800000000003,
                    263.472,
                ]
            ],
            "keypoints": None,
            "num_keypoints": None,
            "id": 2,
            "attributes": {
                "track_id": 2,
                "encord_track_uuid": "u8BIOLmY",
                "classifications": {},
                "manual_annotation": True,
            },
        },
        {
            "area": 2768.498688,
            "bbox": [340.032, 283.872, 63.104, 43.872],
            "category_id": 1,
            "image_id": 0,
            "iscrowd": 0,
            "segmentation": [
                [340.032, 283.872, 403.13599999999997, 283.872, 403.13599999999997, 327.744, 340.032, 327.744]
            ],
            "keypoints": None,
            "num_keypoints": None,
            "id": 3,
            "attributes": {
                "track_id": 3,
                "encord_track_uuid": "/ghwDXVK",
                "classifications": {},
                "manual_annotation": True,
            },
        },
        {
            "area": 2538.319872,
            "bbox": [169.024, 116.016, 54.016000000000005, 46.992],
            "category_id": 1,
            "image_id": 1,
            "iscrowd": 0,
            "segmentation": [
                [169.024, 116.016, 223.04000000000002, 116.016, 223.04000000000002, 163.008, 169.024, 163.008]
            ],
            "keypoints": None,
            "num_keypoints": None,
            "id": 4,
            "attributes": {
                "track_id": 0,
                "encord_track_uuid": "428fba2b",
                "classifications": {},
                "manual_annotation": False,
            },
        },
        {
            "area": 999.9974399999999,
            "bbox": [195.32800000000003, 238.512, 40.064, 24.959999999999997],
            "category_id": 1,
            "image_id": 1,
            "iscrowd": 0,
            "segmentation": [
                [
                    195.32800000000003,
                    238.512,
                    235.39200000000002,
                    238.512,
                    235.39200000000002,
                    263.472,
                    195.32800000000003,
                    263.472,
                ]
            ],
            "keypoints": None,
            "num_keypoints": None,
            "id": 5,
            "attributes": {
                "track_id": 2,
                "encord_track_uuid": "u8BIOLmY",
                "classifications": {},
                "manual_annotation": True,
            },
        },
        {
            "area": 2538.319872,
            "bbox": [169.024, 114.0, 54.016000000000005, 46.992],
            "category_id": 1,
            "image_id": 2,
            "iscrowd": 0,
            "segmentation": [
                [169.024, 114.0, 223.04000000000002, 114.0, 223.04000000000002, 160.992, 169.024, 160.992]
            ],
            "keypoints": None,
            "num_keypoints": None,
            "id": 6,
            "attributes": {
                "track_id": 0,
                "encord_track_uuid": "428fba2b",
                "classifications": {},
                "manual_annotation": False,
            },
        },
        {
            "area": 2538.319872,
            "bbox": [171.968, 114.0, 54.016000000000005, 46.992],
            "category_id": 1,
            "image_id": 3,
            "iscrowd": 0,
            "segmentation": [
                [171.968, 114.0, 225.98399999999998, 114.0, 225.98399999999998, 160.992, 171.968, 160.992]
            ],
            "keypoints": None,
            "num_keypoints": None,
            "id": 7,
            "attributes": {
                "track_id": 0,
                "encord_track_uuid": "428fba2b",
                "classifications": {},
                "manual_annotation": False,
            },
        },
    ],
}

# This test is disabled because it fails when executing tests in parallel
# def test_coco_exporter_without_coco_extra():
#     # Simulate the absence of `pycocotools` and `shapely` packages
#     with patch.dict("sys.modules", {"pycocotools": None, "shapely": None}):
#         with pytest.raises(ImportError, match="The 'pycocotools' and 'shapely' packages are required"):
#             from encord.utilities.coco.exporter import CocoExporter
#
#             output = CocoExporter([BASE_LABEL_DICT], ontology_structure).export()
#             assert output == EXPECTED_COCO_RESULT


def test_coco_exporter_with_coco_extra():
    from encord.utilities.coco.exporter import CocoExporter

    output = CocoExporter([BASE_LABEL_DICT], ontology_structure).export()
    assert output == EXPECTED_COCO_RESULT
