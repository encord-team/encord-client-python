import re
import time
from copy import deepcopy
from dataclasses import asdict
from typing import cast
from unittest.mock import Mock

import pytest

from encord.exceptions import LabelRowError
from encord.objects import LabelRowV2, Object, ObjectInstance
from encord.objects.coordinates import (
    BoundingBoxCoordinates,
    CuboidCoordinates,
    PointCoordinate,
    PolygonCoordinates,
    TextCoordinates,
)
from encord.objects.events import LabelDeleteEvent
from encord.objects.frames import Range
from encord.objects.ontology_object_instance import AnswersForFrames
from encord.objects.spaces.annotation.base_annotation import _AnnotationMetadata
from encord.objects.types import BaseFrameObject
from encord.orm.label_row import LabelRowMetadata
from tests.objects.common import BASE_LABEL_ROW_METADATA
from tests.objects.data import event_based_scene
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.event_based_scene import EVENT_BASED_SCENE_LABELS, dense_scene_labels


def _scene_label_row(all_types_ontology, labels=None) -> LabelRowV2:
    metadata_dict = asdict(BASE_LABEL_ROW_METADATA)
    metadata_dict["data_type"] = "SCENE"
    metadata_dict["data_hash"] = event_based_scene.DATA_HASH
    metadata_dict["number_of_frames"] = 0
    metadata_dict["frames_per_second"] = None
    metadata_dict["duration"] = None
    label_row = LabelRowV2(LabelRowMetadata(**metadata_dict), Mock(), all_types_ontology)
    label_row.from_labels_dict(deepcopy(EVENT_BASED_SCENE_LABELS) if labels is None else labels)
    return label_row


@pytest.fixture
def dense_scene_label_row(all_types_ontology) -> LabelRowV2:
    """The same stored geometry as a frame-based scene: no scene metadata and no `event` tags."""
    return _scene_label_row(all_types_ontology, dense_scene_labels())


@pytest.fixture
def event_based_label_row(all_types_ontology) -> LabelRowV2:
    return _scene_label_row(all_types_ontology)


# ---- _AnnotationMetadata.event_kind


def test_missing_event_key_is_none():
    data = cast(BaseFrameObject, {"createdAt": "Mon, 11 Jul 2022 17:10:51 UTC"})
    assert _AnnotationMetadata.from_dict(data).event_kind is None


@pytest.mark.parametrize("kind", ["upsert", "delete"])
def test_event_key_is_parsed(kind):
    d = cast(BaseFrameObject, {"createdAt": "Mon, 11 Jul 2022 17:10:51 UTC", "event": kind})
    assert _AnnotationMetadata.from_dict(d).event_kind == kind


def test_update_from_optional_fields_sets_event_kind():
    metadata = _AnnotationMetadata()
    metadata.update_from_optional_fields(event_kind="delete")
    assert metadata.event_kind == "delete"
    metadata.update_from_optional_fields()
    assert metadata.event_kind == "delete"


# ---- LabelRowV2 event flag


@pytest.mark.parametrize("row_fixture", ["empty_video_label_row", "dense_scene_label_row"])
def test_null_scene_metadata_keeps_dense_labels_readable(request, row_fixture):
    row = request.getfixturevalue(row_fixture)
    expected = row.to_encord_dict()
    labels = deepcopy(expected)
    labels["scene"] = None

    row.from_labels_dict(labels)

    assert row.is_event_based is False
    assert row.to_encord_dict() == expected


def test_the_fixture_is_event_based_by_its_scene_metadata(event_based_label_row):
    assert event_based_label_row._event_based is None
    assert event_based_label_row.is_event_based is True


@pytest.mark.parametrize("row_fixture", ["empty_video_label_row", "dense_scene_label_row"])
def test_dense_force_replacement_preserves_existing_handles_and_frame_queries(request, row_fixture):
    row = request.getfixturevalue(row_fixture)
    box = all_types_structure.get_child_by_hash("MjI2NzEy", Object)
    original = ObjectInstance(box, object_hash="dense-replacement")
    replacement = ObjectInstance(box, object_hash=original.object_hash)
    coordinates = BoundingBoxCoordinates(top_left_x=0.1, top_left_y=0.2, width=0.3, height=0.4)
    original.set_for_frames(coordinates, frames=0)
    replacement.set_for_frames(coordinates, frames=1)
    row.add_object_instance(original)

    row.add_object_instance(replacement, force=True)

    assert original.is_assigned_to_label_row() is row
    assert replacement.is_assigned_to_label_row() is row
    assert replacement in row.get_object_instances(filter_frames=0)
    assert replacement in row.get_object_instances(filter_frames=1)
    assert replacement.get_annotation_frames() == {1}

    other = ObjectInstance(box)
    other.set_for_frames(coordinates, frames=0)
    row.add_object_instance(other)
    with pytest.raises(LabelRowError, match="not on the frame"):
        row.to_encord_dict()


def test_defaults_are_off(dense_scene_label_row):
    assert dense_scene_label_row.is_event_based is False


def test_parsing_keeps_all_stored_frames(event_based_label_row):
    [obj] = event_based_label_row.get_object_instances()
    assert sorted(obj._frames_to_instance_data.keys()) == [
        event_based_scene.UPSERT_0,
        event_based_scene.UPSERT_1,
        event_based_scene.DELETE_2,
        event_based_scene.UPSERT_3,
        event_based_scene.DELETE_4,
    ]
    assert obj._frames_to_instance_data[event_based_scene.DELETE_2].annotation_metadata.event_kind == "delete"
    assert obj._frames_to_instance_data[event_based_scene.UPSERT_0].annotation_metadata.event_kind is None


CUBOID_A = CuboidCoordinates(position=(0.2, 0.2, 0.2), orientation=(0.0, 0.0, 0.0), size=(0.1, 0.1, 0.1))
CUBOID_B = CuboidCoordinates(position=(0.3, 0.3, 0.3), orientation=(0.1, 0.2, 0.3), size=(0.2, 0.2, 0.2))
CUBOID_C = CuboidCoordinates(position=(0.4, 0.4, 0.4), orientation=(0.2, 0.3, 0.4), size=(0.3, 0.3, 0.3))


def _object(label_row) -> ObjectInstance:
    [obj] = label_row.get_object_instances()
    return obj


# ---- Resolved reads


def test_exact_keyframe_is_not_virtual(event_based_label_row):
    annotation = _object(event_based_label_row).get_annotation(event_based_scene.UPSERT_1)
    assert isinstance(annotation, ObjectInstance.ResolvedAnnotation)
    assert annotation.is_virtual is False
    assert annotation.keyframe == event_based_scene.UPSERT_1
    assert annotation.frame == event_based_scene.UPSERT_1
    assert annotation.coordinates == CUBOID_B


def test_frame_between_keyframes_is_virtual(event_based_label_row):
    frame = event_based_scene.UPSERT_1 + 5
    annotation = _object(event_based_label_row).get_annotation(frame)
    assert isinstance(annotation, ObjectInstance.ResolvedAnnotation)
    assert annotation.is_virtual is True
    assert annotation.keyframe == event_based_scene.UPSERT_1
    assert annotation.frame == frame
    assert annotation.coordinates == CUBOID_B
    assert annotation.created_by == "annotator@encord.com"
    assert annotation.confidence == 1


def test_untagged_entry_reads_as_upsert(event_based_label_row):
    annotation = _object(event_based_label_row).get_annotation(event_based_scene.UPSERT_0 + 1)
    assert isinstance(annotation, ObjectInstance.ResolvedAnnotation)
    assert annotation.is_virtual is True
    assert annotation.coordinates == CUBOID_A


def test_deleted_stretch_is_absent(event_based_label_row):
    obj = _object(event_based_label_row)
    with pytest.raises(LabelRowError, match="does not exist"):
        obj.get_annotation(event_based_scene.DELETE_2)
    with pytest.raises(LabelRowError, match="does not exist"):
        obj.get_annotation(event_based_scene.DELETE_2 + 1)


def test_last_upsert_holds_up_to_its_closing_delete(event_based_label_row):
    obj = _object(event_based_label_row)
    annotation = obj.get_annotation(event_based_scene.DELETE_4 - 1)
    assert isinstance(annotation, ObjectInstance.ResolvedAnnotation)
    assert annotation.is_virtual is True
    assert annotation.coordinates == CUBOID_C
    with pytest.raises(LabelRowError, match="does not exist"):
        obj.get_annotation(event_based_scene.DELETE_4 + 10**12)


