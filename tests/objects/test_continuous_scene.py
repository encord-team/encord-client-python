"""A self-contained (MCAP) scene is continuous: it has no frame grid, and positions on it are nanosecond offsets.

The enriched label row response says so with `scene.isContinuous`, which the SDK reads as
`LabelRowV2.is_event_based`. `DataType.SCENE` is otherwise bucketed with the geometric (frame-based) types, so
without that flag the generic parse path treats the row's classifications as frame labels and expands their
nanosecond ranges into an entry per frame. Classifications on such a row are therefore held as ranges.
"""

from copy import deepcopy
from dataclasses import asdict
from unittest.mock import Mock

import pytest

from encord.constants.enums import DataType
from encord.exceptions import LabelRowError
from encord.objects import Classification, ClassificationInstance, LabelRowV2
from encord.objects.coordinates import BoundingBoxCoordinates
from encord.objects.frames import Range
from encord.orm.label_row import LabelRowMetadata
from encord.orm.storage import CustomerProvidedVideoMetadata
from tests.objects.common import BASE_LABEL_ROW_METADATA
from tests.objects.data import mcap_scene
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.scene import SCENE_METADATA, SCENE_NO_LABELS
from tests.objects.data.mcap_scene import MCAP_SCENE_LABELS

KEYPOINT_DYNAMIC = next(o for o in all_types_structure.objects if o.name == "Keypoint Dynamic Answers")

TEXT_CLASSIFICATION = all_types_structure.get_child_by_hash(mcap_scene.TEXT_CLASSIFICATION_HASH, type_=Classification)
CHECKLIST_CLASSIFICATION = all_types_structure.get_child_by_hash("3DuQbFxo", type_=Classification)


def _labels_without_classifications() -> dict:
    """The same scene with no stored classifications, and no event-tagged objects.

    A row that is not event-based parses a classification answer as frame labels, expanding its range into an
    entry per frame, and these ranges are nanosecond offsets. The `delete` marker goes too: an `event` tag and
    an event-based row imply each other, so a row used to exercise the not-event-based case cannot carry one.
    """
    labels = deepcopy(MCAP_SCENE_LABELS)
    del labels["data_units"][mcap_scene.DATA_HASH]["labels"][str(mcap_scene.DELETE_NS)]
    return dict(labels, classification_answers={})


def _mcap_row(all_types_ontology, labels=None) -> LabelRowV2:
    metadata_dict = asdict(BASE_LABEL_ROW_METADATA)
    metadata_dict["data_type"] = "SCENE"
    metadata_dict["data_hash"] = mcap_scene.DATA_HASH
    metadata_dict["number_of_frames"] = 0
    metadata_dict["frames_per_second"] = None
    metadata_dict["duration"] = None
    row = LabelRowV2(LabelRowMetadata(**metadata_dict), Mock(), all_types_ontology)
    row.from_labels_dict(deepcopy(MCAP_SCENE_LABELS) if labels is None else labels)
    return row


def test_continuous_scene_metadata_marks_the_row_event_based(all_types_ontology):
    assert _mcap_row(all_types_ontology).is_event_based is True


@pytest.mark.parametrize("scene_metadata", [None, {}, {"isContinuous": False}])
def test_a_scene_without_the_flag_is_not_event_based(all_types_ontology, scene_metadata):
    labels = dict(_labels_without_classifications(), scene=scene_metadata)
    assert _mcap_row(all_types_ontology, labels).is_event_based is False


def test_a_dense_composite_scene_is_not_event_based(all_types_ontology):
    row = LabelRowV2(SCENE_METADATA, Mock(), all_types_ontology)
    row.from_labels_dict(deepcopy(SCENE_NO_LABELS))
    assert row.is_event_based is False


