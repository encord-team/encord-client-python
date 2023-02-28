import datetime
from dataclasses import asdict
from unittest.mock import Mock

import pytest

from encord.exceptions import LabelRowError, OntologyError
from encord.objects import (
    AnswerForFrames,
    Classification,
    ClassificationInstance,
    LabelRowV2,
    Object,
    ObjectInstance,
)
from encord.objects.common import (
    Attribute,
    ChecklistAttribute,
    Option,
    RadioAttribute,
    TextAttribute,
)
from encord.objects.constants import DEFAULT_CONFIDENCE, DEFAULT_MANUAL_ANNOTATION
from encord.objects.coordinates import (
    BoundingBoxCoordinates,
    PointCoordinate,
    PolygonCoordinates,
)
from encord.objects.utils import Range
from encord.orm.label_row import LabelRowMetadata, LabelStatus
from tests.objects.common import FAKE_LABEL_ROW_METADATA
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.empty_image_group import empty_image_group_labels

box_ontology_item = all_types_structure.get_item_by_hash("MjI2NzEy", Object)
polygon_ontology_item = all_types_structure.get_item_by_hash("ODkxMzAx", Object)
polyline_ontology_item = all_types_structure.get_item_by_hash("OTcxMzIy", Object)

nested_box_ontology_item = all_types_structure.get_item_by_hash("MTA2MjAx")
text_attribute_1 = all_types_structure.get_item_by_hash("OTkxMjU1")
checklist_attribute_1 = all_types_structure.get_item_by_hash("ODcxMDAy")
checklist_attribute_1_option_1 = all_types_structure.get_item_by_hash("MTE5MjQ3")
checklist_attribute_1_option_2 = all_types_structure.get_item_by_hash("Nzg3MDE3")

deeply_nested_polygon_item = all_types_structure.get_item_by_hash("MTM1MTQy")
nested_polygon_text = all_types_structure.get_item_by_hash("OTk555U1")
nested_polygon_checklist = all_types_structure.get_item_by_hash("ODc555Ay")
nested_polygon_checklist_option_1 = all_types_structure.get_item_by_hash("MT5555Q3")
nested_polygon_checklist_option_2 = all_types_structure.get_item_by_hash("Nzg5555E3")
radio_attribute_level_1 = all_types_structure.get_item_by_hash("MTExMjI3")
radio_nested_option_1 = all_types_structure.get_item_by_hash("MTExNDQ5")
radio_nested_option_1_text = all_types_structure.get_item_by_hash("MjE2OTE0")
radio_nested_option_2 = all_types_structure.get_item_by_hash("MTcxMjAy")
radio_nested_option_2_checklist = all_types_structure.get_item_by_hash("ODc666Ay")
radio_nested_option_2_checklist_option_1 = all_types_structure.get_item_by_hash("MT66665Q3")
radio_nested_option_2_checklist_option_2 = all_types_structure.get_item_by_hash("Nzg66665E3")

keypoint_dynamic = all_types_structure.get_item_by_hash("MTY2MTQx")
dynamic_text: TextAttribute = all_types_structure.get_item_by_hash("OTkxMjU1")
dynamic_checklist = all_types_structure.get_item_by_hash("ODcxMDAy")
dynamic_checklist_option_1 = all_types_structure.get_item_by_hash("MTE5MjQ3")
dynamic_checklist_option_2 = all_types_structure.get_item_by_hash("Nzg3MDE3")
dynamic_radio = all_types_structure.get_item_by_hash("MTExM9I3")
dynamic_radio_option_1 = all_types_structure.get_item_by_hash("MT9xNDQ5")  # This is dynamic and deeply nested.
dynamic_radio_option_2 = all_types_structure.get_item_by_hash("9TcxMjAy")  # This is dynamic and deeply nested.

text_classification = all_types_structure.get_item_by_hash("jPOcEsbw", Classification)
text_classification_attribute: TextAttribute = all_types_structure.get_item_by_hash("OxrtEM+v", TextAttribute)
radio_classification = all_types_structure.get_item_by_hash("NzIxNTU1")
radio_classification_option_1 = all_types_structure.get_item_by_hash("MTcwMjM5")
radio_classification_option_2 = all_types_structure.get_item_by_hash("MjUzMTg1")
radio_classification_option_2_text = all_types_structure.get_item_by_hash("MTg0MjIw")
checklist_classification = all_types_structure.get_item_by_hash("3DuQbFxo")
checklist_classification_option_1 = all_types_structure.get_item_by_hash("fvLjF0qZ")
checklist_classification_option_2 = all_types_structure.get_item_by_hash("a4r7nK9i")

BOX_COORDINATES = BoundingBoxCoordinates(
    height=0.1,
    width=0.2,
    top_left_x=0.3,
    top_left_y=0.4,
)

POLYGON_COORDINATES = PolygonCoordinates(
    values=[
        PointCoordinate(x=0.2, y=0.1),
        PointCoordinate(x=0.3, y=0.2),
        PointCoordinate(x=0.5, y=0.3),
        PointCoordinate(x=0.6, y=0.5),
    ]
)

KEYPOINT_COORDINATES = PointCoordinate(x=0.2, y=0.1)


# =======================================================
# =========== demonstrative tests below here ============
# =======================================================


