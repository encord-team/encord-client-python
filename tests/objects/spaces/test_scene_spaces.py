from unittest.mock import Mock

import pytest
from deepdiff import DeepDiff

from encord.constants.enums import SpaceType
from encord.objects import Classification, LabelRowV2, Object
from encord.objects.attributes import Attribute
from encord.objects.frames import Range
from encord.objects.ontology_object_instance import ObjectInstance
from encord.objects.spaces.range_space.point_cloud_space import PointCloudFileSpace
from encord.objects.spaces.types import PointCloudFileSpaceInfo
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.scene import SCENE_METADATA, SCENE_NO_LABELS

segmentation_ontology_item = all_types_structure.get_child_by_hash("segmentationFeatureNodeHash", Object)
box_ontology_item = all_types_structure.get_child_by_hash("MjI2NzEy", Object)
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


def test_add_segmentation_instance_on_two_spaces(ontology):
    # Arrange
    label_row = LabelRowV2(SCENE_METADATA, Mock(), ontology)
    label_row.from_labels_dict(SCENE_NO_LABELS)

    segmentation_cls = label_row.ontology_structure.get_child_by_hash("segmentationFeatureNodeHash", type_=Object)
    segm_instance = ObjectInstance(segmentation_cls)
    space1 = label_row._space_map["path/to/file1.pcd"]
    space2 = label_row._space_map["path/to/file2.pcd"]

    assert isinstance(space1, PointCloudFileSpace)
    assert isinstance(space2, PointCloudFileSpace)

    space1.put_object_instance(segm_instance, ranges=[Range(0, 5)])
    space2.put_object_instance(segm_instance, ranges=[Range(10, 15)])

    # Check space1 labels (single labels dict with objects and classifications)
    space1_dict = space1._to_space_dict()
    expected_space1_objects = [
        {
            "objectHash": segm_instance.object_hash,
            "featureHash": "segmentationFeatureNodeHash",
            # Range(0, 5) = points {0,1,2,3,4,5} = 6 consecutive points starting at 0 = RLE "06"
            "segmentation": "06",
            "confidence": 1.0,
            "manualAnnotation": True,
        }
    ]
    assert not DeepDiff(
        space1_dict["labels"]["objects"],
        expected_space1_objects,
        exclude_regex_paths=[rf"\[\d+\]\['{field}'\]" for field in IGNORED_METADATA_FIELDS],
    )
    assert space1_dict["labels"]["classifications"] == []

    # Check space2 labels (single labels dict)
    space2_dict = space2._to_space_dict()
    expected_space2_objects = [
        {
            "objectHash": segm_instance.object_hash,
            "featureHash": "segmentationFeatureNodeHash",
            # Range(10, 15) = points {10,11,12,13,14,15} = empty run of 10, then 6 consecutive points
            "segmentation": ":6",
            "confidence": 1.0,
            "manualAnnotation": True,
        }
    ]
    assert not DeepDiff(
        space2_dict["labels"]["objects"],
        expected_space2_objects,
        exclude_regex_paths=[rf"\[\d+\]\['{field}'\]" for field in IGNORED_METADATA_FIELDS],
    )
    assert space2_dict["labels"]["classifications"] == []


def test_point_cloud_segmentation_serde(ontology):
    label_row = LabelRowV2(SCENE_METADATA, Mock(), ontology)
    label_row.from_labels_dict(SCENE_NO_LABELS)

    segmentation_cls = label_row.ontology_structure.get_child_by_hash("segmentationFeatureNodeHash", type_=Object)
    obj = ObjectInstance(segmentation_cls)
    space = label_row._space_map["path/to/file1.pcd"]
    assert isinstance(space, PointCloudFileSpace)

    original_ranges = [Range(0, 5), Range(10, 15), Range(20, 22)]
    space.put_object_instance(obj, ranges=original_ranges)

    space_dict = space._to_space_dict()
    # Single labels dict with objects and classifications
    object_data = space_dict["labels"]["objects"][0]

    # segmentation was encoded
    segmentation = object_data["segmentation"]
    assert isinstance(segmentation, str)
    assert len(segmentation) > 0

    # Create a new space and decode
    label_row2 = LabelRowV2(SCENE_METADATA, Mock(), ontology)
    label_row2.from_labels_dict(SCENE_NO_LABELS)
    space2 = label_row2._space_map["path/to/file1.pcd"]
    assert isinstance(space2, PointCloudFileSpace)

    # Use labels structure for PointCloudFileSpaceInfo
    space_info = PointCloudFileSpaceInfo(
        space_type=SpaceType.POINT_CLOUD,
        scene_info={"stream_id": "", "event_index": 0, "uri": "path/to/file1.pcd"},
        labels=space_dict["labels"],
    )
    # Convert objects list to dict with objectHash as key
    objects_list = space_dict["labels"]["objects"]
    objects_dict = {obj_data["objectHash"]: obj_data for obj_data in objects_list}
    space2._parse_space_dict(space_info, objects_dict, {})

    # Verify the ranges are preserved
    decoded_objects = space2.get_object_instances()
    assert len(decoded_objects) == 1
    decoded_range_manager = space2._object_hash_to_range_manager[decoded_objects[0].object_hash]
    decoded_ranges = decoded_range_manager.get_ranges()

    original_range_tuples = [(r.start, r.end) for r in original_ranges]
    decoded_range_tuples = [(r.start, r.end) for r in decoded_ranges]
    assert decoded_range_tuples == original_range_tuples