def test_scene_metadata_is_ignored_on_a_non_scene_row(all_types_ontology):
    # The flag only means anything on a scene, and no non-scene response carries it.
    row = LabelRowV2.from_media_metadata(
        all_types_ontology,
        CustomerProvidedVideoMetadata(
            fps=25.0, duration=4.0, width=1920, height=1080, file_size=0, mime_type="video/mp4"
        ),
    )
    expected = row.to_encord_dict()
    row.from_labels_dict(dict(expected, scene={"isContinuous": True}))

    assert row.data_type != DataType.SCENE
    assert row.is_event_based is False
    assert row.to_encord_dict() == expected


def test_reading_the_flag_before_initialising_labels_is_refused(all_types_ontology):
    row = LabelRowV2(SCENE_METADATA, Mock(), all_types_ontology)
    with pytest.raises(LabelRowError, match="initialize labelling first"):
        row.is_event_based


def test_the_flag_survives_a_round_trip(all_types_ontology):
    # Dropping the scene metadata on export would turn a reloaded continuous scene back into a frame-based
    # one, expanding its nanosecond ranges into an entry per frame.
    exported = _mcap_row(all_types_ontology).to_encord_dict()

    assert exported["scene"] == {"isContinuous": True}
    reloaded = _mcap_row(all_types_ontology, deepcopy(exported))
    assert reloaded.is_event_based is True
    assert reloaded.to_encord_dict() == exported


def test_stored_classifications_are_parsed_as_ranges(all_types_ontology):
    row = _mcap_row(all_types_ontology)
    [classification] = row.get_classification_instances()

    assert classification.is_range_only() is True
    assert [(r.start, r.end) for r in classification.range_list] == [tuple(mcap_scene.CLASSIFICATION_RANGE)]
    assert classification.get_answer(TEXT_CLASSIFICATION.attributes[0]) == "Text Answer"


def test_classifications_round_trip(all_types_ontology):
    row = _mcap_row(all_types_ontology)
    exported = row.to_encord_dict()

    assert exported["classification_answers"][mcap_scene.CLASSIFICATION_INSTANCE_HASH]["range"] == [
        mcap_scene.CLASSIFICATION_RANGE
    ]
    reloaded = _mcap_row(all_types_ontology, deepcopy(exported))
    assert reloaded.to_encord_dict()["classification_answers"] == exported["classification_answers"]


def test_a_range_only_classification_can_be_added(all_types_ontology):
    row = _mcap_row(all_types_ontology)
    classification = ClassificationInstance(CHECKLIST_CLASSIFICATION, range_only=True)
    classification.set_for_frames(Range(5_000_000_000, 6_000_000_000))

    row.add_classification_instance(classification)

    assert classification in row.get_classification_instances()
    assert row.to_encord_dict()["classification_answers"][classification.classification_hash]["range"] == [
        [5_000_000_000, 6_000_000_000]
    ]


def test_a_frame_based_classification_is_refused(all_types_ontology):
    row = _mcap_row(all_types_ontology)
    classification = ClassificationInstance(CHECKLIST_CLASSIFICATION)
    classification.set_for_frames(Range(0, 0))

    with pytest.raises(LabelRowError, match="needs to be created with the range_only property set to True"):
        row.add_classification_instance(classification)


def test_a_frame_based_classification_is_accepted_on_a_dense_scene(all_types_ontology):
    # The refusal is about the continuous timeline, not about scenes.
    row = LabelRowV2(SCENE_METADATA, Mock(), all_types_ontology)
    row.from_labels_dict(deepcopy(SCENE_NO_LABELS))
    classification = ClassificationInstance(CHECKLIST_CLASSIFICATION)
    classification.set_for_frames(Range(0, 0))

    row.add_classification_instance(classification)

    assert classification in row.get_classification_instances()


def _frame_objects(exported: dict) -> dict:
    """The exported object entries, keyed by the frame they are stored on."""
    labels = exported["data_units"][mcap_scene.DATA_HASH]["labels"]
    return {frame: entry["objects"] for frame, entry in labels.items()}


