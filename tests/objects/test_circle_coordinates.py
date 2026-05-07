from unittest.mock import Mock

import pytest

from encord.exceptions import LabelRowError
from encord.objects import LabelRowV2, Object, ObjectInstance
from encord.objects.common import Shape
from encord.objects.coordinates import (
    ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS,
    BoundingBoxCoordinates,
    CircleCoordinates,
)
from tests.objects.common import BASE_LABEL_ROW_METADATA
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.empty_image_group import empty_image_group_labels
from tests.objects.objects_test_utils import validate_label_row_serialisation

CIRCLE_ONTOLOGY_ITEM: Object = all_types_structure.get_child_by_hash("circleFeatureNodeHash", Object)
BOX_ONTOLOGY_ITEM: Object = all_types_structure.get_child_by_hash("MjI2NzEy", Object)


# ---------------------------------------------------------------------------
# CircleCoordinates — unit tests
# ---------------------------------------------------------------------------


def test_circle_coordinates_basic() -> None:
    circle = CircleCoordinates(center_x=0.5, center_y=0.4, radius=0.1)
    assert circle.center_x == 0.5
    assert circle.center_y == 0.4
    assert circle.radius == 0.1


def test_circle_coordinates_frozen() -> None:
    circle = CircleCoordinates(center_x=0.5, center_y=0.5, radius=0.1)
    with pytest.raises(Exception):
        # Frozen-dataclass mutation is intentional here; setattr sidesteps the
        # type checker without an inline ignore.
        setattr(circle, "center_x", 0.9)


def test_circle_coordinates_to_dict() -> None:
    circle = CircleCoordinates(center_x=0.25, center_y=0.75, radius=0.15)
    result = circle.to_dict()
    assert result == {"x": 0.25, "y": 0.75, "r": 0.15, "stretch": 1.0, "theta": 0.0}


def test_circle_coordinates_from_dict() -> None:
    d = {"circle": {"x": 0.3, "y": 0.6, "r": 0.08}}
    circle = CircleCoordinates.from_dict(d)
    assert circle.center_x == 0.3
    assert circle.center_y == 0.6
    assert circle.radius == 0.08


def test_circle_coordinates_roundtrip() -> None:
    original = CircleCoordinates(center_x=0.33, center_y=0.67, radius=0.12)
    reconstructed = CircleCoordinates.from_dict({"circle": original.to_dict()})
    assert reconstructed == original


def test_circle_coordinates_boundary_values() -> None:
    # Center at origin, zero radius
    zero = CircleCoordinates(center_x=0.0, center_y=0.0, radius=0.0)
    assert (zero.center_x, zero.center_y, zero.radius) == (0.0, 0.0, 0.0)

    # Center at far corner, large radius (out-of-bounds usage)
    oob = CircleCoordinates(center_x=1.0, center_y=1.0, radius=1.5)
    assert (oob.center_x, oob.center_y, oob.radius) == (1.0, 1.0, 1.5)


def test_circle_in_acceptable_coordinates_registry() -> None:
    assert Shape.CIRCLE in ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS
    assert CircleCoordinates in ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS[Shape.CIRCLE]


def test_circle_coordinates_custom_stretch_and_theta() -> None:
    c = CircleCoordinates(center_x=0.5, center_y=0.5, radius=0.1, stretch=1.5, theta=45.0)
    assert c.stretch == 1.5
    assert c.theta == 45.0


def test_circle_coordinates_from_dict_reads_stretch_and_theta() -> None:
    d = {"circle": {"x": 0.3, "y": 0.6, "r": 0.08, "stretch": 2.0, "theta": 30.0}}
    c = CircleCoordinates.from_dict(d)
    assert c.stretch == 2.0
    assert c.theta == 30.0


def test_circle_coordinates_from_dict_defaults_when_absent() -> None:
    # Older payloads omit stretch/theta — must not raise and must use defaults.
    d = {"circle": {"x": 0.3, "y": 0.6, "r": 0.08}}
    c = CircleCoordinates.from_dict(d)
    assert c.stretch == 1.0
    assert c.theta == 0.0


def test_circle_coordinates_roundtrip_with_stretch_and_theta() -> None:
    original = CircleCoordinates(center_x=0.33, center_y=0.67, radius=0.12, stretch=0.8, theta=15.0)
    reconstructed = CircleCoordinates.from_dict({"circle": original.to_dict()})
    assert reconstructed == original


# ---------------------------------------------------------------------------
# ObjectInstance — integration tests with LabelRowV2
# ---------------------------------------------------------------------------


def _make_label_row(all_types_ontology) -> LabelRowV2:
    label_row = LabelRowV2(BASE_LABEL_ROW_METADATA, Mock(), all_types_ontology)
    label_row.from_labels_dict(empty_image_group_labels)
    return label_row


