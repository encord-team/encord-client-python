"""Self-contained (MCAP) scenes carry point cloud labels under `stream@timestamp_ns` keys in the data unit labels,
with no space metadata on the row. The SDK does not know which point clouds the recording holds. It runs on trust:
a key holding labels is a point cloud space, and a caller asking for one by id gets it."""

from copy import deepcopy
from dataclasses import asdict
from unittest.mock import Mock

import pytest

from encord.exceptions import LabelRowError
from encord.objects import LabelRowV2, Object
from encord.objects.frames import Range
from encord.objects.spaces.range_space.point_cloud_space import PointCloudFileSpace
from encord.objects.spaces.types import SceneMetadata
from encord.orm.label_row import LabelRow, LabelRowMetadata
from tests.objects.common import BASE_LABEL_ROW_METADATA
from tests.objects.data import mcap_scene
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.mcap_scene import MCAP_SCENE_LABELS

STREAM = "/lidar/smooth_pointcloud"
TS_1 = 1750258475125212159
TS_2 = 1750258475225212159
TS_3 = 1750258475325212159
KEY_1 = f"{STREAM}@{TS_1}"
KEY_2 = f"{STREAM}@{TS_2}"
KEY_3 = f"{STREAM}@{TS_3}"  # never labelled: the row has no idea it exists
SEG_HASH = "segObj001"
SEG_FEATURE = "segmentationFeatureNodeHash"
DECLARED_SPACE = "declared-time-series"


def _declared_space_info() -> dict:
    return {
        "space_type": "time_series",
        "child_info": {"layout_key": DECLARED_SPACE, "file_name": "declared.csv", "data_link": None},
        "labels": {},
    }


def _segmentation_entry(rle: str) -> dict:
    return {
        "shape": "segmentation",
        "objectHash": SEG_HASH,
        "featureHash": SEG_FEATURE,
        "name": "segmentation object",
        "color": "#4904a5",
        "value": "segmentation_object",
        "segmentation": rle,
        "confidence": 1,
        "createdAt": "Wed, 02 Sep 2026 13:58:07 GMT",
        "createdBy": "annotator@encord.com",
        "lastEditedAt": "Wed, 02 Sep 2026 13:58:07 GMT",
        "lastEditedBy": "annotator@encord.com",
        "manualAnnotation": True,
    }


def mcap_labels() -> dict:
    labels = deepcopy(MCAP_SCENE_LABELS)
    unit_labels = labels["data_units"][mcap_scene.DATA_HASH]["labels"]
    unit_labels[KEY_1] = {"objects": [_segmentation_entry("06")], "classifications": []}  # points 0..5
    unit_labels[KEY_2] = {"objects": [_segmentation_entry(":6")], "classifications": []}  # points 10..15
    labels["object_answers"][SEG_HASH] = {
        "objectHash": SEG_HASH,
        "classifications": [],
        "range": None,
        "featureHash": SEG_FEATURE,
        "createdAt": "Wed, 02 Sep 2026 13:58:07 GMT",
        "createdBy": "annotator@encord.com",
        "lastEditedAt": "Wed, 02 Sep 2026 13:58:07 GMT",
        "lastEditedBy": "annotator@encord.com",
        "spaces": {KEY_1: {"type": "frame", "range": []}, KEY_2: {"type": "frame", "range": []}},
    }
    labels["spaces"] = {}
    return labels


def _scene_row(all_types_ontology, labels) -> LabelRowV2:
    metadata_dict = asdict(BASE_LABEL_ROW_METADATA)
    metadata_dict["data_type"] = "SCENE"
    metadata_dict["data_hash"] = mcap_scene.DATA_HASH
    metadata_dict["number_of_frames"] = 0
    metadata_dict["frames_per_second"] = None
    metadata_dict["duration"] = None
    metadata_dict["spaces"] = deepcopy(labels.get("spaces", {}))
    row = LabelRowV2(LabelRowMetadata(**metadata_dict), Mock(), all_types_ontology)
    row.from_labels_dict(labels)
    return row


@pytest.fixture
def mcap_row(all_types_ontology) -> LabelRowV2:
    return _scene_row(all_types_ontology, mcap_labels())


def test_labelled_keys_are_point_cloud_spaces(mcap_row):
    space_1 = mcap_row.get_space(id=KEY_1, type_="point_cloud")
    assert isinstance(space_1, PointCloudFileSpace)
    # Only what the key says: stream and uri. Nothing about ordering or timestamps is claimed.
    assert type(space_1.metadata) is SceneMetadata
    assert space_1.metadata.stream_id == STREAM
    assert space_1.metadata.uri == KEY_1
    assert space_1.metadata.event_index == 0
    assert mcap_row.get_space(id=KEY_2, type_="point_cloud").metadata.event_index == 0