@pytest.mark.skip("The functionality is not fully implemented")
def test_upload_simple_data():
    project = "code that generates a project ..."
    label_hash = "1234"

    label_row = project.get_label_row_class(label_hash)  # can either take label_hash or data_hash

    # Now create an object and add it to the label row
    box_ontology_item = example_ontology_structure.get_item_by_hash("MjI2NzEy", Object)
    # ^ The `Object` argument is for properly typing the return value and doing an internal type check which can throw.

    object_instance = ObjectInstance(box_ontology_item)
    # ^ There is an ongoing discussion about making this box_ontology_item.create_instance() instead, which has
    # other tradeoffs.

    coordinates = BoundingBoxCoordinates(
        height=0.1,
        width=0.2,
        top_left_x=0.3,
        top_left_y=0.4,
    )
    object_instance.set_for_frames(coordinates=coordinates, frames=Range(1, 3))

    # ======== Setting static attributes ========
    text_attribute_of_box_ontology_item = example_ontology_structure.get_item_by_hash("OTkxMjU1", TextAttribute)
    object_instance.set_answer(answer="Poseidon", attribute=text_attribute_of_box_ontology_item)
    # ^ this is how we answer static attributes
    assert object_instance.get_answer(attribute=text_attribute_of_box_ontology_item) == "Poseidon"

    # Overwritting previous answers
    object_instance.set_answer(answer="Ulysses", attribute=text_attribute_of_box_ontology_item, overwrite=True)
    # ^ add overwrite=True to avoid throwing an error.
    assert object_instance.get_answer(attribute=text_attribute_of_box_ontology_item) == "Ulysses"

    # NOTE: Setting nested answers to attribute where a parent is not selected will throw an error.

    # ======== Setting dynamic attributes ========
    dynamic_text_attribute_of_box_item = example_ontology_structure.get_item_by_hash("OTkxMj222", TextAttribute)
    object_instance.set_answer(answer="Zeus", attribute=dynamic_text_attribute_of_box_item)
    # ^ this sets the answer for all the dynamic attributes that are currently available

    assert object_instance.get_answer(attribute=dynamic_text_attribute_of_box_item) == [
        AnswerForFrames(answer="Zeus", ranges=[Range(1, 3)]),
    ]

    object_instance.set_answer(answer="Hermes", attribute=dynamic_text_attribute_of_box_item, frames=1)
    assert object_instance.get_answer(attribute=dynamic_text_attribute_of_box_item) == [
        AnswerForFrames(answer="Hermes", ranges=[Range(1, 1)]),
        AnswerForFrames(answer="Zeus", ranges=[Range(2, 3)]),
    ]

    # ======== Add the object to the label row ========
    label_row.add_object_instance(object_instance)

    # ======= ClassificationIndex ========
    # This essentially works very similar to setting one static answer in the ObjectInstance.
    text_classification = example_ontology_structure.get_item_by_hash("jPOcEsbw", Classification)
    text_attribute = text_classification.attributes[0]

    classification_instance = ClassificationInstance(text_classification)
    classification_instance.set_answer("Zeus")  # You can explicitly set the `text_attribute`, but it is implicit.

    assert classification_instance.get_answer() == "Zeus"
    # ^ Again, the `text_attribute` is implicit here, but you can explicitly set it. If it was a nested attribute,
    # you would have to set the parent first and then you must specify the nested attribute.

    classification_instance.add_frames([2, 3])

    label_row.add_classification_instance(classification_instance)
    # ======== Radio classification ========
    # This will work similarly for the ObjectIndex
    radio_classification = example_ontology_structure.get_item_by_hash("jPOcEswer", Classification)
    radio_option_1 = radio_classification.attributes[0].options[0]

    radio_classification.set_answer(radio_option_1)
    assert radio_classification.get_answer() == radio_option_1

    # ======== Checklist classification ========
    # This will work similarly for the ObjectIndex
    checklist_classification = example_ontology_structure.get_item_by_hash("jPOcEswer", Classification)
    checklist_option_1 = checklist_classification.attributes[0].options[0]
    checklist_option_2 = checklist_classification.attributes[0].options[1]

    checklist_classification.set_answer({checklist_option_1, checklist_option_2})
    assert checklist_classification.get_answer() == {checklist_option_1, checklist_option_2}

    # ======== Upload to server ========
    label_row.save()


# =======================================================
# =========== demonstrative tests above here ============
# =======================================================


def test_create_object_instance_one_coordinate():
    object_instance = box_ontology_item.create_instance()

    coordinates = BoundingBoxCoordinates(
        height=0.1,
        width=0.2,
        top_left_x=0.3,
        top_left_y=0.4,
    )

    object_instance.set_for_frames(coordinates=coordinates, frames=1)
    object_instance.is_valid()


def test_create_a_label_row_from_empty_image_group_label_row_dict():
    label_row = LabelRowV2(FAKE_LABEL_ROW_METADATA, Mock())

    with pytest.raises(LabelRowError):
        label_row.get_classification_instances()

    label_row.from_labels_dict(empty_image_group_labels, all_types_structure)
    assert label_row.get_classification_instances() == []
    assert label_row.get_object_instances() == []
    # TODO: do more assertions


def test_add_object_instance_to_label_row():
    label_row = LabelRowV2(FAKE_LABEL_ROW_METADATA, Mock())
    label_row.from_labels_dict(empty_image_group_labels, all_types_structure)

    object_instance = ObjectInstance(box_ontology_item)

    coordinates = BoundingBoxCoordinates(
        height=0.1,
        width=0.2,
        top_left_x=0.3,
        top_left_y=0.4,
    )

    object_instance.set_for_frames(coordinates=coordinates, frames=1)
    label_row.add_object_instance(object_instance)
    assert label_row.get_object_instances()[0].object_hash == object_instance.object_hash