# Objects on a continuous scene are sparse events: an entry carries an `event` tag saying what it asserts
# from its offset onward. The tag is not modelled as anything richer here, only carried through faithfully, so
# that loading a row and saving it back does not quietly strip the `delete` that terminates every object.


def test_a_delete_marker_keeps_its_tag(all_types_ontology):
    # Dropping this on export would leave the object present with no end.
    exported = _mcap_row(all_types_ontology).to_encord_dict()

    assert _frame_objects(exported)[str(mcap_scene.DELETE_NS)][0]["event"] == "delete"


def test_an_untagged_entry_is_normalised_to_upsert(all_types_ontology):
    # An `event` tag and an event-based row imply each other, so every entry on this row carries one on the
    # way out. An entry stored untagged reads as an upsert and is written back as an explicit one.
    exported = _mcap_row(all_types_ontology).to_encord_dict()

    assert _frame_objects(exported)[str(mcap_scene.KEYFRAME_NS)][0]["event"] == "upsert"


def test_an_explicit_upsert_tag_is_kept(all_types_ontology):
    labels = deepcopy(MCAP_SCENE_LABELS)
    labels["data_units"][mcap_scene.DATA_HASH]["labels"][str(mcap_scene.KEYFRAME_NS)]["objects"][0]["event"] = "upsert"

    exported = _mcap_row(all_types_ontology, labels).to_encord_dict()

    assert _frame_objects(exported)[str(mcap_scene.KEYFRAME_NS)][0]["event"] == "upsert"


def test_objects_round_trip(all_types_ontology):
    exported = _mcap_row(all_types_ontology).to_encord_dict()

    reloaded = _mcap_row(all_types_ontology, deepcopy(exported))

    assert reloaded.to_encord_dict() == exported


@pytest.mark.parametrize("stored_geometry", [None, "absent"])
def test_a_delete_marker_saved_without_geometry_is_read(all_types_ontology, stored_geometry):
    # The editor writes a delete marker with zeroed geometry, but a saved label may carry the geometry key as
    # `null` or omit it. Nothing reads a marker's geometry, so either form parses to the zeroed placeholder.
    labels = deepcopy(MCAP_SCENE_LABELS)
    entry = labels["data_units"][mcap_scene.DATA_HASH]["labels"][str(mcap_scene.DELETE_NS)]["objects"][0]
    if stored_geometry is None:
        entry["boundingBox"] = None
    else:
        entry.pop("boundingBox")

    exported = _mcap_row(all_types_ontology, labels).to_encord_dict()

    marker = _frame_objects(exported)[str(mcap_scene.DELETE_NS)][0]
    assert marker["event"] == "delete"
    assert marker["boundingBox"] == mcap_scene.ZERO_BOX


def test_writing_geometry_over_a_marker_clears_its_tag(all_types_ontology):
    # Real geometry exported alongside a stale `event: "delete"` would be a contradiction in the saved row,
    # so the marker becomes an upsert. That leaves this object's last event an upsert, which the save then
    # refuses — the refusal is the proof the `delete` went, since a surviving one would have terminated it.
    row = _mcap_row(all_types_ontology)
    [box] = row.get_object_instances()

    box.upsert_event(
        BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.1, top_left_y=0.1),
        mcap_scene.DELETE_NS,
    )

    with pytest.raises(LabelRowError, match="present with no end"):
        row.to_encord_dict()

    box.delete_event(mcap_scene.DELETE_NS + 1)
    assert _frame_objects(row.to_encord_dict())[str(mcap_scene.DELETE_NS)][0]["event"] == "upsert"


def test_a_dense_row_never_gains_an_event_tag(all_types_ontology):
    # The tag is carried, not inferred: a row whose labels never had one must not sprout `event: "upsert"`.
    row = LabelRowV2(SCENE_METADATA, Mock(), all_types_ontology)
    row.from_labels_dict(deepcopy(SCENE_NO_LABELS))

    exported = row.to_encord_dict()

    for data_unit in exported["data_units"].values():
        for frame_labels in data_unit["labels"].values():
            assert all("event" not in entry for entry in frame_labels["objects"])