def test_resolved_annotation_setters_raise(event_based_label_row):
    annotation = _object(event_based_label_row).get_annotation(event_based_scene.UPSERT_1)
    with pytest.raises(LabelRowError, match="read-only"):
        annotation.coordinates = CUBOID_A
    with pytest.raises(LabelRowError, match="read-only"):
        annotation.confidence = 0.5
    with pytest.raises(LabelRowError, match="read-only"):
        annotation.created_by = "someone@encord.com"
    with pytest.raises(LabelRowError, match="read-only"):
        annotation.manual_annotation = False


def test_get_annotations_is_refused(event_based_label_row):
    """The object is present over ranges, not on a list of frames, so there is no honest list to return."""
    with pytest.raises(LabelRowError, match="`get_annotations` is not available"):
        _object(event_based_label_row).get_annotations()


def test_get_annotation_frames_is_refused(event_based_label_row):
    """There is no honest frame set: the object is present over ranges, and its stored frames include the
    `delete` markers where it stops existing. Use `get_events` or `get_ranges`."""
    with pytest.raises(LabelRowError, match="get_annotation_frames"):
        _object(event_based_label_row).get_annotation_frames()


def test_get_events_includes_deletes(event_based_label_row):
    events = _object(event_based_label_row).get_events()
    assert [(e.frame, e.kind) for e in events] == [
        (event_based_scene.UPSERT_0, "upsert"),
        (event_based_scene.UPSERT_1, "upsert"),
        (event_based_scene.DELETE_2, "delete"),
        (event_based_scene.UPSERT_3, "upsert"),
        (event_based_scene.DELETE_4, "delete"),
    ]


def test_get_ranges(event_based_label_row):
    assert _object(event_based_label_row).get_ranges() == [
        Range(event_based_scene.UPSERT_0, event_based_scene.DELETE_2 - 1),
        Range(event_based_scene.UPSERT_3, event_based_scene.DELETE_4 - 1),
    ]


def test_dense_row_reads_unchanged(dense_scene_label_row):
    obj = _object(dense_scene_label_row)
    annotation = obj.get_annotation(event_based_scene.UPSERT_1)
    assert isinstance(annotation, ObjectInstance.Annotation)
    assert not isinstance(annotation, ObjectInstance.ResolvedAnnotation)
    with pytest.raises(LabelRowError):
        obj.get_annotation(event_based_scene.UPSERT_1 + 5).coordinates


def test_get_events_raises_on_dense_row(dense_scene_label_row):
    obj = _object(dense_scene_label_row)
    with pytest.raises(LabelRowError, match="not event-based"):
        obj.get_events()


def test_get_ranges_on_a_dense_row_encodes_the_annotated_frames(dense_scene_label_row):
    obj = _object(dense_scene_label_row)
    assert obj.get_ranges() == [
        Range(event_based_scene.UPSERT_0, event_based_scene.UPSERT_0),
        Range(event_based_scene.UPSERT_1, event_based_scene.UPSERT_1),
        Range(event_based_scene.DELETE_2, event_based_scene.DELETE_2),
        Range(event_based_scene.UPSERT_3, event_based_scene.UPSERT_3),
        Range(event_based_scene.DELETE_4, event_based_scene.DELETE_4),
    ]


def test_get_ranges_run_length_encodes_contiguous_frames(dense_scene_label_row):
    obj = _object(dense_scene_label_row)
    obj.set_for_frames(CUBOID_D, frames=[10, 11, 12, 20], overwrite=True)
    assert obj.get_ranges()[:3] == [
        Range(event_based_scene.UPSERT_0, event_based_scene.UPSERT_0),
        Range(10, 12),
        Range(20, 20),
    ]


CUBOID_D = CuboidCoordinates(position=(0.1, 0.1, 0.1), orientation=(0.0, 0.0, 0.0), size=(0.5, 0.5, 0.5))
CUBOID_OBJECT = all_types_structure.get_child_by_hash(event_based_scene.CUBOID_HASH)
ZERO_CUBOID = CuboidCoordinates(position=(0, 0, 0), orientation=(0, 0, 0), size=(0, 0, 0))
CLASSIFICATION = all_types_structure.classifications[0]


def _kinds(obj) -> list:
    return [(e.frame, e.kind) for e in obj.get_events()]


# ---- Dense writes refused


def test_set_for_frames_raises(event_based_label_row):
    with pytest.raises(LabelRowError, match="upsert_event"):
        _object(event_based_label_row).set_for_frames(CUBOID_D, 7)


def test_remove_from_frames_raises(event_based_label_row):
    with pytest.raises(LabelRowError, match="delete_event"):
        _object(event_based_label_row).remove_from_frames(event_based_scene.UPSERT_1)


def test_unattached_object_error_explains_how_to_attach():
    obj = ObjectInstance(CUBOID_OBJECT)
    with pytest.raises(LabelRowError, match="requires this object to be attached") as exc_info:
        obj.upsert_event(CUBOID_D, 0)
    assert "Call `label_row.add_object_instance(object_instance)` first." in str(exc_info.value)


@pytest.mark.parametrize("existing_object", [False, True], ids=["new-object", "existing-object"])
def test_frame_view_cannot_write_objects(event_based_label_row, existing_object):
    obj = _object(event_based_label_row) if existing_object else ObjectInstance(CUBOID_OBJECT)
    before = event_based_label_row.to_encord_dict()
    with pytest.raises(LabelRowError, match="event-based label row"):
        event_based_label_row.get_frame_view(7).add_object_instance(obj, CUBOID_D)
    assert event_based_label_row.to_encord_dict() == before


# ---- Upsert event


def test_upsert_new_keyframe(event_based_label_row):
    obj = _object(event_based_label_row)
    frame = event_based_scene.UPSERT_1 + 500
    obj.upsert_event(CUBOID_D, frame, created_by="writer@encord.com", confidence=0.7)
    annotation = obj.get_annotation(frame)
    assert isinstance(annotation, ObjectInstance.ResolvedAnnotation)
    assert annotation.is_virtual is False
    assert annotation.coordinates == CUBOID_D
    assert annotation.created_by == "writer@encord.com"
    assert annotation.confidence == 0.7
    assert obj.get_annotation(frame + 1).coordinates == CUBOID_D
    assert obj.get_annotation(frame - 1).coordinates == CUBOID_B
    assert event_based_label_row._frame_to_hashes[frame] == {obj.object_hash}


def test_upsert_existing_keyframe_requires_overwrite(event_based_label_row):
    obj = _object(event_based_label_row)
    with pytest.raises(LabelRowError, match="overwrite"):
        obj.upsert_event(CUBOID_D, event_based_scene.UPSERT_1)
    obj.upsert_event(CUBOID_D, event_based_scene.UPSERT_1, overwrite=True)
    assert obj.get_annotation(event_based_scene.UPSERT_1).coordinates == CUBOID_D


def test_upsert_over_delete_marker_replaces_it(event_based_label_row):
    obj = _object(event_based_label_row)
    obj.upsert_event(CUBOID_D, event_based_scene.DELETE_2)
    assert obj._event_kind_at(event_based_scene.DELETE_2) == "upsert"
    assert obj.get_annotation(event_based_scene.DELETE_2).coordinates == CUBOID_D
    assert obj.get_ranges() == [Range(0, event_based_scene.DELETE_4 - 1)]


def test_upsert_wrong_coordinate_type_raises(event_based_label_row):
    with pytest.raises(LabelRowError, match="Expected coordinates"):
        _object(event_based_label_row).upsert_event(PointCoordinate(x=0.1, y=0.1), 5)


def test_upsert_negative_frame_raises(event_based_label_row):
    with pytest.raises(LabelRowError, match="frame"):
        _object(event_based_label_row).upsert_event(CUBOID_D, -1)