def test_add_remove_access_object_instances_in_label_row():
    label_row = LabelRowV2(FAKE_LABEL_ROW_METADATA, Mock())
    label_row.from_labels_dict(empty_image_group_labels, all_types_structure)

    object_instance_1 = ObjectInstance(box_ontology_item)
    object_instance_2 = ObjectInstance(box_ontology_item)

    coordinates_1 = BoundingBoxCoordinates(
        height=0.1,
        width=0.2,
        top_left_x=0.3,
        top_left_y=0.4,
    )
    coordinates_2 = BoundingBoxCoordinates(
        height=0.2,
        width=0.1,
        top_left_x=0.5,
        top_left_y=0.4,
    )

    object_instance_1.set_for_frames(coordinates=coordinates_1, frames=1)
    object_instance_2.set_for_frames(coordinates=coordinates_2, frames=2)
    object_instance_2.set_for_frames(coordinates=coordinates_2, frames=3)

    label_row.add_object_instance(object_instance_1)
    label_row.add_object_instance(object_instance_2)

    objects = label_row.get_object_instances()
    assert objects[0].object_hash == object_instance_1.object_hash
    assert objects[1].object_hash == object_instance_2.object_hash
    # The FE may sometimes rely on the order of these.

    label_row.remove_object(object_instance_1)
    objects = label_row.get_object_instances()
    assert len(objects) == 1
    assert objects[0].object_hash == object_instance_2.object_hash


def test_filter_for_objects():
    label_row = LabelRowV2(FAKE_LABEL_ROW_METADATA, Mock())
    label_row.from_labels_dict(empty_image_group_labels, all_types_structure)

    label_box = ObjectInstance(box_ontology_item)
    label_polygon = ObjectInstance(polygon_ontology_item)

    box_coordinates = BoundingBoxCoordinates(
        height=0.1,
        width=0.2,
        top_left_x=0.3,
        top_left_y=0.4,
    )
    polygon_coordinates = PolygonCoordinates(
        values=[
            PointCoordinate(x=0.2, y=0.1),
            PointCoordinate(x=0.3, y=0.2),
            PointCoordinate(x=0.5, y=0.3),
            PointCoordinate(x=0.6, y=0.5),
        ]
    )

    label_box.set_for_frames(box_coordinates, 1)
    label_box.set_for_frames(box_coordinates, 2)
    label_polygon.set_for_frames(polygon_coordinates, 2)
    label_polygon.set_for_frames(polygon_coordinates, 3)

    label_row.add_object_instance(label_box)
    label_row.add_object_instance(label_polygon)

    objects = label_row.get_object_instances()
    assert len(objects) == 2

    objects = label_row.get_object_instances(filter_ontology_object=polygon_ontology_item)
    assert len(objects) == 1
    assert objects[0].object_hash == label_polygon.object_hash

    objects = label_row.get_object_instances(filter_ontology_object=box_ontology_item)
    assert len(objects) == 1
    assert objects[0].object_hash == label_box.object_hash

    objects = label_row.get_object_instances(filter_ontology_object=polyline_ontology_item)
    assert len(objects) == 0


def test_add_wrong_coordinates():
    label_box = ObjectInstance(box_ontology_item)
    with pytest.raises(LabelRowError):
        label_box.set_for_frames(POLYGON_COORDINATES, frames=1)


def test_get_object_instances_by_frames():
    label_row = LabelRowV2(FAKE_LABEL_ROW_METADATA, Mock())
    label_row.from_labels_dict(empty_image_group_labels, all_types_structure)

    label_box = ObjectInstance(box_ontology_item)
    label_polygon = ObjectInstance(polygon_ontology_item)

    label_box.set_for_frames(BOX_COORDINATES, 1)
    label_box.set_for_frames(BOX_COORDINATES, 2)
    label_polygon.set_for_frames(POLYGON_COORDINATES, 2)
    label_polygon.set_for_frames(POLYGON_COORDINATES, 3)

    label_row.add_object_instance(label_box)
    label_row.add_object_instance(label_polygon)

    objects = label_row.get_object_instances(filter_frames=2)
    assert len(objects) == 2

    objects = label_row.get_object_instances(filter_frames=4)
    assert len(objects) == 0

    objects = list(label_row.get_object_instances(filter_frames=1))
    assert len(objects) == 1
    assert objects[0].object_hash == label_box.object_hash

    objects = list(label_row.get_object_instances(filter_frames=3))
    assert len(objects) == 1
    assert objects[0].object_hash == label_polygon.object_hash

    label_box.set_for_frames(BOX_COORDINATES, 3)
    objects = list(label_row.get_object_instances(filter_frames=3))
    assert len(objects) == 2

    label_row.remove_object(label_box)
    objects = list(label_row.get_object_instances(filter_frames=3))
    assert len(objects) == 1
    assert objects[0].object_hash == label_polygon.object_hash


def test_adding_object_instance_to_multiple_frames_fails():
    label_row_1 = LabelRowV2(FAKE_LABEL_ROW_METADATA, Mock())
    label_row_1.from_labels_dict(empty_image_group_labels, all_types_structure)

    label_row_2 = LabelRowV2(FAKE_LABEL_ROW_METADATA, Mock())
    label_row_2.from_labels_dict(empty_image_group_labels, all_types_structure)

    label_box = ObjectInstance(box_ontology_item)

    label_box.set_for_frames(BOX_COORDINATES, 1)

    label_row_1.add_object_instance(label_box)
    with pytest.raises(LabelRowError):
        label_row_2.add_object_instance(label_box)

    label_row_1.remove_object(label_box)
    label_row_2.add_object_instance(label_box)

    with pytest.raises(LabelRowError):
        label_row_1.add_object_instance(label_box)

    label_box_copy = label_box.copy()
    label_row_1.add_object_instance(label_box_copy)
    assert label_box.object_hash != label_box_copy.object_hash