# Three read APIs assume a frame grid. On a continuous row they are refused rather than answered: each
# would otherwise report something that means a different thing here than it does on a dense row.


def test_enumerating_frame_views_is_refused(all_types_ontology):
    # `number_of_frames` is 0 on a continuous row, so this would report an empty timeline for a row that
    # does hold labels.
    row = _mcap_row(all_types_ontology)

    with pytest.raises(LabelRowError, match="no frame grid to enumerate"):
        row.get_frame_views()


def test_listing_annotations_is_refused(all_types_ontology):
    # A `delete` marker is a terminator, not a label; listing it as an annotation would report a phantom
    # object with zeroed geometry.
    [box] = _mcap_row(all_types_ontology).get_object_instances()

    with pytest.raises(LabelRowError, match="rather than annotations"):
        box.get_annotations()


def test_listing_annotation_frames_is_refused(all_types_ontology):
    [box] = _mcap_row(all_types_ontology).get_object_instances()

    with pytest.raises(LabelRowError, match="stops existing"):
        box.get_annotation_frames()


def test_a_dense_scene_still_answers_all_three(all_types_ontology):
    # The refusal is about the continuous timeline, not about scenes.
    row = LabelRowV2(SCENE_METADATA, Mock(), all_types_ontology)
    row.from_labels_dict(deepcopy(SCENE_NO_LABELS))

    assert row.get_frame_views() != []
    for object_instance in row.get_object_instances():
        assert object_instance.get_annotations() is not None
        assert object_instance.get_annotation_frames() is not None


def test_saving_still_keeps_the_delete_marker(all_types_ontology):
    # Serialisation walks the stored entries, not the annotations, so refusing the annotation reads must
    # not cost the row its terminators.
    exported = _mcap_row(all_types_ontology).to_encord_dict()

    stored = sorted(exported["data_units"][mcap_scene.DATA_HASH]["labels"])
    assert stored == [str(mcap_scene.KEYFRAME_NS), str(mcap_scene.DELETE_NS)]


def test_an_object_can_still_be_validated_and_removed(all_types_ontology):
    # `is_valid` and `remove_object` both used to read the annotation list.
    row = _mcap_row(all_types_ontology)
    [box] = row.get_object_instances()

    box.is_valid()
    row.remove_object(box)

    assert row.get_object_instances() == []
    assert row.to_encord_dict()["data_units"][mcap_scene.DATA_HASH]["labels"] == {}


# `interpolate` is a reserved per-keyframe field on continuous scenes. The SDK does not interpolate: it
# reads every keyframe as holding until the next one. A label asking for anything else is refused at parse,
# because answering it would mean reporting coordinates the platform does not show.


def _with_interpolate(value) -> dict:
    labels = deepcopy(MCAP_SCENE_LABELS)
    entry = labels["data_units"][mcap_scene.DATA_HASH]["labels"][str(mcap_scene.KEYFRAME_NS)]["objects"][0]
    entry["interpolate"] = value
    return labels


@pytest.mark.parametrize("mode", ["linear", "bezier", "nearest", "cubic"])
def test_an_unsupported_mode_is_refused_at_parse(all_types_ontology, mode):
    with pytest.raises(LabelRowError, match="does not support"):
        _mcap_row(all_types_ontology, _with_interpolate(mode))


@pytest.mark.parametrize("value", ["hold", None])
def test_a_supported_value_parses(all_types_ontology, value):
    # Unset, `null` and `hold` all mean no interpolation, which is what the SDK already does.
    assert _mcap_row(all_types_ontology, _with_interpolate(value)).is_event_based is True


def test_hold_is_round_tripped(all_types_ontology):
    exported = _mcap_row(all_types_ontology, _with_interpolate("hold")).to_encord_dict()

    assert _frame_objects(exported)[str(mcap_scene.KEYFRAME_NS)][0]["interpolate"] == "hold"


