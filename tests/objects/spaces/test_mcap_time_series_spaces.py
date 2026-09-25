"""MCAP time-series channels have no top-level space metadata, so the SDK takes their ids on trust.

Saved annotations identify channels in their answer-level ``spaces`` mappings. Bots identify them by explicitly
asking for a time-series space on a continuous scene.
"""

from copy import deepcopy
from dataclasses import asdict
from unittest.mock import Mock

import pytest

from encord.exceptions import LabelRowError
from encord.objects import LabelRowV2, Object, OntologyStructure, Shape
from encord.objects.constants import ROOT_SPACE_ID
from encord.objects.frames import Range
from encord.objects.spaces.range_space.time_series_space import TimeSeriesSpace
from encord.orm.label_row import LabelRowMetadata
from tests.objects.common import BASE_LABEL_ROW_METADATA
from tests.objects.data import mcap_scene
from tests.objects.data.all_types_ontology_structure import RADIO_CLASSIFICATION, all_types_structure
from tests.objects.data.mcap_scene import MCAP_SCENE_LABELS

CHANNEL = "/spot/cmd_vel.angular.x"
SECOND_CHANNEL = "/spot/cmd_vel.linear.x"
AT_CHANNEL = "/spot/channel@123"
TIME_RANGE_FEATURE = "timeRangeFeatureHash"
TIME_RANGE_HASH = "mcapTimeRange01"
CLASSIFICATION_HASH = "mcapTimeSeriesClassification01"
DECLARED_SPACE = "declared-time-series"


def _declared_space_info() -> dict:
    return {
        "space_type": "time_series",
        "child_info": {"layout_key": DECLARED_SPACE, "file_name": "declared.csv", "data_link": None},
        "labels": {},
    }


def _ontology() -> Mock:
    time_range = Object(
        uid=100,
        name="Time range",
        color="#A4FF00",
        shape=Shape.TIME_RANGE,
        feature_node_hash=TIME_RANGE_FEATURE,
    )
    structure = OntologyStructure(
        objects=[*all_types_structure.objects, time_range],
        classifications=all_types_structure.classifications,
        skeleton_templates=all_types_structure.skeleton_templates,
    )
    return Mock(structure=structure)


def _empty_mcap_labels(*, continuous: bool = True) -> dict:
    labels = deepcopy(MCAP_SCENE_LABELS)
    labels["scene"] = {"isContinuous": continuous}
    labels["object_answers"] = {}
    labels["classification_answers"] = {}
    labels["data_units"][mcap_scene.DATA_HASH]["labels"] = {}
    labels["spaces"] = {}
    return labels


def _time_range_answer(channel: str = CHANNEL) -> dict:
    return {
        "objectHash": TIME_RANGE_HASH,
        "featureHash": TIME_RANGE_FEATURE,
        "classifications": [],
        "range": [],
        "spaces": {channel: {"type": "frame", "range": [[100, 200]]}},
        "createdAt": "Wed, 02 Sep 2026 13:58:07 GMT",
        "createdBy": "annotator@encord.com",
        "lastEditedAt": "Wed, 02 Sep 2026 13:58:07 GMT",
        "lastEditedBy": "annotator@encord.com",
        "confidence": 1.0,
        "manualAnnotation": True,
    }


def _classification_answer(channel: str = CHANNEL) -> dict:
    return {
        "classificationHash": CLASSIFICATION_HASH,
        "featureHash": RADIO_CLASSIFICATION.feature_node_hash,
        "classifications": [
            {
                "name": "Radio classification 1",
                "value": "radio_classification_1",
                "answers": [
                    {
                        "name": "cl 1 option 1",
                        "value": "cl_1_option_1",
                        "featureHash": "MTcwMjM5",
                    }
                ],
                "featureHash": "MjI5MTA5",
                "manualAnnotation": True,
            }
        ],
        "range": [],
        "spaces": {channel: {"type": "frame", "range": []}},
        "createdAt": "Wed, 02 Sep 2026 13:58:07 GMT",
        "createdBy": "annotator@encord.com",
        "lastEditedAt": "Wed, 02 Sep 2026 13:58:07 GMT",
        "lastEditedBy": "annotator@encord.com",
        "confidence": 1.0,
        "manualAnnotation": True,
    }


def _scene_row(labels: dict) -> LabelRowV2:
    metadata = asdict(BASE_LABEL_ROW_METADATA)
    metadata.update(
        data_type="SCENE",
        data_hash=mcap_scene.DATA_HASH,
        number_of_frames=0,
        frames_per_second=None,
        duration=None,
        spaces=deepcopy(labels.get("spaces", {})),
    )
    row = LabelRowV2(LabelRowMetadata(**metadata), Mock(), _ontology())
    row.from_labels_dict(labels)
    return row


def test_frontend_time_range_is_loaded_from_its_channel():
    labels = _empty_mcap_labels()
    labels["object_answers"][TIME_RANGE_HASH] = _time_range_answer()

    row = _scene_row(labels)
    space = row.get_space(id=CHANNEL, type_="time_series")

    assert isinstance(space, TimeSeriesSpace)
    [obj] = space.get_object_instances()
    assert obj.object_hash == TIME_RANGE_HASH
    assert space.get_object_ranges(obj) == [Range(100, 200)]
    assert row.get_object_instances() == []


def test_frontend_channel_classification_is_loaded_on_its_channel():
    labels = _empty_mcap_labels()
    labels["classification_answers"][CLASSIFICATION_HASH] = _classification_answer()

    row = _scene_row(labels)
    space = row.get_space(id=CHANNEL, type_="time_series")

    [classification] = space.get_classification_instances()
    assert classification.classification_hash == CLASSIFICATION_HASH
    assert classification.get_answer(RADIO_CLASSIFICATION.attributes[0]).value == "cl_1_option_1"
    assert row.get_classification_instances() == []