def test_update_remove_object_instance_coordinates():
    label_box = ObjectInstance(box_ontology_item)

    # Add initial coordinates
    label_box.set_for_frames(BOX_COORDINATES, 1)
    frames = label_box.get_annotations()
    frame_1_view = label_box.get_annotation(1)
    assert sorted([frame.frame for frame in frames]) == [1]
    assert frame_1_view.coordinates == BOX_COORDINATES
    assert frame_1_view.confidence == DEFAULT_CONFIDENCE
    assert frame_1_view.manual_annotation == DEFAULT_MANUAL_ANNOTATION

    box_coordinates_2 = BoundingBoxCoordinates(
        height=0.1,
        width=0.3,
        top_left_x=0.4,
        top_left_y=0.5,
    )

    confidence = 0.5
    manual_annotation = False

    # Add new coordinates
    label_box.set_for_frames(box_coordinates_2, 2, confidence=confidence, manual_annotation=manual_annotation)
    label_box.set_for_frames(box_coordinates_2, 3, confidence=confidence, manual_annotation=manual_annotation)
    label_box.set_for_frames(box_coordinates_2, 4, confidence=confidence, manual_annotation=manual_annotation)
    frames = label_box.get_annotations()
    # instance_data = label_box.get_instance_data(frames)
    assert sorted([frame.frame for frame in frames]) == [1, 2, 3, 4]
    frame_1_view = label_box.get_annotation(1)
    assert frame_1_view.coordinates == BOX_COORDINATES
    assert frame_1_view.confidence == DEFAULT_CONFIDENCE
    assert frame_1_view.manual_annotation == DEFAULT_MANUAL_ANNOTATION

    frame_2_view = label_box.get_annotation(2)
    assert frame_2_view.coordinates == box_coordinates_2
    assert frame_2_view.confidence == confidence
    assert frame_2_view.manual_annotation == manual_annotation

    # Remove coordinates
    label_box.remove_from_frames(Range(2, 3))
    with pytest.raises(LabelRowError):
        frame_2_view.coordinates

    frames = label_box.get_annotations()
    assert sorted([frame.frame for frame in frames]) == [1, 4]
    frame_1_view = label_box.get_annotation(1)
    assert frame_1_view.coordinates == BOX_COORDINATES
    assert frame_1_view.confidence == DEFAULT_CONFIDENCE
    assert frame_1_view.manual_annotation == DEFAULT_MANUAL_ANNOTATION

    frame_4_view = label_box.get_annotation(4)
    assert frame_4_view.coordinates == box_coordinates_2
    assert frame_4_view.confidence == confidence
    assert frame_4_view.manual_annotation == manual_annotation

    # Reset coordinates
    box_coordinates_3 = BoundingBoxCoordinates(
        height=0.1,
        width=0.3,
        top_left_x=0.6,
        top_left_y=0.5,
    )
    new_confidence = 0.7

    with pytest.raises(LabelRowError):
        label_box.set_for_frames(box_coordinates_3, 4, confidence=new_confidence, manual_annotation=manual_annotation)

    label_box.set_for_frames(
        box_coordinates_3, 4, overwrite=True, confidence=new_confidence, manual_annotation=manual_annotation
    )
    label_box.set_for_frames(box_coordinates_3, 5, confidence=new_confidence, manual_annotation=manual_annotation)

    frames = label_box.get_annotations()
    assert sorted([frame.frame for frame in frames]) == [1, 4, 5]

    frame_1_view = label_box.get_annotation(1)
    assert frame_1_view.coordinates == BOX_COORDINATES
    assert frame_1_view.confidence == DEFAULT_CONFIDENCE
    assert frame_1_view.manual_annotation == DEFAULT_MANUAL_ANNOTATION

    frame_4_view = label_box.get_annotation(4)
    assert frame_4_view.coordinates == box_coordinates_3
    assert frame_4_view.confidence == new_confidence
    assert frame_4_view.manual_annotation == manual_annotation


def test_removing_coordinates_from_object_removes_it_from_parent():
    label_row = LabelRowV2(FAKE_LABEL_ROW_METADATA, Mock())
    label_row.from_labels_dict(empty_image_group_labels, all_types_structure)

    label_box = ObjectInstance(box_ontology_item)
    label_box.set_for_frames(BOX_COORDINATES, 1)
    label_box.set_for_frames(BOX_COORDINATES, 2)
    label_box.set_for_frames(BOX_COORDINATES, 3)

    label_row.add_object_instance(label_box)

    objects = label_row.get_object_instances(filter_frames=Range(1, 3))
    assert len(objects) == 1
    objects = label_row.get_object_instances(filter_frames=3)
    assert len(objects) == 1

    label_box.remove_from_frames(3)

    objects = label_row.get_object_instances(filter_frames=Range(1, 3))
    assert len(objects) == 1
    objects = label_row.get_object_instances(filter_frames=3)
    assert len(objects) == 0


def test_classification_index_answer_overwrite():
    classification_instance = text_classification.create_instance()
    attribute = text_classification.attributes[0]

    classification_instance.set_answer("Zeus", attribute)
    assert classification_instance.get_answer() == "Zeus"

    classification_instance.set_answer("Hermes", overwrite=True)  # inferred attribute
    assert classification_instance.get_answer() == "Hermes"

    with pytest.raises(LabelRowError):
        classification_instance.set_answer("Poseidon")
    assert classification_instance.get_answer() == "Hermes"

    classification_instance.set_answer("Aphrodite", overwrite=True)
    assert classification_instance.get_answer() == "Aphrodite"