def test_new_object_via_add_object_instance(event_based_label_row):
    obj = ObjectInstance(CUBOID_OBJECT)
    event_based_label_row.add_object_instance(obj)
    assert obj.is_assigned_to_label_row() is event_based_label_row
    with pytest.raises(LabelRowError, match="has no events"):
        event_based_label_row.to_encord_dict()
    obj.upsert_event(CUBOID_D, 100)
    annotation = obj.get_annotation(150)
    assert isinstance(annotation, ObjectInstance.ResolvedAnnotation)
    assert annotation.is_virtual is True
    obj.upsert_event(CUBOID_A, 200)
    obj.delete_event(300)
    assert _kinds(obj) == [(100, "upsert"), (200, "upsert"), (300, "delete")]
    exported = _frame_objects(event_based_label_row.to_encord_dict())
    assert exported[100][0]["objectHash"] == obj.object_hash
    assert exported[100][0]["event"] == "upsert"
    assert exported[300][0]["event"] == "delete"


def test_empty_object_refused_on_dense_row(dense_scene_label_row):
    obj = ObjectInstance(CUBOID_OBJECT)
    before = dense_scene_label_row.to_encord_dict()
    with pytest.raises(LabelRowError, match="not on any frames"):
        dense_scene_label_row.add_object_instance(obj)
    assert obj.is_assigned_to_label_row() is None
    assert dense_scene_label_row.to_encord_dict() == before


def test_empty_object_reserves_its_hash(event_based_label_row):
    first = ObjectInstance(CUBOID_OBJECT, object_hash="shared-hash")
    duplicate = ObjectInstance(CUBOID_OBJECT, object_hash="shared-hash")
    event_based_label_row.add_object_instance(first, force=False)
    with pytest.raises(LabelRowError, match="already previously added"):
        event_based_label_row.add_object_instance(duplicate, force=False)
    assert duplicate.is_assigned_to_label_row() is None
    first.upsert_event(CUBOID_D, 100)
    first.delete_event(200)
    assert _frame_objects(event_based_label_row.to_encord_dict())[100][0]["objectHash"] == "shared-hash"


def test_empty_object_replaces_existing_events(event_based_label_row):
    previous = _object(event_based_label_row)
    replacement = ObjectInstance(CUBOID_OBJECT, object_hash=previous.object_hash)
    event_based_label_row.add_object_instance(replacement, force=True)
    assert previous.is_assigned_to_label_row() is None
    assert replacement.is_assigned_to_label_row() is event_based_label_row
    with pytest.raises(LabelRowError, match="has no events"):
        event_based_label_row.to_encord_dict()
    replacement.upsert_event(CUBOID_D, 100)
    replacement.delete_event(200)
    exported = _frame_objects(event_based_label_row.to_encord_dict())
    assert {frame for frame, objects in exported.items() if objects} == {100, 200}
    assert exported[100][0]["objectHash"] == previous.object_hash


def test_empty_object_is_refused_on_save(event_based_label_row):
    ontology_object = all_types_structure.get_child_by_hash("MTY2MTQx")
    attribute = ontology_object.get_child_by_hash("OTkxMjU1")
    obj = ObjectInstance(ontology_object)
    event_based_label_row.add_object_instance(obj)
    obj.set_answer("hello", attribute=attribute, frames=100)
    with pytest.raises(LabelRowError, match=f"`{re.escape(obj.object_hash)}` .* has no events"):
        event_based_label_row.to_encord_dict()
    obj.upsert_event(PointCoordinate(0.1, 0.2), 100)
    obj.delete_event(200)
    exported = event_based_label_row.to_encord_dict()
    assert obj.object_hash in exported["object_answers"]
    assert obj.object_hash in exported["object_actions"]


def test_empty_replacement_preserves_other_objects_on_shared_frames(event_based_label_row):
    previous = _object(event_based_label_row)
    other = ObjectInstance(CUBOID_OBJECT)
    event_based_label_row.add_object_instance(other)
    other.upsert_event(CUBOID_D, event_based_scene.UPSERT_0)
    other.delete_event(event_based_scene.DELETE_2)
    replacement = ObjectInstance(CUBOID_OBJECT, object_hash=previous.object_hash)
    event_based_label_row.add_object_instance(replacement, force=True)
    replacement.upsert_event(CUBOID_D, 100)
    replacement.delete_event(200)
    exported = _frame_objects(event_based_label_row.to_encord_dict())
    assert {frame for frame, objects in exported.items() if objects} == {
        event_based_scene.UPSERT_0,
        100,
        200,
        event_based_scene.DELETE_2,
    }
    for frame in (event_based_scene.UPSERT_0, event_based_scene.DELETE_2):
        assert all(obj["objectHash"] == other.object_hash for obj in exported[frame])


def test_empty_unzeroable_shape_refused_at_attach(event_based_label_row):
    polygon_object = all_types_structure.get_child_by_hash("ODkxMzAx")
    obj = ObjectInstance(polygon_object)
    with pytest.raises(LabelRowError, match="cannot be placed on an event-based"):
        event_based_label_row.add_object_instance(obj)
    assert obj.is_assigned_to_label_row() is None


def test_unzeroable_shape_refused_at_attach(event_based_label_row):
    polygon_object = all_types_structure.get_child_by_hash("ODkxMzAx")  # "Polygon"
    polygon_coordinates = PolygonCoordinates(
        values=[
            PointCoordinate(x=0.2, y=0.1),
            PointCoordinate(x=0.3, y=0.2),
            PointCoordinate(x=0.5, y=0.3),
        ]
    )
    obj = ObjectInstance(polygon_object)
    obj.set_for_frames(polygon_coordinates, 0)
    with pytest.raises(LabelRowError, match="cannot be placed on an event-based"):
        event_based_label_row.add_object_instance(obj)


def test_multi_frame_object_refused_on_event_row(event_based_label_row):
    obj = ObjectInstance(CUBOID_OBJECT)
    obj.set_for_frames(CUBOID_D, [0, 1, 2])
    with pytest.raises(LabelRowError, match="per-frame coordinates"):
        event_based_label_row.add_object_instance(obj)
    assert obj.is_assigned_to_label_row() is None


def test_single_frame_dense_object_refused_on_event_row(event_based_label_row):
    """One untagged frame would become a dangling upsert that only fails at save. Refuse it at attach."""
    obj = ObjectInstance(CUBOID_OBJECT)
    obj.set_for_frames(CUBOID_D, 0)
    with pytest.raises(LabelRowError, match="per-frame coordinates"):
        event_based_label_row.add_object_instance(obj)
    assert obj.is_assigned_to_label_row() is None


def test_copy_of_a_terminated_object_can_be_added_to_another_event_row(event_based_label_row, all_types_ontology):
    original = _object(event_based_label_row)
    other_row = _scene_label_row(all_types_ontology)
    for existing in other_row.get_object_instances():
        other_row.remove_object(existing)

    copied = original.copy()
    other_row.add_object_instance(copied)

    assert copied.is_assigned_to_label_row() is other_row
    assert [(e.frame, e.kind) for e in copied.get_events()] == [(e.frame, e.kind) for e in original.get_events()]
    assert copied.get_ranges() == original.get_ranges()
    exported = _frame_objects(other_row.to_encord_dict())
    assert exported[event_based_scene.DELETE_4][0]["event"] == "delete"


def test_copy_with_dynamic_answers_over_held_ranges_is_accepted(event_based_label_row, all_types_ontology):
    ontology_object = all_types_structure.get_child_by_hash("MTY2MTQx")
    attribute = ontology_object.get_child_by_hash("OTkxMjU1")
    obj = ObjectInstance(ontology_object)
    event_based_label_row.add_object_instance(obj)
    obj.upsert_event(PointCoordinate(0.1, 0.2), 0)
    obj.delete_event(event_based_scene.DELETE_2)
    obj.set_answer("hello", attribute=attribute, frames=Range(0, event_based_scene.DELETE_2 - 1))

    other_row = _scene_label_row(all_types_ontology)
    other_row.add_object_instance(obj.copy())


def test_upsert_after_all_events_removed_reattaches_object(event_based_label_row):
    obj = _object(event_based_label_row)
    for frame in [e.frame for e in obj.get_events()]:
        if frame in obj._frames_to_instance_data:
            obj.remove_event(frame)
    assert event_based_label_row.get_object_instances() == []

    obj.upsert_event(CUBOID_D, 500)
    obj.delete_event(600)

    assert event_based_label_row.get_object_instances() == [obj]
    assert _frame_objects(event_based_label_row.to_encord_dict())[500][0]["cuboid"] == CUBOID_D.to_dict()


