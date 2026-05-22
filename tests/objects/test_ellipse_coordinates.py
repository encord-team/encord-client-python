"""Ellipse coordinates — same wire shape as Circle.

Ellipse reuses ``CircleCoordinates``. These tests verify the enum entry, the
ontology registry mapping, and the round-trip serialisation under an
``ELLIPSE``-shaped ontology object.
"""

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

ELLIPSE_ONTOLOGY_ITEM: Object = all_types_structure.get_child_by_hash("ellipseFeatureNodeHash", Object)


def test_ellipse_enum_value() -> None:
    assert Shape.ELLIPSE.value == "ellipse"


def test_ellipse_in_acceptable_coordinates_registry() -> None:
    """Ellipse must accept CircleCoordinates — same wire payload as Circle."""
    assert Shape.ELLIPSE in ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS
    assert CircleCoordinates in ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS[Shape.ELLIPSE]


def _make_label_row(all_types_ontology) -> LabelRowV2:
    label_row = LabelRowV2(BASE_LABEL_ROW_METADATA, Mock(), all_types_ontology)
    label_row.from_labels_dict(empty_image_group_labels)
    return label_row


def test_add_ellipse_instance_to_label_row(all_types_ontology) -> None:
    label_row = _make_label_row(all_types_ontology)

    # Stretch and theta are the whole point of Ellipse — exercise both.
    coords = CircleCoordinates(center_x=0.5, center_y=0.5, radius=0.2, stretch=0.5, theta=30.0)
    instance = ObjectInstance(ELLIPSE_ONTOLOGY_ITEM)
    instance.set_for_frames(coordinates=coords, frames=1)
    label_row.add_object_instance(instance)

    objects = label_row.get_object_instances()
    assert len(objects) == 1
    assert objects[0].ontology_item.shape == Shape.ELLIPSE
    validate_label_row_serialisation(label_row)


def test_ellipse_coordinates_survive_serialisation_roundtrip(all_types_ontology) -> None:
    label_row = _make_label_row(all_types_ontology)

    coords = CircleCoordinates(center_x=0.25, center_y=0.75, radius=0.08, stretch=0.7, theta=15.0)
    instance = ObjectInstance(ELLIPSE_ONTOLOGY_ITEM)
    instance.set_for_frames(coordinates=coords, frames=0)
    label_row.add_object_instance(instance)

    validate_label_row_serialisation(label_row)

    recovered = label_row.get_object_instances()[0].get_annotation(frame=0)
    assert recovered is not None
    assert recovered.coordinates == coords


def test_ellipse_wire_format_tags_shape_as_ellipse(all_types_ontology) -> None:
    """The exported label dict must carry shape="ellipse" — not "circle" —
    even though the geometry payload still lives under the "circle" key.
    """
    label_row = _make_label_row(all_types_ontology)

    coords = CircleCoordinates(center_x=0.5, center_y=0.5, radius=0.1, stretch=0.5, theta=45.0)
    instance = ObjectInstance(ELLIPSE_ONTOLOGY_ITEM)
    instance.set_for_frames(coordinates=coords, frames=0)
    label_row.add_object_instance(instance)

    blob = label_row.to_encord_dict()
    assert blob is not None

    # The blob nests "objects" deep under data_units → labels → frame keys.
    # Walk the whole tree generically so the test isn't tied to the exact
    # shape (it's evolved across SDK versions).
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
        # Geometry still under "circle" key — that's Ellipse's storage choice.
        assert obj.get("circle") == coords.to_dict()


def test_wrong_coordinate_type_rejected_for_ellipse(all_types_ontology) -> None:
    instance = ObjectInstance(ELLIPSE_ONTOLOGY_ITEM)
    box_coords = BoundingBoxCoordinates(height=0.1, width=0.1, top_left_x=0.0, top_left_y=0.0)
    with pytest.raises(LabelRowError):
        instance.set_for_frames(coordinates=box_coords, frames=0)