def test_classification_answering_with_ontology_access():
    """A demonstrative test to show how easy it would be for clients to use the ontology to answer classifications"""

    # NOTE: it is important to add the `Classification` here, to distinguish between the attribute and classification,
    # which both go by the same name.
    radio_classification_ = all_types_structure.get_item_by_title("Radio classification 1", Classification)
    radio_instance = radio_classification_.create_instance()

    radio_classification_attribute_1: ChecklistAttribute = radio_classification_.get_item_by_title(
        "Radio classification 1", type_=RadioAttribute
    )
    # Different `type_` with generic `Attribute`
    radio_classification_attribute_2 = radio_classification_.get_item_by_title(
        "Radio classification 1", type_=Attribute
    )
    with pytest.raises(OntologyError):
        radio_classification_.get_item_by_title(
            # This is not the correct `type_`
            "Radio classification 1",
            type_=Option,
        )

    assert radio_classification_attribute_1 == radio_classification_attribute_2

    option_1 = radio_classification_.get_item_by_title("cl 1 option 1", type_=Option)
    option_2 = radio_classification_.get_item_by_title("cl 1 option 2", type_=Option)

    radio_instance.set_answer(option_1, attribute=radio_classification_attribute_2)
    assert radio_instance.get_answer() == option_1

    radio_instance.set_answer(option_2, overwrite=True)
    assert radio_instance.get_answer() == option_2


def test_classification_index_answer_nested_attributes():
    classification_instance = ClassificationInstance(radio_classification)
    attribute = radio_classification.attributes[0]

    # Setting nested attribute
    with pytest.raises(LabelRowError):
        classification_instance.set_answer(answer="Zeus", attribute=radio_classification_option_2_text)
    assert classification_instance.get_answer(attribute) is None

    # Setting non-nested answer
    classification_instance.set_answer(answer=radio_classification_option_2, attribute=attribute)  # inferred attribute
    assert classification_instance.get_answer(attribute) == radio_classification_option_2

    classification_instance.set_answer(answer=radio_classification_option_1, overwrite=True)
    assert classification_instance.get_answer(attribute) == radio_classification_option_1

    # Changing to the nested passed_attribute
    with pytest.raises(LabelRowError):
        classification_instance.set_answer(answer="Zeus", attribute=radio_classification_option_2_text)
    assert classification_instance.get_answer(attribute) == radio_classification_option_1

    classification_instance.set_answer(answer=radio_classification_option_2, overwrite=True)

    assert classification_instance.get_answer(radio_classification_option_2_text) is None

    classification_instance.set_answer(answer="Dionysus", attribute=radio_classification_option_2_text)

    assert classification_instance.get_answer(attribute=attribute) == radio_classification_option_2
    assert classification_instance.get_answer(radio_classification_option_2_text) == "Dionysus"

    # Changing back to the un-nested passed_attribute
    classification_instance.set_answer(answer=radio_classification_option_1, attribute=attribute, overwrite=True)

    assert classification_instance.get_answer(attribute) == radio_classification_option_1
    assert classification_instance.get_answer(radio_classification_option_2_text) is None

    # Change again to nested passed_attribute
    classification_instance.set_answer(answer=radio_classification_option_2, overwrite=True)

    assert classification_instance.get_answer(attribute=attribute) == radio_classification_option_2
    assert classification_instance.get_answer(radio_classification_option_2_text) == "Dionysus"
    # ^ this does not necessarily have to be like this, it could also reset from the switch.


def test_classification_instances():
    classification_instance_1 = ClassificationInstance(text_classification)
    classification_instance_2 = ClassificationInstance(text_classification)
    with pytest.raises(LabelRowError) as e:
        classification_instance_1.is_valid()
        assert "not on any frames" in str(e)

    classification_instance_1.set_for_frames(Range(1, 3))
    classification_instance_1.is_valid()

    classification_instance_1.set_answer("Dionysus")
    assert classification_instance_1.get_answer() == "Dionysus"

    classification_instance_2.set_answer(classification_instance_1.get_answer())
    assert classification_instance_2.get_answer() == "Dionysus"

    with pytest.raises(LabelRowError) as e:
        classification_instance_2.set_answer("Hades")
    assert classification_instance_2.get_answer() == "Dionysus"

    classification_instance_2.set_answer("Hades", overwrite=True)
    assert classification_instance_2.get_answer() == "Hades"
    assert classification_instance_1.get_answer() == "Dionysus"


def assert_datetime_is_recent(datetime_: datetime.datetime):
    now = datetime.datetime.now()
    assert datetime_ > now - datetime.timedelta(seconds=5)


def test_classification_instances_frame_view():
    classification_instance_1 = ClassificationInstance(text_classification)

    classification_instance_1.set_for_frames(Range(1, 3))

    # Test defaults
    frame_view_1 = classification_instance_1.get_annotation(1)
    assert frame_view_1.created_by is None
    assert_datetime_is_recent(frame_view_1.created_at)
    assert frame_view_1.last_edited_by is None
    assert_datetime_is_recent(frame_view_1.last_edited_at)
    assert frame_view_1.confidence is 1
    assert frame_view_1.manual_annotation is True
    assert frame_view_1.reviews is None

    specific_time = datetime.datetime.now() - datetime.timedelta(days=1)
    frame_view_1.created_by = "zeus@gmail.com"
    frame_view_1.created_at = specific_time
    frame_view_1.last_edited_by = "poseidon@gmail.com"
    frame_view_1.last_edited_at = specific_time
    frame_view_1.confidence = 0.5
    frame_view_1.manual_annotation = False

    assert frame_view_1.created_by == "zeus@gmail.com"
    assert frame_view_1.created_at == specific_time
    assert frame_view_1.last_edited_by == "poseidon@gmail.com"
    assert frame_view_1.last_edited_at == specific_time
    assert frame_view_1.confidence == 0.5
    assert frame_view_1.manual_annotation == False

    classification_instance_1.remove_from_frames(1)

    # Using invalid frame view.
    with pytest.raises(LabelRowError):
        x = frame_view_1.created_by
    with pytest.raises(LabelRowError):
        frame_view_1.created_by = "aphrodite@gmail.com"


