from copy import deepcopy
from dataclasses import asdict
from typing import List
from unittest.mock import Mock

import pytest

from encord.exceptions import LabelRowError
from encord.objects import LabelRowV2, ObjectInstance, Shape
from encord.objects.coordinates import BoundingBoxCoordinates, CuboidCoordinates, PointCoordinate
from encord.objects.events import LabelUpsertEvent
from encord.objects.interpolation import (
    INTERPOLATED_CONFIDENCE,
    INTERPOLATION_SHAPES,
    _slerp_orientation,
    check_interpolation_supported,
)
from encord.orm.label_row import LabelRowMetadata
from tests.objects.common import BASE_LABEL_ROW_METADATA
from tests.objects.data import event_based_scene as scene
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.event_based_scene import EVENT_BASED_SCENE_LABELS

A = CuboidCoordinates(position=(0.2, 0.2, 0.2), orientation=(0.0, 0.0, 0.0), size=(0.1, 0.1, 0.1))
B = CuboidCoordinates(position=(0.3, 0.3, 0.3), orientation=(0.1, 0.2, 0.3), size=(0.2, 0.2, 0.2))
C = CuboidCoordinates(position=(0.4, 0.4, 0.4), orientation=(0.2, 0.3, 0.4), size=(0.3, 0.3, 0.3))
KEYPOINT = next(o for o in all_types_structure.objects if o.shape == Shape.POINT)

# three.js 0.183.2 `Quaternion.slerpQuaternions` between `Euler(..., "XYZ")`s, read back as an XYZ `Euler`.
THREE_JS_SLERP = [
    ((0.1, 0.2, 0.3), (0.2, 0.3, 0.4), 0.5, (0.15097194098593214, 0.24878862513196232, 0.3509719409859321)),
    ((0.0, 0.0, 0.0), (0.1, 0.2, 0.3), 0.25, (0.030451958974302643, 0.04704724822872714, 0.0764907211226212)),
    ((3.0, -1.2, 2.5), (-2.9, 1.3, -2.6), 0.4, (-2.6898303075799057, -0.23887928618343418, -3.120388903282482)),
    ((0.1, 1.5707, 0.2), (0.3, -1.2, 0.1), 0.7, (0.26367148028688, -0.3689896326627572, 0.0636786501910532)),
    ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0001), 0.3, (0.0, 0.0, 0.000029999999996500003)),
]


def _row(ontology, labels=None) -> LabelRowV2:
    metadata = asdict(BASE_LABEL_ROW_METADATA)
    metadata.update(data_type="SCENE", data_hash=scene.DATA_HASH, number_of_frames=0, frames_per_second=None)
    metadata["duration"] = None
    row = LabelRowV2(LabelRowMetadata(**metadata), Mock(), ontology)
    row.from_labels_dict(deepcopy(EVENT_BASED_SCENE_LABELS) if labels is None else labels)
    return row


def _labels(**modes: str) -> dict:
    """The fixture scene with `interpolate` set on the named keyframes, e.g. `UPSERT_0="linear"`."""
    labels = deepcopy(EVENT_BASED_SCENE_LABELS)
    unit = labels["data_units"][scene.DATA_HASH]["labels"]
    for name, mode in modes.items():
        unit[str(getattr(scene, name))]["objects"][0]["interpolate"] = mode
    return labels


def _object(row) -> ObjectInstance:
    [obj] = row.get_object_instances()
    return obj


def _view(obj: ObjectInstance, frame: int) -> ObjectInstance.ResolvedAnnotation:
    view = obj.get_annotation(frame)
    assert isinstance(view, ObjectInstance.ResolvedAnnotation)
    return view


def _upserts(obj: ObjectInstance) -> List[LabelUpsertEvent]:
    return [event for event in obj.get_events() if isinstance(event, LabelUpsertEvent)]


def _exported(row) -> dict:
    labels = row.to_encord_dict()["data_units"][scene.DATA_HASH]["labels"]
    return {int(frame): entry["objects"][0] for frame, entry in labels.items()}


def _approx(cuboid: CuboidCoordinates, position, orientation, size) -> None:
    assert cuboid.position == pytest.approx(position)
    assert cuboid.orientation == pytest.approx(orientation, abs=1e-12)
    assert cuboid.size == pytest.approx(size)