# ---- Delete event


def test_delete_terminates_a_stretch(event_based_label_row):
    obj = _object(event_based_label_row)
    frame = event_based_scene.UPSERT_3 + 100
    obj.delete_event(frame)
    assert _kinds(obj)[-1] == (frame, "delete")
    assert obj.get_ranges()[-1] == Range(event_based_scene.UPSERT_3, frame - 1)
    with pytest.raises(LabelRowError):
        obj.get_annotation(frame)
    assert event_based_label_row._frame_to_hashes[frame] == {obj.object_hash}


def test_delete_marker_has_zeroed_geometry_and_copied_metadata(event_based_label_row):
    obj = _object(event_based_label_row)
    frame = event_based_scene.UPSERT_3 + 100
    obj.delete_event(frame)
    event = obj.get_events()[-1]
    assert event.kind == "delete"
    # A delete carries no geometry at all: there is no attribute to read, so no zeroed cuboid can leak out.
    assert isinstance(event, LabelDeleteEvent)
    assert not hasattr(event, "coordinates")
    assert event.metadata.created_by == "annotator@encord.com"
    assert event.metadata.confidence == 1


def test_delete_where_absent_is_noop(event_based_label_row):
    obj = _object(event_based_label_row)
    before = _kinds(obj)
    obj.delete_event(event_based_scene.DELETE_2 + 5)
    assert _kinds(obj) == before


def test_delete_before_first_upsert_is_noop(event_based_label_row):
    obj = _object(event_based_label_row)
    obj.remove_event(event_based_scene.UPSERT_0)
    before = _kinds(obj)
    obj.delete_event(5)
    assert _kinds(obj) == before


def test_delete_on_opening_keyframe_removes_it(event_based_label_row):
    obj = _object(event_based_label_row)
    obj.delete_event(event_based_scene.UPSERT_3)
    assert _kinds(obj) == [
        (event_based_scene.UPSERT_0, "upsert"),
        (event_based_scene.UPSERT_1, "upsert"),
        (event_based_scene.DELETE_2, "delete"),
    ]


def test_delete_on_non_opening_keyframe_flips_it_and_prunes(event_based_label_row):
    obj = _object(event_based_label_row)
    obj.delete_event(event_based_scene.UPSERT_1)
    assert _kinds(obj) == [
        (event_based_scene.UPSERT_0, "upsert"),
        (event_based_scene.UPSERT_1, "delete"),
        (event_based_scene.UPSERT_3, "upsert"),
        (event_based_scene.DELETE_4, "delete"),
    ]
    assert obj.object_hash not in event_based_label_row._frame_to_hashes[event_based_scene.DELETE_2]


def test_deleting_every_stretch_removes_object_from_row(event_based_label_row):
    obj = _object(event_based_label_row)
    obj.delete_event(event_based_scene.UPSERT_3)
    obj.delete_event(event_based_scene.UPSERT_0)
    # UPSERT_1 is its own stored keyframe, so the object is still present from there until DELETE_2.
    assert _kinds(obj) == [(event_based_scene.UPSERT_1, "upsert"), (event_based_scene.DELETE_2, "delete")]
    obj.delete_event(event_based_scene.UPSERT_1)
    # Removing the last opening keyframe leaves DELETE_2 dangling; it is pruned and the object is dropped.
    assert event_based_label_row.get_object_instances() == []
    assert obj.object_hash not in event_based_label_row._frame_to_hashes[event_based_scene.DELETE_2]


# ---- Remove event


def test_remove_upsert(event_based_label_row):
    obj = _object(event_based_label_row)
    obj.remove_event(event_based_scene.UPSERT_1)
    assert obj.get_annotation(event_based_scene.UPSERT_1).coordinates == CUBOID_A
    assert obj.object_hash not in event_based_label_row._frame_to_hashes[event_based_scene.UPSERT_1]


def test_remove_delete_marker_extends_previous_upsert(event_based_label_row):
    obj = _object(event_based_label_row)
    obj.remove_event(event_based_scene.DELETE_2)
    assert obj.get_annotation(event_based_scene.DELETE_2 + 1).coordinates == CUBOID_B


def test_remove_prunes_dangling_deletes(event_based_label_row):
    obj = _object(event_based_label_row)
    obj.remove_event(event_based_scene.UPSERT_0)
    obj.remove_event(event_based_scene.UPSERT_1)
    assert _kinds(obj) == [(event_based_scene.UPSERT_3, "upsert"), (event_based_scene.DELETE_4, "delete")]


def test_remove_missing_raises(event_based_label_row):
    with pytest.raises(LabelRowError, match="No event"):
        _object(event_based_label_row).remove_event(123)


def test_remove_all_drops_object(event_based_label_row):
    obj = _object(event_based_label_row)
    for frame in [e.frame for e in obj.get_events()]:
        if frame in obj._frames_to_instance_data:
            obj.remove_event(frame)
    assert event_based_label_row.get_object_instances() == []


def test_event_writes_raise_on_dense_row(dense_scene_label_row):
    obj = _object(dense_scene_label_row)
    with pytest.raises(LabelRowError, match="not event-based"):
        obj.upsert_event(CUBOID_D, 5)
    with pytest.raises(LabelRowError, match="not event-based"):
        obj.delete_event(5)
    with pytest.raises(LabelRowError, match="not event-based"):
        obj.remove_event(event_based_scene.UPSERT_1)


# ---- Non-geometric objects on an event row


def test_force_replacement_preserves_the_existing_range_object_handle(event_based_label_row):
    text_object = all_types_structure.get_child_by_hash("textFeatureNodeHash", Object)
    original = ObjectInstance(text_object, object_hash="range-replacement")
    replacement = ObjectInstance(text_object, object_hash=original.object_hash)
    original.set_for_frames(TextCoordinates(range=[Range(0, 5)]), 0)
    replacement.set_for_frames(TextCoordinates(range=[Range(1, 6)]), 0)
    event_based_label_row.add_object_instance(original)

    event_based_label_row.add_object_instance(replacement, force=True)

    assert original.is_assigned_to_label_row() is event_based_label_row
    assert replacement.is_assigned_to_label_row() is event_based_label_row
    assert replacement.get_annotation().coordinates == TextCoordinates(range=[Range(1, 6)])


def test_text_object_stays_range_based_on_event_row(event_based_label_row):
    text_object = all_types_structure.get_child_by_hash("textFeatureNodeHash")  # "text object"
    obj = ObjectInstance(text_object)
    obj.set_for_frames(TextCoordinates(range=[Range(start=0, end=5)]), 0)
    event_based_label_row.add_object_instance(obj)

    annotation = obj.get_annotation(0)
    coordinates = annotation.coordinates
    assert isinstance(coordinates, TextCoordinates)
    assert coordinates.range == [Range(start=0, end=5)]
    assert isinstance(annotation, ObjectInstance.Annotation)
    assert not isinstance(annotation, ObjectInstance.ResolvedAnnotation)

    with pytest.raises(LabelRowError, match="not event-based"):
        obj.get_events()


def _frame_objects(encord_dict: dict) -> dict:
    labels = encord_dict["data_units"][event_based_scene.DATA_HASH]["labels"]
    return {int(frame): frame_labels["objects"] for frame, frame_labels in labels.items()}


# ---- Serialisation


def test_export_tags_every_entry_and_keeps_delete_markers(event_based_label_row):
    objects_by_frame = _frame_objects(event_based_label_row.to_encord_dict())
    assert sorted(objects_by_frame) == [
        event_based_scene.UPSERT_0,
        event_based_scene.UPSERT_1,
        event_based_scene.DELETE_2,
        event_based_scene.UPSERT_3,
        event_based_scene.DELETE_4,
    ]
    assert objects_by_frame[event_based_scene.UPSERT_0][0]["event"] == "upsert"  # untagged input made explicit
    assert objects_by_frame[event_based_scene.UPSERT_1][0]["event"] == "upsert"
    delete_entry = objects_by_frame[event_based_scene.DELETE_2][0]
    assert delete_entry["event"] == "delete"
    assert delete_entry["cuboid"] == ZERO_CUBOID.to_dict()