def test_add_and_get_classification_instances_to_label_row():
    label_row = LabelRowV2(FAKE_LABEL_ROW_METADATA, Mock())
    label_row.from_labels_dict(empty_image_group_labels, all_types_structure)

    classification_instance_1 = ClassificationInstance(text_classification)
    classification_instance_2 = ClassificationInstance(text_classification)
    classification_instance_3 = ClassificationInstance(checklist_classification)

    classification_instance_1.set_for_frames(Range(1, 2))
    classification_instance_2.set_for_frames(Range(3, 4))
    classification_instance_3.set_for_frames(Range(1, 4))

    label_row.add_classification_instance(classification_instance_1)
    label_row.add_classification_instance(classification_instance_2)
    label_row.add_classification_instance(classification_instance_3)

    classification_instances = label_row.get_classification_instances()
    assert set(classification_instances) == {
        classification_instance_1,
        classification_instance_2,
        classification_instance_3,
    }

    filtered_classification_instances = label_row.get_classification_instances(text_classification)
    assert set(filtered_classification_instances) == {classification_instance_1, classification_instance_2}

    overlapping_classification_instance = ClassificationInstance(text_classification)
    overlapping_classification_instance.set_for_frames(1)
    with pytest.raises(LabelRowError):
        label_row.add_classification_instance(overlapping_classification_instance)

    overlapping_classification_instance.remove_from_frames(1)
    overlapping_classification_instance.set_for_frames(5)
    label_row.add_classification_instance(overlapping_classification_instance)
    with pytest.raises(LabelRowError):
        overlapping_classification_instance.set_for_frames(1)
    with pytest.raises(LabelRowError):
        overlapping_classification_instance.set_for_frames(1, overwrite=True)

    label_row.remove_classification(classification_instance_1)
    overlapping_classification_instance.set_for_frames(1)

    with pytest.raises(LabelRowError):
        overlapping_classification_instance.set_for_frames(3)
    classification_instance_2.remove_from_frames(3)
    overlapping_classification_instance.set_for_frames(3)


def test_object_instance_answer_for_static_attributes():

    object_instance = ObjectInstance(deeply_nested_polygon_item)

    assert object_instance.get_answer(nested_polygon_text) is None

    object_instance.set_answer("Zeus", attribute=nested_polygon_text)
    assert object_instance.get_answer(nested_polygon_text) == "Zeus"

    with pytest.raises(LabelRowError):
        # Invalid attribute
        object_instance.get_answer(dynamic_text)

    # Setting frames for a non-dynamic attribute
    assert object_instance.get_answer(nested_polygon_checklist) == []
    with pytest.raises(LabelRowError):
        object_instance.set_answer(
            [nested_polygon_checklist_option_1],
            attribute=nested_polygon_checklist,
            frames=1,
        )

    assert object_instance.get_answer(nested_polygon_checklist) == []

    # Overwriting frames
    with pytest.raises(LabelRowError):
        object_instance.set_answer("Poseidon", attribute=nested_polygon_text)

    assert object_instance.get_answer(nested_polygon_text) == "Zeus"
    object_instance.set_answer("Poseidon", attribute=nested_polygon_text, overwrite=True)
    assert object_instance.get_answer(nested_polygon_text) == "Poseidon"


def test_object_instance_answer_static_checklist():
    object_instance = ObjectInstance(deeply_nested_polygon_item)

    assert object_instance.get_answer(nested_polygon_checklist) == []

    object_instance.set_answer([], attribute=nested_polygon_checklist)

    assert object_instance.get_answer(nested_polygon_checklist) == []

    with pytest.raises(LabelRowError):
        # Already set the answer
        object_instance.set_answer([nested_polygon_checklist_option_1], attribute=nested_polygon_checklist)

    object_instance.set_answer([nested_polygon_checklist_option_1], overwrite=True)  # inferred answer
    assert object_instance.get_answer(nested_polygon_checklist) == [nested_polygon_checklist_option_1]

    object_instance.set_answer(
        [nested_polygon_checklist_option_1, nested_polygon_checklist_option_2],
        attribute=nested_polygon_checklist,
        overwrite=True,
    )

    assert object_instance.get_answer(nested_polygon_checklist) == [
        nested_polygon_checklist_option_1,
        nested_polygon_checklist_option_2,
    ]


def test_object_instance_answer_static_nested_radio():
    object_instance = ObjectInstance(deeply_nested_polygon_item)

    assert object_instance.get_answer(radio_attribute_level_1) is None

    with pytest.raises(LabelRowError):
        object_instance.set_answer("Poseidon", attribute=radio_nested_option_1_text)
    assert object_instance.get_answer(radio_attribute_level_1) is None

    object_instance.set_answer(radio_nested_option_1, attribute=radio_attribute_level_1)
    assert object_instance.get_answer(radio_attribute_level_1) == radio_nested_option_1

    with pytest.raises(LabelRowError):
        # inferring answers does not work if multiple text answers are possible.
        object_instance.set_answer("Zeus")  # inferred answer

    object_instance.set_answer("Zeus", attribute=radio_nested_option_1_text)
    assert object_instance.get_answer(radio_nested_option_1_text) == "Zeus"

    # Switching to a new radio answer
    assert object_instance.get_answer(radio_nested_option_2_checklist) is None

    object_instance.set_answer(radio_nested_option_2, attribute=radio_attribute_level_1, overwrite=True)
    assert object_instance.get_answer(radio_nested_option_1_text) is None

    object_instance.set_answer(
        [radio_nested_option_2_checklist_option_1, radio_nested_option_2_checklist_option_2],
        radio_nested_option_2_checklist,
    )
    assert object_instance.get_answer(radio_nested_option_2_checklist) == [
        radio_nested_option_2_checklist_option_1,
        radio_nested_option_2_checklist_option_2,
    ]