def test_each_referenced_channel_becomes_a_time_series_space():
    labels = _empty_mcap_labels()
    labels["object_answers"][TIME_RANGE_HASH] = _time_range_answer()
    labels["classification_answers"][CLASSIFICATION_HASH] = _classification_answer(SECOND_CHANNEL)

    row = _scene_row(labels)

    assert {space.space_id for space in row.get_spaces()} == {CHANNEL, SECOND_CHANNEL}


def test_bot_can_create_and_reload_a_time_range_on_a_trusted_channel():
    row = _scene_row(_empty_mcap_labels())
    space = row.get_space(id=CHANNEL, type_="time_series")
    time_range = row._ontology.structure.get_child_by_hash(TIME_RANGE_FEATURE, type_=Object)
    obj = time_range.create_instance()
    space.put_object_instance(obj, ranges=Range(300, 400))

    exported = row.to_encord_dict()
    reloaded = _scene_row(deepcopy(exported))
    reloaded_space = reloaded.get_space(id=CHANNEL, type_="time_series")
    [reloaded_obj] = reloaded_space.get_object_instances()

    assert exported["spaces"] == {}
    assert exported["object_answers"][obj.object_hash]["spaces"] == {CHANNEL: {"type": "frame", "range": [[300, 400]]}}
    assert reloaded_space.get_object_ranges(reloaded_obj) == [Range(300, 400)]


def test_bot_time_series_id_that_looks_like_a_point_cloud_round_trips():
    row = _scene_row(_empty_mcap_labels())
    space = row.get_space(id=AT_CHANNEL, type_="time_series")
    time_range = row._ontology.structure.get_child_by_hash(TIME_RANGE_FEATURE, type_=Object)
    obj = time_range.create_instance()
    space.put_object_instance(obj, ranges=Range(500, 600))

    reloaded = _scene_row(deepcopy(row.to_encord_dict()))
    reloaded_space = reloaded.get_space(id=AT_CHANNEL, type_="time_series")
    [reloaded_obj] = reloaded_space.get_object_instances()

    assert reloaded_space.get_object_ranges(reloaded_obj) == [Range(500, 600)]


def test_repeated_lookup_returns_the_same_space():
    row = _scene_row(_empty_mcap_labels())

    space = row.get_space(id=CHANNEL, type_="time_series")

    assert row.get_space(id=CHANNEL, type_="time_series") is space


def test_unwritten_trusted_channel_leaves_no_trace():
    row = _scene_row(_empty_mcap_labels())
    before = row.to_encord_dict()

    row.get_space(id=CHANNEL, type_="time_series")

    assert row.to_encord_dict() == before


def test_frontend_time_range_round_trip_keeps_answer_space_only():
    labels = _empty_mcap_labels()
    labels["object_answers"][TIME_RANGE_HASH] = _time_range_answer()
    row = _scene_row(labels)

    exported = row.to_encord_dict()

    assert exported["spaces"] == {}
    assert exported["object_answers"][TIME_RANGE_HASH]["spaces"] == {CHANNEL: {"type": "frame", "range": [[100, 200]]}}
    assert _scene_row(deepcopy(exported)).to_encord_dict() == exported


def test_frontend_classification_round_trip_keeps_answer_space_only():
    labels = _empty_mcap_labels()
    labels["classification_answers"][CLASSIFICATION_HASH] = _classification_answer()
    row = _scene_row(labels)

    exported = row.to_encord_dict()

    assert exported["spaces"] == {}
    assert exported["classification_answers"][CLASSIFICATION_HASH]["spaces"] == {
        CHANNEL: {"type": "frame", "range": []}
    }
    assert _scene_row(deepcopy(exported)).to_encord_dict() == exported


def test_non_continuous_scene_does_not_trust_a_time_series_channel():
    row = _scene_row(_empty_mcap_labels(continuous=False))

    with pytest.raises(LabelRowError, match="Could not find space"):
        row.get_space(id=CHANNEL, type_="time_series")


def test_continuous_scene_with_declared_spaces_does_not_trust_time_series_channels():
    labels = _empty_mcap_labels()
    labels["object_answers"][TIME_RANGE_HASH] = _time_range_answer()
    labels["spaces"] = {DECLARED_SPACE: _declared_space_info()}
    row = _scene_row(labels)

    assert {space.space_id for space in row.get_spaces()} == {DECLARED_SPACE}
    with pytest.raises(LabelRowError, match="Could not find space"):
        row.get_space(id=CHANNEL, type_="time_series")
    with pytest.raises(LabelRowError, match="Could not find space"):
        row.get_space(id=SECOND_CHANNEL, type_="time_series")


def test_empty_channel_id_is_not_trusted():
    row = _scene_row(_empty_mcap_labels())

    with pytest.raises(LabelRowError, match="Could not find space"):
        row.get_space(id="", type_="time_series")


def test_root_space_id_is_not_trusted_as_a_channel():
    row = _scene_row(_empty_mcap_labels())

    with pytest.raises(LabelRowError, match="Could not find space"):
        row.get_space(id=ROOT_SPACE_ID, type_="time_series")


def test_an_existing_point_cloud_id_is_not_reinterpreted_as_time_series():
    row = _scene_row(_empty_mcap_labels())
    point_cloud_id = "/lidar/points@1750258475125212159"
    row.get_space(id=point_cloud_id, type_="point_cloud")

    with pytest.raises(LabelRowError, match="not of expected type 'time_series'"):
        row.get_space(id=point_cloud_id, type_="time_series")