def test_dense_row_export_never_carries_event_tags(dense_scene_label_row):
    """An `event` tag and an event-based row imply each other: a frame-based row never writes one."""
    for entries in _frame_objects(dense_scene_label_row.to_encord_dict()).values():
        assert all("event" not in entry for entry in entries)


def test_dense_row_without_tags_exports_none(empty_video_label_row):
    obj = ObjectInstance(CUBOID_OBJECT)
    obj.set_for_frames(CUBOID_D, 0)
    empty_video_label_row.add_object_instance(obj)
    exported = empty_video_label_row.to_encord_dict()
    [data_unit] = exported["data_units"].values()
    objects_by_frame = {int(frame): frame_labels["objects"] for frame, frame_labels in data_unit["labels"].items()}
    assert all("event" not in entry for entries in objects_by_frame.values() for entry in entries)


def test_written_events_round_trip(event_based_label_row, all_types_ontology):
    obj = _object(event_based_label_row)
    obj.upsert_event(CUBOID_D, event_based_scene.DELETE_4 + 100)
    obj.delete_event(event_based_scene.DELETE_4 + 200)
    exported = event_based_label_row.to_encord_dict()

    reloaded = _scene_label_row(all_types_ontology, deepcopy(exported))
    assert _kinds(_object(reloaded)) == _kinds(obj)
    assert _object(reloaded).get_ranges() == obj.get_ranges()
    assert reloaded.to_encord_dict()["data_units"] == exported["data_units"]


def test_pruned_frames_leave_no_empty_entry(event_based_label_row, all_types_ontology):
    """A frame exists only because an event sits on it, so pruning the event must take the frame with it."""
    obj = _object(event_based_label_row)
    obj.upsert_event(CUBOID_D, event_based_scene.UPSERT_3 + 100)
    obj.delete_event(event_based_scene.UPSERT_3 + 200)  # DELETE_4 now follows a delete, so it is pruned
    assert event_based_scene.DELETE_4 not in {e.frame for e in obj.get_events()}
    assert event_based_scene.DELETE_4 not in event_based_label_row._frame_to_hashes

    exported = event_based_label_row.to_encord_dict()
    assert event_based_scene.DELETE_4 not in _frame_objects(exported)

    reloaded = _scene_label_row(all_types_ontology, deepcopy(exported))
    assert reloaded.to_encord_dict()["data_units"] == exported["data_units"]


def test_parse_works_when_flag_set_before_parsing(all_types_ontology):
    metadata_dict = asdict(BASE_LABEL_ROW_METADATA)
    metadata_dict["data_type"] = "SCENE"
    metadata_dict["data_hash"] = event_based_scene.DATA_HASH
    metadata_dict["number_of_frames"] = 0
    metadata_dict["frames_per_second"] = None
    metadata_dict["duration"] = None
    label_row = LabelRowV2(LabelRowMetadata(**metadata_dict), Mock(), all_types_ontology)
    label_row._event_based = True
    labels = deepcopy(EVENT_BASED_SCENE_LABELS)
    labels.pop("scene")  # no scene metadata: only the override says event-based
    label_row.from_labels_dict(labels)
    assert _kinds(_object(label_row)) == [
        (event_based_scene.UPSERT_0, "upsert"),
        (event_based_scene.UPSERT_1, "upsert"),
        (event_based_scene.DELETE_2, "delete"),
        (event_based_scene.UPSERT_3, "upsert"),
        (event_based_scene.DELETE_4, "delete"),
    ]


# ---- Frame views on event rows
# A single frame view resolves: `frame` is a nanosecond offset, and reads answer presence over ranges.
# Enumerating every frame cannot: the timeline is continuous, so `get_frame_views` refuses.


def test_get_frame_views_is_refused(event_based_label_row):
    with pytest.raises(LabelRowError, match="`get_frame_views` is not available"):
        event_based_label_row.get_frame_views()


def test_dense_scene_row_still_enumerates(dense_scene_label_row):
    """The refusal keys off the row being event-based, not off the data type."""
    assert dense_scene_label_row.get_frame_views() == []


def test_view_between_keyframes_resolves_the_object(event_based_label_row):
    """Nothing is stored here, but an upsert holds over it, so the object is present."""
    view = event_based_label_row.get_frame_view(event_based_scene.UPSERT_1 + 5)
    assert [o.object_hash for o in view.get_object_instances()] == [event_based_scene.OBJECT_HASH]


def test_view_inside_a_deleted_stretch_is_empty(event_based_label_row):
    assert event_based_label_row.get_frame_view(event_based_scene.DELETE_2 + 5).get_object_instances() == []


def test_view_past_the_closing_delete_is_empty(event_based_label_row):
    assert event_based_label_row.get_frame_view(event_based_scene.DELETE_4 + 5).get_object_instances() == []


def test_view_on_a_keyframe_resolves_the_object(event_based_label_row):
    view = event_based_label_row.get_frame_view(event_based_scene.UPSERT_3)
    assert [o.object_hash for o in view.get_object_instances()] == [event_based_scene.OBJECT_HASH]


def test_writing_through_the_view_is_still_refused(event_based_label_row):
    view = event_based_label_row.get_frame_view(event_based_scene.UPSERT_1)
    with pytest.raises(LabelRowError):
        view.add_object_instance(_object(event_based_label_row), CUBOID_D)


def test_range_filter_is_not_expanded(event_based_label_row):
    """A ns range must never be walked frame by frame; presence is range intersection."""
    whole_timeline = Range(event_based_scene.UPSERT_0, event_based_scene.DELETE_4)
    assert len(event_based_label_row.get_object_instances(filter_frames=whole_timeline)) == 1
    gap = Range(event_based_scene.DELETE_2 + 1, event_based_scene.UPSERT_3 - 1)
    assert event_based_label_row.get_object_instances(filter_frames=gap) == []


# ---- Classifications on event rows
# Classifications on a ns timeline are ranges. A per-frame classification would store an entry per
# nanosecond, and a per-frame filter would walk them.


def test_frame_based_classification_is_refused_at_attach(event_based_label_row):
    classification = CLASSIFICATION.create_instance()  # range_only defaults to False
    classification.set_for_frames(0)
    with pytest.raises(LabelRowError, match="range_only"):
        event_based_label_row.add_classification_instance(classification)
    assert classification.is_assigned_to_label_row() is False


def test_frame_view_cannot_add_a_frame_based_classification(event_based_label_row):
    view = event_based_label_row.get_frame_view(500)
    with pytest.raises(LabelRowError, match="range_only"):
        view.add_classification_instance(CLASSIFICATION.create_instance())
    assert event_based_label_row.get_classification_instances() == []


def test_range_only_classification_over_a_ns_range(event_based_label_row):
    classification = CLASSIFICATION.create_instance(range_only=True)
    classification.set_for_frames(Range(event_based_scene.UPSERT_1, event_based_scene.UPSERT_3))
    event_based_label_row.add_classification_instance(classification)
    [exported] = event_based_label_row.to_encord_dict()["classification_answers"].values()
    assert exported["range"] == [[event_based_scene.UPSERT_1, event_based_scene.UPSERT_3]]


def test_classification_range_filter_is_not_expanded(event_based_label_row):
    classification = CLASSIFICATION.create_instance(range_only=True)
    classification.set_for_frames(Range(event_based_scene.UPSERT_1, event_based_scene.UPSERT_3))
    event_based_label_row.add_classification_instance(classification)

    started = time.monotonic()
    whole_timeline = Range(0, event_based_scene.DELETE_4)
    assert event_based_label_row.get_classification_instances(filter_frames=whole_timeline) == [classification]
    before = Range(0, event_based_scene.UPSERT_1 - 1)
    assert event_based_label_row.get_classification_instances(filter_frames=before) == []
    assert event_based_label_row.get_frame_view(event_based_scene.UPSERT_1 + 5).get_classification_instances() == [
        classification
    ]
    assert time.monotonic() - started < 1.0