@pytest.mark.parametrize("value", [None, "absent"])
def test_it_is_never_invented(all_types_ontology, value):
    # Emitting `interpolate` on a label that never carried it would be a change the SDK did not make.
    labels = MCAP_SCENE_LABELS if value == "absent" else _with_interpolate(None)

    exported = _mcap_row(all_types_ontology, deepcopy(labels)).to_encord_dict()

    for objects in _frame_objects(exported).values():
        assert all("interpolate" not in entry for entry in objects)


def _row_with_dynamic_object(all_types_ontology) -> LabelRowV2:
    """The same scene carrying a keypoint object, which has dynamic attributes, instead of the box."""

    def entry(event):
        stored = {
            "name": KEYPOINT_DYNAMIC.name,
            "color": "#D33115",
            "shape": "point",
            "value": "kp",
            "createdAt": "Mon, 11 Jul 2022 17:10:51 UTC",
            "createdBy": "annotator@encord.com",
            "lastEditedAt": "Mon, 11 Jul 2022 17:10:51 UTC",
            "lastEditedBy": "annotator@encord.com",
            "confidence": 1,
            "objectHash": "dynObj0001",
            "featureHash": KEYPOINT_DYNAMIC.feature_node_hash,
            "manualAnnotation": True,
            "point": {"0": {"x": 0.5, "y": 0.5}},
        }
        if event is not None:
            stored["event"] = event
        return stored

    labels = deepcopy(MCAP_SCENE_LABELS)
    labels["object_answers"]["dynObj0001"] = {
        "objectHash": "dynObj0001",
        "featureHash": KEYPOINT_DYNAMIC.feature_node_hash,
        "classifications": [],
        "range": None,
    }
    labels["data_units"][mcap_scene.DATA_HASH]["labels"] = {
        str(mcap_scene.KEYFRAME_NS): {"objects": [entry(None)], "classifications": []},
        str(mcap_scene.DELETE_NS): {"objects": [entry("delete")], "classifications": []},
    }
    return _mcap_row(all_types_ontology, labels)


def test_setting_an_answer_for_every_frame_covers_the_held_range(all_types_ontology):
    # `set_answer` with no frames means everywhere the object has coordinates. On an event-based row that is
    # the stretch its upsert holds over, up to the `delete` that ends it: not the keyframe alone, and never
    # the marker itself, where the object does not exist.
    row = _row_with_dynamic_object(all_types_ontology)
    [keypoint] = row.get_object_instances()
    attribute = next(a for a in KEYPOINT_DYNAMIC.attributes if a.dynamic)

    keypoint.set_answer("Alice", attribute)

    [action] = row.to_encord_dict()["object_actions"]["dynObj0001"]["actions"]
    assert action["range"] == [[mcap_scene.KEYFRAME_NS, mcap_scene.DELETE_NS - 1]]
    keypoint.is_valid()


def test_a_dynamic_answer_round_trips(all_types_ontology):
    row = _row_with_dynamic_object(all_types_ontology)
    [keypoint] = row.get_object_instances()
    keypoint.set_answer("Alice", next(a for a in KEYPOINT_DYNAMIC.attributes if a.dynamic))

    exported = row.to_encord_dict()

    assert _mcap_row(all_types_ontology, deepcopy(exported)).to_encord_dict() == exported


# An event-based object is present from an upsert until a delete closes it. An object whose last event is
# an upsert has no end, which the editor never writes, so the row refuses it where it meets stored labels:
# reading them and writing them back out. In between, a half-built object is free to dangle.


def test_a_stored_object_with_no_terminator_is_refused_at_parse(all_types_ontology):
    labels = deepcopy(MCAP_SCENE_LABELS)
    del labels["data_units"][mcap_scene.DATA_HASH]["labels"][str(mcap_scene.DELETE_NS)]

    with pytest.raises(LabelRowError, match="present with no end"):
        _mcap_row(all_types_ontology, labels)