def test_label_row_formatter_preserves_mcap_trust_metadata():
    labels = LabelRow(mcap_labels())

    assert labels["scene"] == {"isContinuous": True}


def test_segmentation_is_read_as_point_ranges(mcap_row):
    space_1 = mcap_row.get_space(id=KEY_1, type_="point_cloud")
    space_2 = mcap_row.get_space(id=KEY_2, type_="point_cloud")
    [seg_1] = space_1.get_object_instances()
    [seg_2] = space_2.get_object_instances()
    assert seg_1.object_hash == seg_2.object_hash == SEG_HASH
    assert [(r.start, r.end) for r in space_1.get_object_ranges(seg_1)] == [(0, 5)]
    assert [(r.start, r.end) for r in space_2.get_object_ranges(seg_2)] == [(10, 15)]
    # the root box object is untouched by the point clouds
    assert {o.object_hash for o in mcap_row.get_object_instances()} == {mcap_scene.OBJECT_HASH}


def test_get_spaces_lists_only_what_was_trusted(mcap_row, all_types_ontology):
    assert {s.space_id for s in mcap_row.get_spaces()} == {KEY_1, KEY_2}
    # A recording with no point cloud labels yet: the row knows of no spaces at all.
    assert _scene_row(all_types_ontology, deepcopy(MCAP_SCENE_LABELS)).get_spaces() == []


def test_asking_for_an_unlabelled_point_cloud_creates_it(mcap_row):
    assert KEY_3 not in {s.space_id for s in mcap_row.get_spaces()}
    space = mcap_row.get_space(id=KEY_3, type_="point_cloud")
    assert isinstance(space, PointCloudFileSpace)
    assert space.metadata.uri == KEY_3
    assert space.get_object_instances() == []
    assert mcap_row.get_space(id=KEY_3, type_="point_cloud") is space


def test_an_unwritten_space_leaves_no_trace_on_export(mcap_row):
    before = mcap_row.to_encord_dict()
    mcap_row.get_space(id=KEY_3, type_="point_cloud")
    assert mcap_row.to_encord_dict() == before


def test_ids_that_do_not_look_like_a_point_cloud_are_not_trusted(mcap_row):
    with pytest.raises(LabelRowError, match="Could not find space"):
        mcap_row.get_space(id="not-a-point-cloud", type_="point_cloud")
    with pytest.raises(LabelRowError, match="Could not find space"):
        mcap_row.get_space(id=f"{STREAM}@not-a-timestamp", type_="point_cloud")


def test_only_point_cloud_type_is_trusted(mcap_row):
    with pytest.raises(LabelRowError, match="Could not find space"):
        mcap_row.get_space(id=KEY_3, type_="image")


def test_non_continuous_scene_does_not_trust_point_cloud_keys(all_types_ontology):
    labels = mcap_labels()
    labels["scene"] = {"isContinuous": False}
    labels["classification_answers"] = {}
    del labels["data_units"][mcap_scene.DATA_HASH]["labels"][str(mcap_scene.DELETE_NS)]
    row = _scene_row(all_types_ontology, labels)

    assert row.get_spaces() == []
    with pytest.raises(LabelRowError, match="Could not find space"):
        row.get_space(id=KEY_3, type_="point_cloud")


def test_continuous_scene_with_declared_spaces_does_not_trust_point_cloud_keys(all_types_ontology):
    labels = mcap_labels()
    labels["spaces"] = {DECLARED_SPACE: _declared_space_info()}
    row = _scene_row(all_types_ontology, labels)

    assert {space.space_id for space in row.get_spaces()} == {DECLARED_SPACE}
    with pytest.raises(LabelRowError, match="Could not find space"):
        row.get_space(id=KEY_1, type_="point_cloud")
    with pytest.raises(LabelRowError, match="Could not find space"):
        row.get_space(id=KEY_3, type_="point_cloud")


def test_continuous_scene_without_spaces_field_does_not_trust_point_cloud_keys(all_types_ontology):
    labels = mcap_labels()
    del labels["spaces"]
    row = _scene_row(all_types_ontology, labels)

    assert row.get_spaces() == []
    with pytest.raises(LabelRowError, match="Could not find space"):
        row.get_space(id=KEY_3, type_="point_cloud")