def test_parsed_classifications_are_range_only(all_types_ontology):
    labels = deepcopy(EVENT_BASED_SCENE_LABELS)
    labels["scene"] = {"isContinuous": True}
    labels["classification_answers"] = {
        "clsHash01": {
            "classificationHash": "clsHash01",
            "featureHash": CLASSIFICATION.feature_node_hash,
            "classifications": [],
            "range": [[event_based_scene.UPSERT_1, event_based_scene.UPSERT_3]],
            "createdAt": "Mon, 11 Jul 2022 17:10:51 UTC",
            "createdBy": "annotator@encord.com",
            "lastEditedAt": "Mon, 11 Jul 2022 17:10:51 UTC",
            "lastEditedBy": "annotator@encord.com",
            "manualAnnotation": True,
        }
    }
    row = _scene_label_row(all_types_ontology, labels)
    [classification] = row.get_classification_instances()
    assert classification.is_range_only() is True
    assert [(r.start, r.end) for r in classification.range_list] == [
        (event_based_scene.UPSERT_1, event_based_scene.UPSERT_3)
    ]


# ---- Dynamic answers over ranges
# Answers are held as ranges, never as the frames inside them. On a ns timeline expanding a range is
# ruinous — a one-second range is a billion entries — and save and load are range-based either way.


def _object_with_dynamic_attribute(label_row):
    ontology_object = all_types_structure.get_child_by_hash("MTY2MTQx")
    attribute = ontology_object.get_child_by_hash("OTkxMjU1")
    obj = ObjectInstance(ontology_object)
    label_row.add_object_instance(obj)
    obj.upsert_event(PointCoordinate(0.1, 0.2), event_based_scene.UPSERT_0)
    obj.delete_event(event_based_scene.DELETE_4)
    return obj, attribute


def test_answer_over_a_ns_range_is_stored_as_a_range(event_based_label_row):
    obj, attribute = _object_with_dynamic_attribute(event_based_label_row)
    range = Range(event_based_scene.UPSERT_1, event_based_scene.UPSERT_3)
    obj.set_answer("hello", attribute=attribute, frames=range)
    [answered] = cast(AnswersForFrames, obj.get_answer(attribute))
    assert answered.answer == "hello"
    assert [(r.start, r.end) for r in answered.ranges] == [(range.start, range.end)]


def test_read_inside_the_range_resolves(event_based_label_row):
    obj, attribute = _object_with_dynamic_attribute(event_based_label_row)
    obj.set_answer("hello", attribute=attribute, frames=Range(event_based_scene.UPSERT_1, event_based_scene.UPSERT_3))
    midpoint = event_based_scene.UPSERT_1 + 500
    answers = cast(AnswersForFrames, obj.get_answer(attribute, filter_frame=midpoint))
    assert answers[0].answer == "hello"


def test_read_outside_the_range_finds_nothing(event_based_label_row):
    obj, attribute = _object_with_dynamic_attribute(event_based_label_row)
    obj.set_answer("hello", attribute=attribute, frames=Range(event_based_scene.UPSERT_1, event_based_scene.UPSERT_3))
    assert obj.get_answer(attribute, filter_frame=event_based_scene.UPSERT_3 + 1) == []


def test_a_single_frame_is_just_a_degenerate_range(event_based_label_row):
    obj, attribute = _object_with_dynamic_attribute(event_based_label_row)
    obj.set_answer("hello", attribute=attribute, frames=event_based_scene.UPSERT_1)
    [answered] = cast(AnswersForFrames, obj.get_answer(attribute))
    assert [(r.start, r.end) for r in answered.ranges] == [(event_based_scene.UPSERT_1, event_based_scene.UPSERT_1)]


def test_deleting_one_frame_splits_the_range(event_based_label_row):
    """The range is carved in place rather than rebuilt from a frame set."""
    obj, attribute = _object_with_dynamic_attribute(event_based_label_row)
    obj.set_answer("hello", attribute=attribute, frames=Range(0, 1000))
    obj.delete_answer(attribute, filter_frame=500)
    [answered] = cast(AnswersForFrames, obj.get_answer(attribute))
    assert [(r.start, r.end) for r in answered.ranges] == [(0, 499), (501, 1000)]


def test_a_range_of_a_billion_frames_is_never_walked(event_based_label_row):
    """Expanding this would be ~4 billion entries; as ranges it is instant."""
    obj, attribute = _object_with_dynamic_attribute(event_based_label_row)
    started = time.monotonic()
    obj.set_answer("hello", attribute=attribute, frames=Range(0, event_based_scene.DELETE_4))
    found = cast(AnswersForFrames, obj.get_answer(attribute, filter_frame=event_based_scene.UPSERT_3))
    assert found[0].answer == "hello"
    assert time.monotonic() - started < 1.0


def test_answer_without_frames_covers_the_held_ranges_not_the_keyframes(event_based_label_row):
    """`frames=None` means everywhere the object has coordinates. On an event-based row that is every offset
    an upsert holds over, not the handful of offsets the upserts sit on."""
    ontology_object = all_types_structure.get_child_by_hash("MTY2MTQx")
    attribute = ontology_object.get_child_by_hash("OTkxMjU1")
    obj = ObjectInstance(ontology_object)
    event_based_label_row.add_object_instance(obj)
    obj.upsert_event(PointCoordinate(0.1, 0.2), event_based_scene.UPSERT_0)
    obj.upsert_event(PointCoordinate(0.2, 0.2), event_based_scene.UPSERT_1)
    obj.delete_event(event_based_scene.DELETE_2)
    obj.upsert_event(PointCoordinate(0.3, 0.3), event_based_scene.UPSERT_3)
    obj.delete_event(event_based_scene.DELETE_4)

    obj.set_answer("hello", attribute=attribute)

    [answered] = cast(AnswersForFrames, obj.get_answer(attribute))
    assert [(r.start, r.end) for r in answered.ranges] == [(r.start, r.end) for r in obj.get_ranges()]
    midpoint = event_based_scene.UPSERT_0 + 500
    assert cast(AnswersForFrames, obj.get_answer(attribute, filter_frame=midpoint))[0].answer == "hello"
    assert obj.get_answer(attribute, filter_frame=event_based_scene.DELETE_2 + 500) == []
    obj.are_dynamic_answers_valid()


def test_answer_without_frames_on_a_dangling_object_raises(event_based_label_row):
    obj, attribute = _object_with_dynamic_attribute(event_based_label_row)
    obj.upsert_event(PointCoordinate(0.5, 0.5), event_based_scene.DELETE_4)  # replaces the terminator
    with pytest.raises(LabelRowError, match="end on an `upsert`"):
        obj.set_answer("hello", attribute=attribute)


# ---- Dangling upsert
# A stretch with no closing `delete` has no end. It may dangle mid-edit, but never on parse or on save.


def _labels_without_the_closing_delete() -> dict:
    labels = deepcopy(EVENT_BASED_SCENE_LABELS)
    del labels["data_units"][event_based_scene.DATA_HASH]["labels"][str(event_based_scene.DELETE_4)]
    return labels


def test_parsing_a_dangling_upsert_raises(all_types_ontology):
    metadata_dict = asdict(BASE_LABEL_ROW_METADATA)
    metadata_dict["data_type"] = "SCENE"
    metadata_dict["data_hash"] = event_based_scene.DATA_HASH
    metadata_dict["number_of_frames"] = 0
    metadata_dict["frames_per_second"] = None
    metadata_dict["duration"] = None
    label_row = LabelRowV2(LabelRowMetadata(**metadata_dict), Mock(), all_types_ontology)
    label_row._event_based = True
    with pytest.raises(LabelRowError, match="events end on an `upsert` at frame `3000000000`"):
        label_row.from_labels_dict(_labels_without_the_closing_delete())


def test_dense_row_parses_the_same_geometry_fine(all_types_ontology):
    """The layout is only unsupported where the entries are read as events."""
    label_row = _scene_label_row(all_types_ontology, dense_scene_labels(_labels_without_the_closing_delete()))
    assert label_row.get_object_instances() != []


def test_saving_a_dangling_upsert_raises(event_based_label_row):
    obj = _object(event_based_label_row)
    obj.upsert_event(CUBOID_D, event_based_scene.DELETE_4 + 100)
    with pytest.raises(LabelRowError, match="events end on an `upsert` at frame `4000000100`"):
        event_based_label_row.to_encord_dict()