def test_object_instance_answer_dynamic_attributes():
    object_instance = ObjectInstance(keypoint_dynamic)

    assert object_instance.get_answer(dynamic_text) == []

    object_instance.set_answer("Zeus", attribute=dynamic_text, frames=1)
    assert object_instance.get_answer(dynamic_text) == [AnswerForFrames(answer="Zeus", ranges=[Range(1, 1)])]

    with pytest.raises(LabelRowError):
        # Invalid attribute
        object_instance.get_answer(nested_polygon_text)

    assert object_instance.get_answer(dynamic_checklist) == []

    # Overwriting frames
    object_instance.set_answer("Poseidon", attribute=dynamic_text, frames=1)
    assert object_instance.get_answer(dynamic_text) == [AnswerForFrames(answer="Poseidon", ranges=[Range(1, 1)])]


def test_object_instance_answer_dynamic_no_frames_argument():
    object_instance = ObjectInstance(keypoint_dynamic)

    object_instance.set_answer("Zeus", attribute=dynamic_text)
    assert object_instance.get_answer(dynamic_text) == []

    object_instance.set_for_frames(KEYPOINT_COORDINATES, frames=1)
    object_instance.set_for_frames(KEYPOINT_COORDINATES, frames=2)
    object_instance.set_for_frames(KEYPOINT_COORDINATES, frames=3)
    assert object_instance.get_answer(dynamic_text) == []

    object_instance.set_answer("Zeus", attribute=dynamic_text)
    # Answers for all coordinates
    assert object_instance.get_answer(dynamic_text) == [
        AnswerForFrames(answer="Zeus", ranges=[Range(1, 3)]),
    ]

    object_instance.set_for_frames(KEYPOINT_COORDINATES, frames=5)
    object_instance.set_for_frames(KEYPOINT_COORDINATES, frames=6)
    # Nothing changes after setting new coordinates
    assert object_instance.get_answer(dynamic_text) == [
        AnswerForFrames(answer="Zeus", ranges=[Range(1, 3)]),
    ]

    object_instance.set_answer("Poseidon", attribute=dynamic_text, frames=[Range(2, 2), Range(6, 6)])
    # Setting frames does only set the frames you specify.
    assert object_instance.get_answer(dynamic_text) == [
        AnswerForFrames(answer="Zeus", ranges=[Range(1, 1), Range(3, 3)]),
        AnswerForFrames(answer="Poseidon", ranges=[Range(2, 2), Range(6, 6)]),
    ]


# TODO: check if everything is handled correctly when running `remove_from_frames` with dynamic answers.
def test_object_instance_answer_dynamic_is_valid():
    object_instance = ObjectInstance(keypoint_dynamic)

    with pytest.raises(LabelRowError) as e:
        object_instance.is_valid()
    assert "not on any frames" in str(e)

    object_instance.are_dynamic_answers_valid()

    object_instance.set_answer("Zeus", attribute=dynamic_text, frames=1)
    # Dynamic answers without corresponding coordinates.

    with pytest.raises(LabelRowError) as e:
        object_instance.is_valid()
    assert "not on any frames" in str(e)

    with pytest.raises(LabelRowError) as e:
        object_instance.are_dynamic_answers_valid()
    assert "only on frames" in str(e)

    object_instance.set_for_frames(KEYPOINT_COORDINATES, frames=1)
    object_instance.set_for_frames(KEYPOINT_COORDINATES, frames=2)
    object_instance.set_for_frames(KEYPOINT_COORDINATES, frames=3)
    object_instance.is_valid()


def test_object_instance_answer_dynamic_getter_filters():
    object_instance = ObjectInstance(keypoint_dynamic)

    object_instance.set_answer("Zeus", attribute=dynamic_text, frames=1)
    object_instance.set_answer("Poseidon", attribute=dynamic_text, frames=Range(2, 4))

    assert object_instance.get_answer(dynamic_text, filter_frame=1) == [
        AnswerForFrames(answer="Zeus", ranges=[Range(1, 1)]),
    ]
    assert object_instance.get_answer(dynamic_text, filter_answer="Poseidon") == [
        AnswerForFrames(answer="Poseidon", ranges=[Range(2, 4)]),
    ]
    assert object_instance.get_answer(dynamic_text, filter_answer="Poseidon", filter_frame=2) == [
        AnswerForFrames(answer="Poseidon", ranges=[Range(2, 4)]),
    ]


def test_object_instance_static_answer_delete():
    object_instance = ObjectInstance(deeply_nested_polygon_item)

    object_instance.set_answer(radio_nested_option_1, attribute=radio_attribute_level_1)
    assert object_instance.get_answer(radio_attribute_level_1) == radio_nested_option_1

    object_instance.set_answer("Zeus", attribute=radio_nested_option_1_text)
    assert object_instance.get_answer(radio_nested_option_1_text) == "Zeus"

    object_instance.delete_answer(radio_attribute_level_1)
    assert object_instance.get_answer(radio_attribute_level_1) is None
    assert object_instance.get_answer(radio_nested_option_1_text) is None


