"""Ellipse coordinates — independent {x, y, rx, ry, theta} representation.

Mirrors RotatableBoundingBox: rx normalised to image width, ry to height,
theta as a rotation in screen-pixel space.
"""

from unittest.mock import Mock

import pytest

from encord.exceptions import LabelRowError
from encord.objects import LabelRowV2, Object, ObjectInstance
from encord.objects.common import Shape
from encord.objects.coordinates import (
    ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS,
    BoundingBoxCoordinates,
    EllipseCoordinates,
)
from tests.objects.common import BASE_LABEL_ROW_METADATA
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.empty_image_group import empty_image_group_labels
from tests.objects.objects_test_utils import validate_label_row_serialisation

ELLIPSE_ONTOLOGY_ITEM: Object = all_types_structure.get_child_by_hash("ellipseFeatureNodeHash", Object)


def test_ellipse_enum_value() -> None:
    assert Shape.ELLIPSE.value == "ellipse"


def test_ellipse_in_acceptable_coordinates_registry() -> None:
    """Ellipse uses its own EllipseCoordinates class."""
    assert Shape.ELLIPSE in ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS
    assert EllipseCoordinates in ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS[Shape.ELLIPSE]


def _make_label_row(all_types_ontology) -> LabelRowV2:
    label_row = LabelRowV2(BASE_LABEL_ROW_METADATA, Mock(), all_types_ontology)
    label_row.from_labels_dict(empty_image_group_labels)
    return label_row


def test_add_ellipse_instance_to_label_row(all_types_ontology) -> None:
    label_row = _make_label_row(all_types_ontology)

    coords = EllipseCoordinates(center_x=0.5, center_y=0.5, rx=0.2, ry=0.1, theta=30.0)
    instance = ObjectInstance(ELLIPSE_ONTOLOGY_ITEM)
    instance.set_for_frames(coordinates=coords, frames=1)
    label_row.add_object_instance(instance)

    objects = label_row.get_object_instances()
    assert len(objects) == 1
    assert objects[0].ontology_item.shape == Shape.ELLIPSE
    validate_label_row_serialisation(label_row)


def test_ellipse_coordinates_survive_serialisation_roundtrip(all_types_ontology) -> None:
    label_row = _make_label_row(all_types_ontology)

    coords = EllipseCoordinates(center_x=0.25, center_y=0.75, rx=0.08, ry=0.05, theta=15.0)
    instance = ObjectInstance(ELLIPSE_ONTOLOGY_ITEM)
    instance.set_for_frames(coordinates=coords, frames=0)
    label_row.add_object_instance(instance)

    validate_label_row_serialisation(label_row)

    recovered = label_row.get_object_instances()[0].get_annotation(frame=0)
    assert recovered is not None
    assert recovered.coordinates == coords


def test_ellipse_wire_format_uses_ellipse_field(all_types_ontology) -> None:
    """The exported label dict must carry shape="ellipse" with geometry
    under its own `ellipse` field (rx, ry, theta) — not `circle`.
    """
    label_row = _make_label_row(all_types_ontology)

    coords = EllipseCoordinates(center_x=0.5, center_y=0.5, rx=0.1, ry=0.05, theta=45.0)
    instance = ObjectInstance(ELLIPSE_ONTOLOGY_ITEM)
    instance.set_for_frames(coordinates=coords, frames=0)
    label_row.add_object_instance(instance)

    blob = label_row.to_encord_dict()
    assert blob is not None

    # Walk the data_units → labels → frame keys → objects tree generically.
    ellipse_objects: list[dict] = []

    def _walk(node):
        if isinstance(node, dict):
            if node.get("objectHash") == instance.object_hash and "shape" in node:
                ellipse_objects.append(node)
            for v in node.values():
                _walk(v)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(blob)

    assert len(ellipse_objects) >= 1, f"Expected at least one ellipse object; got {ellipse_objects}"
    for obj in ellipse_objects:
        assert obj["shape"] == "ellipse"
        assert obj.get("ellipse") == coords.to_dict()
        # No leakage onto the `circle` wire field.
        assert obj.get("circle") is None


def test_wrong_coordinate_type_rejected_for_ellipse(all_types_ontology) -> None:
    instance = ObjectInstance(ELLIPSE_ONTOLOGY_ITEM)
    box_coords = BoundingBoxCoordinates(height=0.1, width=0.1, top_left_x=0.0, top_left_y=0.0)
    with pytest.raises(LabelRowError):
        instance.set_for_frames(coordinates=box_coords, frames=0)


def test_ellipse_coordinates_roundtrip_through_dict() -> None:
    """Direct from_dict/to_dict roundtrip preserves all fields exactly."""
    original = EllipseCoordinates(center_x=0.4, center_y=0.6, rx=0.12, ry=0.07, theta=-22.5)
    reconstructed = EllipseCoordinates.from_dict({"ellipse": original.to_dict()})
    assert reconstructed == original