@pytest.mark.parametrize("validate_before_saving", [False, True])
@pytest.mark.parametrize("malformation", ["missing-delete", "removed-delete", "overwritten-delete", "reopened-track"])
def test_save_refuses_unterminated_object_before_upload(event_based_label_row, malformation, validate_before_saving):
    obj = _object(event_based_label_row)
    if malformation == "missing-delete":
        obj = ObjectInstance(CUBOID_OBJECT)
        event_based_label_row.add_object_instance(obj)
        obj.upsert_event(CUBOID_D, 100)
    elif malformation == "removed-delete":
        obj.remove_event(event_based_scene.DELETE_4)
    elif malformation == "overwritten-delete":
        obj.upsert_event(CUBOID_D, event_based_scene.DELETE_4, overwrite=True)
    else:
        obj.upsert_event(CUBOID_D, event_based_scene.DELETE_4 + 100)

    events_before = _kinds(obj)
    last_frame = events_before[-1][0]
    with pytest.raises(
        LabelRowError,
        match=f"events end on an `upsert` at frame `{last_frame}`",
    ) as error:
        event_based_label_row.save(validate_before_saving=validate_before_saving)
    assert f"Object `{obj.object_hash}`:" in str(error.value)
    event_based_label_row._project_client.save_label_rows.assert_not_called()
    assert _kinds(obj) == events_before

    obj.delete_event(last_frame + 1)
    event_based_label_row.save(validate_before_saving=validate_before_saving)
    event_based_label_row._project_client.save_label_rows.assert_called_once()
    kwargs = event_based_label_row._project_client.save_label_rows.call_args.kwargs
    assert kwargs["validate_before_saving"] is validate_before_saving
    [saved] = kwargs["payload"]
    saved_events = [
        (frame, entry["event"])
        for frame, entries in sorted(_frame_objects(saved).items())
        for entry in entries
        if entry["objectHash"] == obj.object_hash
    ]
    assert saved_events == events_before + [(last_frame + 1, "delete")]


def test_dangling_upsert_error_points_at_the_fix(event_based_label_row):
    obj = _object(event_based_label_row)
    obj.upsert_event(CUBOID_D, event_based_scene.DELETE_4 + 100)
    with pytest.raises(LabelRowError, match="insert the `delete` one past the end"):
        obj.get_ranges()


def test_dangling_is_allowed_while_editing(event_based_label_row):
    obj = _object(event_based_label_row)
    obj.upsert_event(CUBOID_D, event_based_scene.DELETE_4 + 100)  # dangles until the next line closes it
    obj.delete_event(event_based_scene.DELETE_4 + 200)
    assert obj.get_ranges()[-1] == Range(
        event_based_scene.DELETE_4 + 100,
        event_based_scene.DELETE_4 + 199,
    )
    assert sorted(_frame_objects(event_based_label_row.to_encord_dict())) == [
        event_based_scene.UPSERT_0,
        event_based_scene.UPSERT_1,
        event_based_scene.DELETE_2,
        event_based_scene.UPSERT_3,
        event_based_scene.DELETE_4,
        event_based_scene.DELETE_4 + 100,
        event_based_scene.DELETE_4 + 200,
    ]


# ---- Delete marker without geometry
# The editor may save a `delete` marker with its geometry key absent or null; the SDK substitutes the zeroed
# placeholder.


def _labels_with_bare_delete(null: bool) -> dict:
    labels = deepcopy(EVENT_BASED_SCENE_LABELS)
    entry = labels["data_units"][event_based_scene.DATA_HASH]["labels"][str(event_based_scene.DELETE_2)]["objects"][0]
    if null:
        entry["cuboid"] = None
    else:
        del entry["cuboid"]
    return labels


@pytest.mark.parametrize("null", [False, True], ids=["absent", "null"])
def test_bare_delete_marker_parses_as_zeroed_geometry(all_types_ontology, null):
    metadata_dict = asdict(BASE_LABEL_ROW_METADATA)
    metadata_dict["data_type"] = "SCENE"
    metadata_dict["data_hash"] = event_based_scene.DATA_HASH
    metadata_dict["number_of_frames"] = 0
    metadata_dict["frames_per_second"] = None
    metadata_dict["duration"] = None
    label_row = LabelRowV2(LabelRowMetadata(**metadata_dict), Mock(), all_types_ontology)
    label_row.from_labels_dict(_labels_with_bare_delete(null))

    obj = _object(label_row)
    delete = [e for e in obj.get_events() if e.kind == "delete"]
    assert [e.frame for e in delete] == [event_based_scene.DELETE_2, event_based_scene.DELETE_4]
    assert all(isinstance(e, LabelDeleteEvent) for e in delete)  # parsed as deletes, carrying no geometry
    with pytest.raises(LabelRowError, match="does not exist"):
        obj.get_annotation(event_based_scene.DELETE_2)

    exported_delete = _frame_objects(label_row.to_encord_dict())[event_based_scene.DELETE_2][0]
    assert exported_delete["event"] == "delete"
    assert exported_delete["cuboid"] == ZERO_CUBOID.to_dict()


def test_bare_upsert_still_raises(all_types_ontology):
    """Only delete markers get the placeholder; an upsert without geometry is still a malformed label."""
    labels = deepcopy(EVENT_BASED_SCENE_LABELS)
    entry = labels["data_units"][event_based_scene.DATA_HASH]["labels"][str(event_based_scene.UPSERT_1)]["objects"][0]
    del entry["cuboid"]
    metadata_dict = asdict(BASE_LABEL_ROW_METADATA)
    metadata_dict["data_type"] = "SCENE"
    metadata_dict["data_hash"] = event_based_scene.DATA_HASH
    metadata_dict["number_of_frames"] = 0
    metadata_dict["frames_per_second"] = None
    metadata_dict["duration"] = None
    label_row = LabelRowV2(LabelRowMetadata(**metadata_dict), Mock(), all_types_ontology)
    with pytest.raises((KeyError, TypeError, NotImplementedError)):
        label_row.from_labels_dict(labels)


# ---- Space objects stay dense
# Objects on spaces (e.g. point-cloud segmentations) have no time axis; the row flag must not touch them.


def _scene_row_with_segmentation():
    from tests.objects.data.all_types_ontology_structure import all_types_structure as structure
    from tests.objects.data.data_group.scene import SCENE_METADATA, SCENE_WITH_LABELS

    ontology_structure = Mock()
    ontology_structure.get_child_by_hash = structure.get_child_by_hash
    label_row = LabelRowV2(SCENE_METADATA, Mock(), Mock(structure=ontology_structure))
    label_row.from_labels_dict(deepcopy(SCENE_WITH_LABELS))  # 1 root cuboid, 1 segmentation on two point clouds
    label_row._event_based = True
    return label_row


def test_segmentation_on_point_cloud_space_is_not_event_based():
    label_row = _scene_row_with_segmentation()
    space = label_row.get_space(id="path/to/file1.pcd", type_="point_cloud")
    [segmentation] = space.get_object_instances()

    assert segmentation._is_assigned_to_space()
    assert segmentation._is_event_based() is False
    assert [(r.start, r.end) for r in space.get_object_ranges(segmentation)] == [(0, 5)]
    assert len(segmentation.get_annotations()) >= 1  # delegates to the spaces, not the (empty) event store
    with pytest.raises(LabelRowError, match="not event-based"):
        segmentation.get_events()


def test_space_object_stays_dense_even_with_a_parent():
    label_row = _scene_row_with_segmentation()
    space = label_row.get_space(id="path/to/file1.pcd", type_="point_cloud")
    [segmentation] = space.get_object_instances()
    segmentation._parent = label_row  # defensive: a future code path attaching space objects to the row
    assert segmentation._is_event_based() is False


def test_root_cuboid_on_same_row_is_event_based():
    label_row = _scene_row_with_segmentation()
    [cuboid] = label_row.get_object_instances()
    assert cuboid._is_event_based() is True
    assert all(e.kind == "upsert" for e in cuboid.get_events())


# ---- Auto-detection
# The enriched label-row scene metadata declares whether root objects are event-based.


def _auto_detection_row(all_types_ontology) -> tuple[LabelRowV2, Mock]:
    metadata_dict = asdict(BASE_LABEL_ROW_METADATA)
    metadata_dict["data_type"] = "SCENE"
    metadata_dict["data_hash"] = event_based_scene.DATA_HASH
    metadata_dict["number_of_frames"] = 0
    metadata_dict["frames_per_second"] = None
    metadata_dict["duration"] = None
    project_client = Mock()
    label_row = LabelRowV2(LabelRowMetadata(**metadata_dict), project_client, all_types_ontology)
    return label_row, project_client