def test_object_instance_dynamic_answer_delete():
    object_instance = ObjectInstance(keypoint_dynamic)

    object_instance.set_answer("Zeus", attribute=dynamic_text, frames=1)
    object_instance.set_answer("Poseidon", attribute=dynamic_text, frames=Range(2, 4))
    object_instance.set_answer("Ulysses", attribute=dynamic_text, frames=Range(5, 6))

    assert object_instance.get_answer(dynamic_text) == [
        AnswerForFrames(answer="Zeus", ranges=[Range(1, 1)]),
        AnswerForFrames(answer="Poseidon", ranges=[Range(2, 4)]),
        AnswerForFrames(answer="Ulysses", ranges=[Range(5, 6)]),
    ]

    object_instance.delete_answer(dynamic_text, filter_frame=2)
    assert object_instance.get_answer(dynamic_text) == [
        AnswerForFrames(answer="Zeus", ranges=[Range(1, 1)]),
        AnswerForFrames(answer="Poseidon", ranges=[Range(3, 4)]),
        AnswerForFrames(answer="Ulysses", ranges=[Range(5, 6)]),
    ]

    object_instance.delete_answer(dynamic_text, filter_answer="Ulysses")
    assert object_instance.get_answer(dynamic_text) == [
        AnswerForFrames(answer="Zeus", ranges=[Range(1, 1)]),
        AnswerForFrames(answer="Poseidon", ranges=[Range(3, 4)]),
    ]

    object_instance.delete_answer(dynamic_text)
    assert object_instance.get_answer(dynamic_text) == []


def test_classification_instance_delete():
    classification_instance = ClassificationInstance(radio_classification)
    attribute = radio_classification.attributes[0]

    classification_instance.set_answer(answer=radio_classification_option_2, attribute=attribute)
    classification_instance.set_answer(answer="Dionysus", attribute=radio_classification_option_2_text)

    assert classification_instance.get_answer() == radio_classification_option_2
    assert classification_instance.get_answer(radio_classification_option_2_text) == "Dionysus"

    # Delete the nested answer only
    classification_instance.delete_answer(radio_classification_option_2_text)
    assert classification_instance.get_answer(radio_classification_option_2_text) is None

    classification_instance.set_answer(answer="Poseidon", attribute=radio_classification_option_2_text)
    assert classification_instance.get_answer(radio_classification_option_2_text) == "Poseidon"

    # Delete the root answer
    classification_instance.delete_answer()
    assert classification_instance.get_answer() is None
    assert classification_instance.get_answer(radio_classification_option_2_text) is None


def test_label_status_forwards_compatibility():
    assert LabelStatus("NOT_LABELLED") == LabelStatus.NOT_LABELLED
    assert LabelStatus("new-unknown-status") == LabelStatus.MISSING_LABEL_STATUS
    assert LabelStatus("new-unknown-status").value == "_MISSING_LABEL_STATUS_"


def test_frame_view():
    label_row_metadata_dict = asdict(FAKE_LABEL_ROW_METADATA)
    label_row_metadata_dict["frames_per_second"] = 25
    label_row_metadata_dict["duration"] = 0.2
    label_row_metadata_dict["number_of_frames"] = 5
    label_row_metadata = LabelRowMetadata(**label_row_metadata_dict)

    label_row = LabelRowV2(label_row_metadata, Mock())

    assert label_row.number_of_frames == label_row_metadata.number_of_frames

    with pytest.raises(LabelRowError):
        frames = label_row.get_frame_views()

    label_row.from_labels_dict(empty_image_group_labels, all_types_structure)  # initialise the labels.

    frame_view: LabelRowV2.FrameView = label_row.get_frame_view(1)
    assert frame_view.get_object_instances() == []
    assert frame_view.get_classification_instances() == []

    object_instance = ObjectInstance(box_ontology_item)
    classification_instance = ClassificationInstance(text_classification)

    frame_view.add_object_instance(object_instance, BOX_COORDINATES)
    frame_view.add_classification_instance(classification_instance)

    frames = label_row.get_frame_views()
    assert len(frames) == label_row_metadata.duration * label_row_metadata.frames_per_second

    frame_num = 0
    for frame in label_row.get_frame_views():
        assert frame.frame == frame_num
        frame_num += 1

    assert frames[0].image_hash == "f850dfb4-7146-49e0-9afc-2b9434a64a9f"
    assert frames[0].image_title == "Screenshot 2021-11-24 at 18.35.57.png"
    assert frames[0].file_type == "image/png"
    assert frames[0].width == 952
    assert frames[0].height == 678
    assert (
        frames[0].data_link
        == "https://storage.googleapis.com/cord-ai-platform.appspot.com/cord-images-prod/yiA5JxmLEGSoEcJAuxr3AJdDDXE2/f850dfb4-7146-49e0-9afc-2b9434a64a9f?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=firebase-adminsdk-64w1p%40cord-ai-platform.iam.gserviceaccount.com%2F20221201%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20221201T133838Z&X-Goog-Expires=604800&X-Goog-SignedHeaders=host&X-Goog-Signature=94c66d85014ff52a99fec1cf671ccc1b859ebead4308ca82c4d810e13ac285d2afa8cfa4bfcbd09f615b243b95d9b1d5d1d779e7a4ba5832a2207b4f3b99dbe405ded373f03f06abe4e24098e70568c269899f2f397c7a4392a1c3090bff2b8c98f2177f5db36f0884a83033f404354bdfda0506bf162e25ff6186fc54104e8273e86959b0296958a03359514660528a54ba94e25c59e59534ce5102f9c87ff7cb03a591606b3a191123af4a30fa4296a788a9433f0c8c1dc7d3f80a022cc42f8716ba44d09ecd04118dc6e4ee5977ffbadcc8d635cc4e906f024dba26e520cfc304fc0f3458a3e3b2422c196956fd3024a6eba0512d557683487b10a1a381b4"
    )

    assert frame_view.get_object_instances() == [object_instance]
    assert frame_view.get_classification_instances() == [classification_instance]