def test_writing_a_segmentation_to_a_trusted_space(mcap_row):
    segmentation = all_types_structure.get_child_by_hash(SEG_FEATURE, type_=Object)
    space = mcap_row.get_space(id=KEY_3, type_="point_cloud")
    obj = segmentation.create_instance()
    space.put_object_instance(obj, ranges=[Range(20, 25)])

    exported = mcap_row.to_encord_dict()
    unit_labels = exported["data_units"][mcap_scene.DATA_HASH]["labels"]
    [entry] = unit_labels[KEY_3]["objects"]
    assert entry["objectHash"] == obj.object_hash
    assert entry["shape"] == "segmentation"
    assert KEY_3 not in exported["spaces"]
    assert exported["object_answers"][obj.object_hash]["spaces"] == {KEY_3: {"type": "frame", "range": []}}


def test_export_writes_point_cloud_labels_back_under_the_same_keys(mcap_row):
    exported = mcap_row.to_encord_dict()
    unit_labels = exported["data_units"][mcap_scene.DATA_HASH]["labels"]

    assert unit_labels[KEY_1]["objects"][0]["segmentation"] == "06"
    assert unit_labels[KEY_2]["objects"][0]["segmentation"] == ":6"
    assert unit_labels[KEY_1]["objects"][0]["objectHash"] == SEG_HASH
    # numeric frames are still there, untouched
    assert str(mcap_scene.KEYFRAME_NS) in unit_labels
    # MCAP point cloud spaces never appear as top-level space metadata
    assert KEY_1 not in exported["spaces"] and KEY_2 not in exported["spaces"]
    assert exported["object_answers"][SEG_HASH]["spaces"] == {
        KEY_1: {"type": "frame", "range": []},
        KEY_2: {"type": "frame", "range": []},
    }


def test_round_trip_is_stable(mcap_row, all_types_ontology):
    exported = mcap_row.to_encord_dict()
    reloaded = _scene_row(all_types_ontology, deepcopy(exported))
    assert reloaded.to_encord_dict()["data_units"] == exported["data_units"]
    assert {s.space_id for s in reloaded.get_spaces()} == {KEY_1, KEY_2}


def test_written_segmentation_round_trips(mcap_row, all_types_ontology):
    segmentation = all_types_structure.get_child_by_hash(SEG_FEATURE, type_=Object)
    space = mcap_row.get_space(id=KEY_3, type_="point_cloud")
    obj = segmentation.create_instance()
    space.put_object_instance(obj, ranges=[Range(20, 25)])

    reloaded = _scene_row(all_types_ontology, deepcopy(mcap_row.to_encord_dict()))
    reloaded_space = reloaded.get_space(id=KEY_3, type_="point_cloud")
    [reloaded_obj] = reloaded_space.get_object_instances()
    assert reloaded_obj.object_hash == obj.object_hash
    assert [(r.start, r.end) for r in reloaded_space.get_object_ranges(reloaded_obj)] == [(20, 25)]


# A continuous scene puts its root geometric objects on a timeline, but a point cloud space is timeless:
# a segmentation is a set of points on one capture, not something that starts and stops. The `event` tag and
# the termination rule apply to the row's own objects and must leave space labels alone.


def test_the_row_is_event_based(mcap_row):
    # Otherwise the rest of this class proves nothing.
    assert mcap_row.is_event_based is True


def test_a_segmentation_is_never_tagged(mcap_row):
    exported = mcap_row.to_encord_dict()

    unit_labels = exported["data_units"][mcap_scene.DATA_HASH]["labels"]
    for key in (KEY_1, KEY_2):
        [entry] = unit_labels[key]["objects"]
        assert "event" not in entry
        assert entry["segmentation"] in ("06", ":6")


def test_the_row_own_objects_are_still_tagged(mcap_row):
    # The same export carries both: the box on the timeline is an event, the segmentation is not.
    exported = mcap_row.to_encord_dict()

    unit_labels = exported["data_units"][mcap_scene.DATA_HASH]["labels"]
    assert unit_labels[str(mcap_scene.KEYFRAME_NS)]["objects"][0]["event"] == "upsert"
    assert unit_labels[str(mcap_scene.DELETE_NS)]["objects"][0]["event"] == "delete"


def test_a_segmentation_is_not_required_to_terminate(mcap_row):
    # It has no delete marker and never will; the termination rule must not reach it.
    assert mcap_row.to_encord_dict() is not None


def test_a_scene_that_is_not_continuous_still_parses_and_saves(all_types_ontology):
    labels = mcap_labels()
    labels["scene"] = {"isContinuous": False}
    labels["classification_answers"] = {}
    del labels["data_units"][mcap_scene.DATA_HASH]["labels"][str(mcap_scene.DELETE_NS)]

    row = _scene_row(all_types_ontology, labels)

    assert row.is_event_based is False
    exported_labels = row.to_encord_dict()["data_units"][mcap_scene.DATA_HASH]["labels"]
    assert KEY_1 not in exported_labels
    assert str(mcap_scene.KEYFRAME_NS) in exported_labels