def test_add_circle_instance_to_label_row(all_types_ontology) -> None:
    label_row = _make_label_row(all_types_ontology)

    instance = ObjectInstance(CIRCLE_ONTOLOGY_ITEM)
    coords = CircleCoordinates(center_x=0.5, center_y=0.5, radius=0.1)
    instance.set_for_frames(coordinates=coords, frames=1)
    label_row.add_object_instance(instance)

    objects = label_row.get_object_instances()
    assert len(objects) == 1
    assert objects[0].object_hash == instance.object_hash
    validate_label_row_serialisation(label_row)


def test_circle_coordinates_survive_serialisation_roundtrip(all_types_ontology) -> None:
    label_row = _make_label_row(all_types_ontology)

    coords = CircleCoordinates(center_x=0.25, center_y=0.75, radius=0.08)
    instance = ObjectInstance(CIRCLE_ONTOLOGY_ITEM)
    instance.set_for_frames(coordinates=coords, frames=0)
    label_row.add_object_instance(instance)

    # Serialise → deserialise → check coordinates are preserved
    validate_label_row_serialisation(label_row)

    recovered = label_row.get_object_instances()[0].get_annotation(frame=0)
    assert recovered is not None
    assert recovered.coordinates == coords


def test_add_multiple_circle_instances(all_types_ontology) -> None:
    label_row = _make_label_row(all_types_ontology)

    coords_a = CircleCoordinates(center_x=0.2, center_y=0.2, radius=0.05)
    coords_b = CircleCoordinates(center_x=0.8, center_y=0.8, radius=0.10)

    instance_a = ObjectInstance(CIRCLE_ONTOLOGY_ITEM)
    instance_b = ObjectInstance(CIRCLE_ONTOLOGY_ITEM)
    instance_a.set_for_frames(coordinates=coords_a, frames=0)
    instance_b.set_for_frames(coordinates=coords_b, frames=0)

    label_row.add_object_instance(instance_a)
    label_row.add_object_instance(instance_b)

    objects = label_row.get_object_instances()
    assert len(objects) == 2
    validate_label_row_serialisation(label_row)


def test_update_circle_coordinates(all_types_ontology) -> None:
    label_row = _make_label_row(all_types_ontology)

    original = CircleCoordinates(center_x=0.3, center_y=0.3, radius=0.1)
    instance = ObjectInstance(CIRCLE_ONTOLOGY_ITEM)
    instance.set_for_frames(coordinates=original, frames=0)
    label_row.add_object_instance(instance)

    updated = CircleCoordinates(center_x=0.6, center_y=0.6, radius=0.2)
    instance.set_for_frames(coordinates=updated, frames=0, overwrite=True)

    recovered = label_row.get_object_instances()[0].get_annotation(frame=0)
    assert recovered is not None
    assert recovered.coordinates == updated
    validate_label_row_serialisation(label_row)


def test_remove_circle_instance(all_types_ontology) -> None:
    label_row = _make_label_row(all_types_ontology)

    instance_a = ObjectInstance(CIRCLE_ONTOLOGY_ITEM)
    instance_b = ObjectInstance(CIRCLE_ONTOLOGY_ITEM)
    instance_a.set_for_frames(coordinates=CircleCoordinates(center_x=0.1, center_y=0.1, radius=0.05), frames=0)
    instance_b.set_for_frames(coordinates=CircleCoordinates(center_x=0.9, center_y=0.9, radius=0.05), frames=0)

    label_row.add_object_instance(instance_a)
    label_row.add_object_instance(instance_b)
    assert len(label_row.get_object_instances()) == 2

    label_row.remove_object(instance_a)
    remaining = label_row.get_object_instances()
    assert len(remaining) == 1
    assert remaining[0].object_hash == instance_b.object_hash
    validate_label_row_serialisation(label_row)


def test_circle_across_multiple_frames(all_types_ontology) -> None:
    label_row = _make_label_row(all_types_ontology)

    instance = ObjectInstance(CIRCLE_ONTOLOGY_ITEM)
    coords_f0 = CircleCoordinates(center_x=0.1, center_y=0.1, radius=0.05)
    coords_f1 = CircleCoordinates(center_x=0.5, center_y=0.5, radius=0.10)
    coords_f2 = CircleCoordinates(center_x=0.9, center_y=0.9, radius=0.15)

    instance.set_for_frames(coordinates=coords_f0, frames=0)
    instance.set_for_frames(coordinates=coords_f1, frames=1)
    instance.set_for_frames(coordinates=coords_f2, frames=2)
    label_row.add_object_instance(instance)

    assert instance.get_annotation(frame=0).coordinates == coords_f0
    assert instance.get_annotation(frame=1).coordinates == coords_f1
    assert instance.get_annotation(frame=2).coordinates == coords_f2
    validate_label_row_serialisation(label_row)


def test_wrong_coordinate_type_rejected(all_types_ontology) -> None:
    instance = ObjectInstance(CIRCLE_ONTOLOGY_ITEM)
    box_coords = BoundingBoxCoordinates(height=0.1, width=0.1, top_left_x=0.0, top_left_y=0.0)
    with pytest.raises(LabelRowError):
        instance.set_for_frames(coordinates=box_coords, frames=0)