# ---- Reading


def test_linear_keyframe_runs_into_the_next_upsert(all_types_ontology):
    obj = _object(_row(all_types_ontology, _labels(UPSERT_0="linear")))
    view = _view(obj, scene.UPSERT_1 // 2)

    assert _upserts(obj)[0].interpolation == "linear"
    assert view.is_interpolated and view.is_virtual and view.keyframe == scene.UPSERT_0
    assert view.interpolation == "linear"
    assert view.confidence == INTERPOLATED_CONFIDENCE
    _approx(view.coordinates, (0.25,) * 3, _slerp_orientation(A.orientation, B.orientation, 0.5), (0.15,) * 3)


@pytest.mark.parametrize("frame", [scene.UPSERT_0, scene.UPSERT_1])
def test_the_ends_of_a_stretch_are_the_stored_keyframes(all_types_ontology, frame):
    view = _view(_object(_row(all_types_ontology, _labels(UPSERT_0="linear"))), frame)
    assert not view.is_interpolated
    assert view.coordinates == (A if frame == scene.UPSERT_0 else B)
    assert view.confidence == 1


def test_an_upsert_before_a_delete_holds(all_types_ontology):
    # UPSERT_1 -> DELETE_2 -> UPSERT_3: the next event is a delete, so it holds until it, then absent.
    obj = _object(_row(all_types_ontology, _labels(UPSERT_1="linear")))
    view = _view(obj, (scene.UPSERT_1 + scene.DELETE_2) // 2)

    assert view.interpolation == "linear"
    assert not view.is_interpolated and view.coordinates == B
    with pytest.raises(LabelRowError, match="does not exist"):
        _view(obj, scene.DELETE_2 + 1)


def test_a_delete_written_into_a_stretch_stops_it(all_types_ontology):
    # UPSERT_0 -> UPSERT_1 interpolates; a delete between them makes UPSERT_0 hold up to it.
    obj = _object(_row(all_types_ontology, _labels(UPSERT_0="linear")))
    assert _view(obj, scene.UPSERT_1 // 4).is_interpolated

    obj.delete_event(scene.UPSERT_1 // 2)
    view = _view(obj, scene.UPSERT_1 // 4)
    assert not view.is_interpolated and view.coordinates == A
    assert _upserts(obj)[0].interpolation == "hold"


def test_the_last_upsert_holds(all_types_ontology):
    view = _view(_object(_row(all_types_ontology, _labels(UPSERT_3="linear"))), scene.UPSERT_3 + 1)
    assert not view.is_interpolated and view.coordinates == C


def test_hold_reads_the_keyframe(all_types_ontology):
    view = _view(_object(_row(all_types_ontology)), scene.UPSERT_1 // 2)
    assert not view.is_interpolated and view.interpolation == "hold" and view.coordinates == A


@pytest.mark.parametrize("start, end, fraction, expected", THREE_JS_SLERP)
def test_orientation_matches_three_js(start, end, fraction, expected):
    assert _slerp_orientation(start, end, fraction) == pytest.approx(expected, abs=1e-12)


def test_linear_round_trips(all_types_ontology):
    exported = _exported(_row(all_types_ontology, _labels(UPSERT_0="linear")))
    assert exported[scene.UPSERT_0]["interpolate"] == "linear"
    assert "interpolate" not in exported[scene.UPSERT_1]


# ---- Writing


def _empty_row(ontology):
    labels = deepcopy(EVENT_BASED_SCENE_LABELS)
    labels["data_units"][scene.DATA_HASH]["labels"] = {}
    labels["object_answers"] = {}
    return _row(ontology, labels)


def test_authoring_a_linear_stretch(all_types_ontology):
    row = _empty_row(all_types_ontology)
    obj = ObjectInstance(all_types_ontology.structure.get_child_by_hash(scene.CUBOID_HASH))
    row.add_object_instance(obj)
    obj.upsert_event(A, 0, interpolation="linear")
    obj.upsert_event(B, 10)
    obj.delete_event(20)

    assert _view(obj, 5).is_interpolated
    reloaded = _object(_row(all_types_ontology, row.to_encord_dict()))
    assert _view(reloaded, 5).coordinates == _view(obj, 5).coordinates


def test_point_interpolates(all_types_ontology):
    row = _empty_row(all_types_ontology)
    obj = ObjectInstance(KEYPOINT)
    row.add_object_instance(obj)
    obj.upsert_event(PointCoordinate(x=0.0, y=0.2), 0, interpolation="linear")
    obj.upsert_event(PointCoordinate(x=1.0, y=0.4), 10)
    obj.delete_event(20)

    assert _view(obj, 5).coordinates == PointCoordinate(x=0.5, y=0.30000000000000004)


def test_a_keyframe_written_into_a_stretch_inherits_it(all_types_ontology):
    obj = _object(_row(all_types_ontology, _labels(UPSERT_0="linear")))
    obj.upsert_event(C, scene.UPSERT_1 // 2)
    assert _view(obj, scene.UPSERT_1 // 2).interpolation == "linear"


def test_explicit_hold_overrides_inheritance(all_types_ontology):
    obj = _object(_row(all_types_ontology, _labels(UPSERT_0="linear")))
    obj.upsert_event(C, scene.UPSERT_1 // 2, interpolation="hold")
    assert _view(obj, scene.UPSERT_1 // 2).interpolation == "hold"
    assert "interpolate" not in _exported(obj._parent)[scene.UPSERT_1 // 2]


def test_overwrite_keeps_the_mode(all_types_ontology):
    obj = _object(_row(all_types_ontology, _labels(UPSERT_0="linear")))
    obj.upsert_event(C, scene.UPSERT_0, overwrite=True)
    assert _upserts(obj)[0].interpolation == "linear"


def test_a_write_over_a_delete_holds(all_types_ontology):
    obj = _object(_row(all_types_ontology, _labels(UPSERT_1="linear")))
    obj.upsert_event(C, scene.DELETE_2, overwrite=True)
    assert _view(obj, scene.DELETE_2).interpolation == "hold"


def test_removing_the_target_clears_the_last_upserts_mode(all_types_ontology):
    obj = _object(_row(all_types_ontology, _labels(UPSERT_1="linear")))
    obj.remove_event(scene.UPSERT_3)
    assert _upserts(obj)[1].interpolation == "hold"

    # It would otherwise run into a keyframe written later.
    obj.upsert_event(C, scene.UPSERT_3)
    assert not _view(obj, scene.UPSERT_1 + 1).is_interpolated


def test_a_delete_marker_never_interpolates(all_types_ontology):
    obj = _object(_row(all_types_ontology, _labels(UPSERT_1="linear")))
    obj.delete_event(scene.UPSERT_1)
    assert "interpolate" not in _exported(obj._parent)[scene.UPSERT_1]


@pytest.mark.parametrize("mode", ["cubic", "HOLD", ""])
def test_an_unknown_mode_is_refused_on_write(all_types_ontology, mode):
    with pytest.raises(LabelRowError, match="Unsupported interpolation mode"):
        _object(_row(all_types_ontology)).upsert_event(C, scene.UPSERT_3 + 1, interpolation=mode)  # type: ignore[arg-type]


def test_linear_on_an_unsupported_shape_is_refused_on_write(all_types_ontology):
    row = _empty_row(all_types_ontology)
    box = ObjectInstance(next(o for o in all_types_structure.objects if o.shape == Shape.BOUNDING_BOX))
    row.add_object_instance(box)
    with pytest.raises(LabelRowError, match="not supported for shape `bounding_box`"):
        box.upsert_event(
            BoundingBoxCoordinates(height=0.1, width=0.1, top_left_x=0, top_left_y=0), 0, interpolation="linear"
        )


# ---- Registry


def test_registry_lists_the_shapes_per_mode():
    assert INTERPOLATION_SHAPES == {"linear": frozenset({Shape.POINT, Shape.CUBOID})}


@pytest.mark.parametrize("shape", [Shape.POINT, Shape.CUBOID, "point", "cuboid"])
def test_linear_is_supported_for(shape):
    check_interpolation_supported("linear", shape)


@pytest.mark.parametrize("shape", list(Shape))
def test_hold_is_supported_for_every_shape(shape):
    check_interpolation_supported("hold", shape)