def test_the_error_names_the_object_and_the_offset(all_types_ontology):
    labels = deepcopy(MCAP_SCENE_LABELS)
    del labels["data_units"][mcap_scene.DATA_HASH]["labels"][str(mcap_scene.DELETE_NS)]

    with pytest.raises(LabelRowError, match=rf"`{mcap_scene.OBJECT_HASH}`.*`{mcap_scene.KEYFRAME_NS}`"):
        _mcap_row(all_types_ontology, labels)


def test_removing_the_terminator_is_refused_on_save(all_types_ontology):
    # Silently saving here would leave the object present to the end of the timeline.
    row = _mcap_row(all_types_ontology)
    [box] = row.get_object_instances()

    box.remove_event(mcap_scene.DELETE_NS)

    with pytest.raises(LabelRowError, match="present with no end"):
        row.to_encord_dict()


def test_an_upsert_past_the_terminator_is_refused_on_save(all_types_ontology):
    row = _mcap_row(all_types_ontology)
    [box] = row.get_object_instances()

    box.upsert_event(
        BoundingBoxCoordinates(height=0.1, width=0.1, top_left_x=0.1, top_left_y=0.1),
        mcap_scene.DELETE_NS + 1_000_000_000,
    )

    with pytest.raises(LabelRowError, match="present with no end"):
        row.to_encord_dict()


def test_a_terminated_row_saves(all_types_ontology):
    assert _mcap_row(all_types_ontology).to_encord_dict() is not None


def test_a_dense_row_is_never_checked(all_types_ontology):
    # The rule is about event-based rows; a frame-based object simply ends on its last frame.
    row = LabelRowV2(SCENE_METADATA, Mock(), all_types_ontology)
    row.from_labels_dict(deepcopy(SCENE_NO_LABELS))

    assert row.to_encord_dict() is not None


# `event` and `is_event_based` are a bijection: every entry on a continuous row carries a tag, and no
# entry on a frame-based row does. Neither half can be stored, or saved, without the other.


def test_every_entry_on_a_continuous_row_is_tagged(all_types_ontology):
    exported = _mcap_row(all_types_ontology).to_encord_dict()

    for objects in _frame_objects(exported).values():
        assert all(entry["event"] in ("upsert", "delete") for entry in objects)


def test_a_tag_on_a_frame_based_row_is_refused_at_parse(all_types_ontology):
    # `event` only means anything on a continuous timeline; on a frame grid it is unreadable either way.
    labels = dict(deepcopy(MCAP_SCENE_LABELS), scene={"isContinuous": False}, classification_answers={})

    with pytest.raises(LabelRowError, match="not event-based"):
        _mcap_row(all_types_ontology, labels)


def test_the_refusal_names_the_object_and_the_offsets(all_types_ontology):
    labels = dict(deepcopy(MCAP_SCENE_LABELS), scene=None, classification_answers={})

    with pytest.raises(LabelRowError, match=rf"`{mcap_scene.OBJECT_HASH}`.*{mcap_scene.DELETE_NS}"):
        _mcap_row(all_types_ontology, labels)


def test_a_tag_appearing_on_a_frame_based_row_is_refused_on_save(all_types_ontology):
    # The row is checked on the way out as well as in, so a tag that appears mid-session cannot be saved.
    row = _mcap_row(all_types_ontology, dict(_labels_without_classifications(), scene={"isContinuous": False}))
    [box] = row.get_object_instances()

    box._frames_to_instance_data[mcap_scene.KEYFRAME_NS].annotation_metadata.event_kind = "delete"

    with pytest.raises(LabelRowError, match="not event-based"):
        row.to_encord_dict()


def test_normalising_is_stable(all_types_ontology):
    # The first save of a row stored with untagged entries adds the tags; every save after that matches.
    first = _mcap_row(all_types_ontology).to_encord_dict()

    second = _mcap_row(all_types_ontology, deepcopy(first)).to_encord_dict()

    assert second == first
