from typing import cast
from unittest.mock import Mock

import pytest
from deepdiff import DeepDiff

from encord.constants.enums import DataType, SpaceType
from encord.exceptions import LabelRowError
from encord.objects import Classification, LabelRowV2, Object
from encord.objects.attributes import Attribute
from encord.objects.common import Shape
from encord.objects.coordinates import CuboidCoordinates
from encord.objects.frames import Range
from encord.objects.ontology_object_instance import ObjectInstance
from encord.objects.spaces.range_space.point_cloud_space import PointCloudFileSpace
from encord.objects.spaces.types import PointCloudFileSpaceInfo
from encord.objects.types import SegmentationObject
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.scene import SCENE_METADATA, SCENE_NO_LABELS, SCENE_WITH_LABELS

segmentation_ontology_item = all_types_structure.get_child_by_hash("segmentationFeatureNodeHash", Object)
cuboid_ontology_item = all_types_structure.get_child_by_hash("cuboidFeatureNodeHash", Object)
box_with_attributes_ontology_item = all_types_structure.get_child_by_hash("MTA2MjAx", Object)
box_text_attribute_ontology_item = box_with_attributes_ontology_item.get_child_by_hash("OTkxMjU1", type_=Attribute)
audio_obj_ontology_item = all_types_structure.get_child_by_hash("KVfzNkFy", Object)
text_classification = all_types_structure.get_child_by_hash("jPOcEsbw", Classification)

IGNORED_METADATA_FIELDS = {"createdAt", "createdBy", "lastEditedAt", "lastEditedBy"}


@pytest.fixture
def ontology():
    ontology_structure = Mock()
    ontology_structure.get_child_by_hash = all_types_structure.get_child_by_hash
    ontology = Mock(structure=ontology_structure)
    yield ontology


def test_get_scene_space(ontology):
    label_row = LabelRowV2(SCENE_METADATA, Mock(), ontology)
    label_row.from_labels_dict(SCENE_NO_LABELS)

    # get by id (== URI)
    space = label_row.get_space(id="path/to/file1.pcd", type_="point_cloud")
    assert isinstance(space, PointCloudFileSpace)
    assert space.metadata.uri == "path/to/file1.pcd"

    with pytest.raises(LabelRowError):
        label_row.get_space(id="path/to/file1.pcd", type_="video")  # wrong type

    # Get by stream name + index
    space2 = label_row.get_space(stream_id="lidar1", event_index=0, type_="point_cloud")
    assert space is space2

    with pytest.raises(LabelRowError) as exc_info:
        label_row.get_space(stream_id="lidar1", event_index=1, type_="point_cloud")
    assert "Could not find space with given stream_id 'lidar1' and event_index '1'" in str(exc_info.value)

    # get by file name
    space3 = label_row.get_space(file_name="file1.pcd", type_="point_cloud")
    assert space3 is space


def test_tmp(ontology):
    label_row = LabelRowV2(SCENE_METADATA, Mock(), ontology)
    label_row.from_labels_dict(SCENE_NO_LABELS)

    cuboid_instance = cuboid_ontology_item.create_instance()
    cuboid_instance.set_for_frames(CuboidCoordinates(position=(0, 0, 0), orientation=(0, 0, 0), size=(1, 1, 1)))
    label_row.add_object_instance(cuboid_instance)
    res = label_row.to_encord_dict()
    print(res)


def test_parse_existing_labels(ontology):
    label_row = LabelRowV2(SCENE_METADATA, Mock(), ontology)
    label_row.from_labels_dict(SCENE_WITH_LABELS)  # existing labels with 1 cuboid, 1 segmentation instance

    # 3D labels are still on the "root", so on the old API.
    root_instances = label_row.get_object_instances()
    assert len(root_instances) == 1
    assert root_instances[0].object_hash == "hash0"

    # point cloud labels are on labelling spaces
    space1 = label_row.get_space(id="path/to/file1.pcd", type_="point_cloud")
    space2 = label_row.get_space(id="path/to/file2.pcd", type_="point_cloud")
    obj_instances = space1.get_object_instances()
    obj_instances2 = space2.get_object_instances()
    assert len(obj_instances) == 1
    assert len(obj_instances2) == 1
    # FIXME: this assertion should pass?
    # assert obj_instances[0] is obj_instances2[0]

    annotations1 = list(space1.get_annotations("object"))
    assert len(annotations1) == 1
    assert annotations1[0].ranges == [Range(0, 5)]

    annotations2 = list(space2.get_annotations("object"))
    assert len(annotations2) == 1
    assert annotations2[0].ranges == [Range(10, 15)]