def _labels_with_scene_metadata(continuous) -> dict:
    # A tag only has a meaning on a continuous row, so the frame-based variants carry none.
    labels = deepcopy(EVENT_BASED_SCENE_LABELS) if continuous else dense_scene_labels()
    labels["scene"] = {"isContinuous": continuous}
    return labels


def test_continuous_scene_is_event_based(all_types_ontology):
    label_row, project_client = _auto_detection_row(all_types_ontology)
    label_row.from_labels_dict(_labels_with_scene_metadata(True))
    assert label_row.is_event_based is True
    obj = _object(label_row)
    assert [e.kind for e in obj.get_events()] == ["upsert", "upsert", "delete", "upsert", "delete"]
    assert isinstance(obj.get_annotation(event_based_scene.UPSERT_1 + 5), ObjectInstance.ResolvedAnnotation)
    project_client._api_client.get.assert_not_called()


@pytest.mark.parametrize("continuous", [False, None], ids=["false", "null"])
def test_non_continuous_scene_stays_dense(all_types_ontology, continuous):
    label_row, _ = _auto_detection_row(all_types_ontology)
    label_row.from_labels_dict(_labels_with_scene_metadata(continuous))
    assert label_row.is_event_based is False
    with pytest.raises(LabelRowError, match="not event-based"):
        _object(label_row).get_events()


def test_legacy_payload_without_scene_metadata_stays_dense(all_types_ontology):
    label_row, project_client = _auto_detection_row(all_types_ontology)
    label_row.from_labels_dict(dense_scene_labels())
    assert label_row.is_event_based is False
    project_client._api_client.get.assert_not_called()


def test_uninitialised_row_raises(all_types_ontology):
    label_row, _ = _auto_detection_row(all_types_ontology)
    with pytest.raises(LabelRowError, match="initialize labelling"):
        _ = label_row.is_event_based


def test_explicit_flag_overrides_detection(all_types_ontology):
    label_row, _ = _auto_detection_row(all_types_ontology)
    label_row._event_based = False
    assert label_row.is_event_based is False
    label_row._event_based = True
    assert label_row.is_event_based is True


# ---- `interpolate` passthrough
# `interpolate` is a reserved per-keyframe field the editor may write. The SDK reads only `hold`, which is
# what it already does; it round-trips that verbatim, never invents it, and never surfaces it publicly.


def _labels_with_interpolate(mode="hold") -> dict:
    labels = deepcopy(EVENT_BASED_SCENE_LABELS)
    unit_labels = labels["data_units"][event_based_scene.DATA_HASH]["labels"]
    unit_labels[str(event_based_scene.UPSERT_0)]["objects"][0]["interpolate"] = mode
    unit_labels[str(event_based_scene.UPSERT_3)]["objects"][0]["interpolate"] = mode
    return labels


def _interpolate_row(all_types_ontology):
    metadata_dict = asdict(BASE_LABEL_ROW_METADATA)
    metadata_dict["data_type"] = "SCENE"
    metadata_dict["data_hash"] = event_based_scene.DATA_HASH
    metadata_dict["number_of_frames"] = 0
    metadata_dict["frames_per_second"] = None
    metadata_dict["duration"] = None
    label_row = LabelRowV2(LabelRowMetadata(**metadata_dict), Mock(), all_types_ontology)
    label_row.from_labels_dict(_labels_with_interpolate())
    return label_row


def test_interpolate_round_trips_verbatim_and_only_where_present(all_types_ontology):
    exported = _frame_objects(_interpolate_row(all_types_ontology).to_encord_dict())
    assert exported[event_based_scene.UPSERT_0][0]["interpolate"] == "hold"
    assert exported[event_based_scene.UPSERT_3][0]["interpolate"] == "hold"
    assert "interpolate" not in exported[event_based_scene.UPSERT_1][0]
    assert "interpolate" not in exported[event_based_scene.DELETE_2][0]


def test_interpolate_not_emitted_when_absent_anywhere(event_based_label_row):
    exported = _frame_objects(event_based_label_row.to_encord_dict())
    assert all("interpolate" not in o for entries in exported.values() for o in entries)


def test_sdk_created_events_never_carry_interpolate(all_types_ontology):
    label_row = _interpolate_row(all_types_ontology)
    obj = _object(label_row)
    obj.upsert_event(CUBOID_D, event_based_scene.UPSERT_3 + 100)
    obj.delete_event(event_based_scene.UPSERT_3 + 200)
    obj.delete_event(event_based_scene.UPSERT_0 + 500)  # flips nothing at 0 itself; a marker after the keyframe
    exported = _frame_objects(label_row.to_encord_dict())
    assert "interpolate" not in exported[event_based_scene.UPSERT_3 + 100][0]
    assert "interpolate" not in exported[event_based_scene.UPSERT_3 + 200][0]
    assert exported[event_based_scene.UPSERT_0][0]["interpolate"] == "hold"  # untouched keyframe keeps it


def test_delete_over_a_keyframe_drops_interpolate(all_types_ontology):
    label_row = _interpolate_row(all_types_ontology)
    obj = _object(label_row)
    obj.delete_event(event_based_scene.UPSERT_3)  # UPSERT_3 opens a stretch -> keyframe removed
    obj.delete_event(event_based_scene.UPSERT_1)  # flips the keyframe at UPSERT_1 into a delete marker
    exported = _frame_objects(label_row.to_encord_dict())
    assert exported[event_based_scene.UPSERT_1][0]["event"] == "delete"
    assert "interpolate" not in exported[event_based_scene.UPSERT_1][0]


def test_overwriting_a_keyframe_keeps_interpolate(all_types_ontology):
    label_row = _interpolate_row(all_types_ontology)
    obj = _object(label_row)
    obj.upsert_event(CUBOID_D, event_based_scene.UPSERT_0, overwrite=True)
    assert _frame_objects(label_row.to_encord_dict())[event_based_scene.UPSERT_0][0]["interpolate"] == "hold"


def test_interpolate_not_exposed_on_public_objects(all_types_ontology):
    obj = _object(_interpolate_row(all_types_ontology))
    event = obj.get_events()[0]
    view = obj.get_annotation(event_based_scene.UPSERT_0)
    assert not hasattr(event, "interpolate") and not hasattr(view, "interpolate")
    assert "interpolate" not in {f for f in dir(event) if not f.startswith("_")}


@pytest.mark.parametrize("mode", ["hold", None], ids=["hold", "null"])
def test_no_interpolation_forms_are_accepted(all_types_ontology, mode):
    """Unset is the usual case; an explicit `null` and `hold` say the same thing and are equally fine."""
    label_row = _scene_label_row(all_types_ontology, _labels_with_interpolate(mode))
    exported = _frame_objects(label_row.to_encord_dict())
    assert exported[event_based_scene.UPSERT_0][0].get("interpolate") == mode


@pytest.mark.parametrize("mode", ["linear", "flat", "cubic", "HOLD", ""])
def test_unsupported_interpolate_mode_is_refused(all_types_ontology, mode):
    """Reading an interpolated label as if it held constant would report coordinates the platform never
    shows, so the SDK refuses the row instead of quietly misreading it."""
    metadata_dict = asdict(BASE_LABEL_ROW_METADATA)
    metadata_dict["data_type"] = "SCENE"
    metadata_dict["data_hash"] = event_based_scene.DATA_HASH
    metadata_dict["number_of_frames"] = 0
    metadata_dict["frames_per_second"] = None
    metadata_dict["duration"] = None
    label_row = LabelRowV2(LabelRowMetadata(**metadata_dict), Mock(), all_types_ontology)
    with pytest.raises(LabelRowError, match="does not support"):
        label_row.from_labels_dict(_labels_with_interpolate(mode))


def test_interpolate_refusal_does_not_depend_on_the_row_being_event_based(all_types_ontology):
    """`interpolate` is read off the stored entry, so a dense row must refuse it just the same."""
    with pytest.raises(LabelRowError, match="does not support"):
        _scene_label_row(all_types_ontology, _labels_with_interpolate("linear"))