def test_add_segmentation_instance_on_two_spaces(ontology):
    # Arrange
    label_row = LabelRowV2(SCENE_METADATA, Mock(), ontology)
    label_row.from_labels_dict(SCENE_NO_LABELS)

    segmentation_cls = label_row.ontology_structure.get_child_by_hash("segmentationFeatureNodeHash", type_=Object)
    space1 = label_row.get_space(id="path/to/file1.pcd", type_="point_cloud")
    space2 = label_row.get_space(id="path/to/file2.pcd", type_="point_cloud")

    assert isinstance(space1, PointCloudFileSpace)
    assert isinstance(space2, PointCloudFileSpace)

    # Add a point cloud segmentation on 2 files
    segm_instance = ObjectInstance(segmentation_cls)
    space1.put_object_instance(segm_instance, ranges=[Range(0, 5)])
    space2.put_object_instance(segm_instance, ranges=[Range(10, 15)])

    # Assert on full label_row.to_encord_dict()
    result = label_row.to_encord_dict()

    expected = {
        "label_hash": "28f0e9d2-51e0-459d-8ffa-2e214da653a9",
        "branch_name": "main",
        "created_at": "Thu, 09 Feb 2023 14:12:03 UTC",
        "last_edited_at": "Thu, 09 Feb 2023 14:12:03 UTC",
        "data_hash": "28f0e9d2-51e0-459d-8ffa-2e214da653a0",
        "dataset_hash": "b0d93919-a5e8-4418-8dd5-2c51e3977de8",
        "dataset_title": "Dataset with Scene",
        "data_title": "scene",
        "data_type": "scene",
        "annotation_task_status": "QUEUED",
        "is_shadow_data": False,
        "object_answers": {
            segm_instance.object_hash: {
                "classifications": [],
                "objectHash": segm_instance.object_hash,
                "manualAnnotation": True,
                "featureHash": "segmentationFeatureNodeHash",
                "name": "segmentation object",
                "color": "#4904a5",
                "shape": Shape.SEGMENTATION,
                "value": "segmentation_object",
                "range": [],
                "spaces": {
                    "path/to/file1.pcd": {"range": [], "type": "frame"},
                    "path/to/file2.pcd": {"range": [], "type": "frame"},
                },
            }
        },
        "classification_answers": {},
        "object_actions": {},
        "label_status": "LABEL_IN_PROGRESS",
        "data_units": {
            "28f0e9d2-51e0-459d-8ffa-2e214da653a0": {
                "data_hash": "28f0e9d2-51e0-459d-8ffa-2e214da653a0",
                "data_title": "",
                "data_link": "",
                "data_type": DataType.SCENE,
                "data_sequence": 0,
                "width": 0,
                "height": 0,
                "data_fps": 25,
                "labels": {},
                "data_duration": 100,
            }
        },
        "spaces": {
            "path/to/file1.pcd": {
                "space_type": SpaceType.POINT_CLOUD,
                "scene_info": {"event_index": 0, "stream_id": "lidar1", "uri": "path/to/file1.pcd"},
                "labels": {
                    "objects": [
                        {
                            "shape": Shape.SEGMENTATION,
                            "objectHash": segm_instance.object_hash,
                            "featureHash": "segmentationFeatureNodeHash",
                            "name": "segmentation object",
                            "color": "#4904a5",
                            "value": "segmentation_object",
                            # Range(0, 5) = points {0,1,2,3,4,5} = 6 consecutive points starting at 0 = RLE "06"
                            "segmentation": "06",
                            "confidence": 1.0,
                            "manualAnnotation": True,
                        }
                    ],
                    "classifications": [],
                },
            },
            "path/to/file2.pcd": {
                "space_type": SpaceType.POINT_CLOUD,
                "scene_info": {"event_index": 0, "stream_id": "lidar1", "uri": "path/to/file2.pcd"},
                "labels": {
                    "objects": [
                        {
                            "shape": Shape.SEGMENTATION,
                            "objectHash": segm_instance.object_hash,
                            "featureHash": "segmentationFeatureNodeHash",
                            "name": "segmentation object",
                            "color": "#4904a5",
                            "value": "segmentation_object",
                            # Range(10, 15) = points {10,11,12,13,14,15} = empty run of 10, then 6 consecutive = RLE ":6"
                            "segmentation": ":6",
                            "confidence": 1.0,
                            "manualAnnotation": True,
                        }
                    ],
                    "classifications": [],
                },
            },
        },
    }

    assert not DeepDiff(
        result,
        expected,
        exclude_regex_paths=[rf".*\['{field}'\]" for field in IGNORED_METADATA_FIELDS],
    )


def test_point_cloud_segmentation_serde(ontology):
    label_row = LabelRowV2(SCENE_METADATA, Mock(), ontology)
    label_row.from_labels_dict(SCENE_NO_LABELS)

    segmentation_cls = label_row.ontology_structure.get_child_by_hash("segmentationFeatureNodeHash", type_=Object)
    obj = ObjectInstance(segmentation_cls)
    space = label_row.get_space(id="path/to/file1.pcd", type_="point_cloud")

    original_ranges = [Range(0, 5), Range(10, 15), Range(20, 22)]
    space.put_object_instance(obj, ranges=original_ranges)

    space_dict = space._to_space_dict()
    object_data = cast(SegmentationObject, space_dict["labels"]["objects"][0])

    # segmentation was encoded
    segmentation = object_data["segmentation"]
    assert isinstance(segmentation, str)
    assert len(segmentation) > 0

    # Create a new space and decode
    label_row2 = LabelRowV2(SCENE_METADATA, Mock(), ontology)
    label_row2.from_labels_dict(SCENE_NO_LABELS)
    space2 = label_row2.get_space(id="path/to/file1.pcd", type_="point_cloud")

    # Use labels structure for PointCloudFileSpaceInfo
    space_info = PointCloudFileSpaceInfo(
        space_type=SpaceType.POINT_CLOUD,
        scene_info={"stream_id": "", "event_index": 0, "uri": "path/to/file1.pcd"},
        labels=space_dict["labels"],
    )
    # Convert objects list to dict with objectHash as key
    objects_list = space_dict["labels"]["objects"]
    object_answers = {obj_data["objectHash"]: obj_data for obj_data in objects_list}
    space2._parse_space_dict(space_info, object_answers, {})

    # Verify the ranges are preserved
    decoded_objects = space2.get_object_instances()
    assert len(decoded_objects) == 1
    decoded_range_manager = space2._object_hash_to_range_manager[decoded_objects[0].object_hash]
    decoded_ranges = decoded_range_manager.get_ranges()

    original_range_tuples = [(r.start, r.end) for r in original_ranges]
    decoded_range_tuples = [(r.start, r.end) for r in decoded_ranges]
    assert decoded_range_tuples == original_range_tuples
