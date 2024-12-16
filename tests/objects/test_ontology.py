import copy
import logging

import pytest

import encord.objects
import encord.objects.attributes
import encord.objects.classification
import encord.objects.ontology_structure
import encord.objects.options
from encord.objects.common import Shape
from encord.objects.skeleton_template import SkeletonTemplate, SkeletonTemplateCoordinate
from encord.objects.utils import short_uuid_str
from tests.objects.data.data_editor_blob import EDITOR_BLOB

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# intentionally using a different import for backwards compatibility check
OBJECT_1 = encord.objects.Object(
    uid=1,
    name="Eye",
    color="#D33115",
    shape=encord.objects.Shape.BOUNDING_BOX,
    feature_node_hash="a55abbeb",
)

FLAT_OPTION_1 = encord.objects.FlatOption(
    uid=[2, 1, 1],
    feature_node_hash="2bc17c88",
    label="Is it a cute nose?",
    value="is_it_a_cute_nose?",
)

FLAT_OPTION_2 = encord.objects.FlatOption(
    uid=[2, 1, 2],
    feature_node_hash="86eaa4f2",
    label="Is it a wet nose? ",
    value="is_it_a_wet_nose?_",
)

CHECKLIST_ATTRIBUTE = encord.objects.ChecklistAttribute(
    uid=[2, 1],
    feature_node_hash="1e3e5cad",
    name="Additional details about the nose",
    required=True,
    dynamic=False,
    options=[FLAT_OPTION_1, FLAT_OPTION_2],
)


OBJECT_2 = encord.objects.Object(
    uid=2,
    name="Nose",
    color="#E27300",
    shape=encord.objects.Shape.POLYGON,
    feature_node_hash="86648f32",
    attributes=[CHECKLIST_ATTRIBUTE],
)

# intentionally using a different import for backwards compatibility check
RADIO_ATTRIBUTE_1 = encord.objects.RadioAttribute(
    uid=[4, 1, 1, 1],
    feature_node_hash="59204845",
    name="Leaf",
    required=False,
    dynamic=False,
)

NESTABLE_OPTION_3 = encord.objects.NestableOption(
    uid=[4, 1, 1],
    feature_node_hash="5d102ce6",
    label="Nested Option",
    value="nested_option",
    nested_options=[RADIO_ATTRIBUTE_1],
)

RADIO_ATTRIBUTE_2 = encord.objects.RadioAttribute(
    uid=[4, 1],
    feature_node_hash="cabfedb5",
    name="Radio with options",
    required=False,
    dynamic=False,
    options=[NESTABLE_OPTION_3],
)
OBJECT_3 = encord.objects.Object(
    uid=3,
    name="Example",
    color="#FE9200",
    shape=encord.objects.Shape.POLYLINE,
    feature_node_hash="6eeba59b",
    attributes=[RADIO_ATTRIBUTE_2],
)

NESTABLE_OPTION_1 = encord.objects.NestableOption(
    uid=[1, 1, 1],
    feature_node_hash="a3aeb48d",
    label="Yes",
    value="yes",
)

NESTABLE_OPTION_2 = encord.objects.NestableOption(
    uid=[1, 1, 2],
    feature_node_hash="d0a4b373",
    label="No",
    value="no",
)

RADIO_ATTRIBUTE_3 = encord.objects.RadioAttribute(
    uid=[1, 1],
    feature_node_hash="a6136d14",
    name="Is the cat standing?",
    required=True,
    dynamic=False,
    options=[NESTABLE_OPTION_1, NESTABLE_OPTION_2],
)
# intentionally using a different import for backwards compatibility check
CLASSIFICATION_1 = encord.objects.Classification(
    uid=1,
    feature_node_hash="a39d81c0",
    attributes=[RADIO_ATTRIBUTE_3],
)
SKELETON_TEMPLATE_COORDINATES = [
    SkeletonTemplateCoordinate(x=0, y=0, name="point_0"),
    SkeletonTemplateCoordinate(x=1, y=1, name="point_1"),
]
SKELETON_TEMPLATE_LINE = SkeletonTemplate(
    name="Line",
    width=100,
    height=100,
    skeleton={str(i): x for (i, x) in enumerate(SKELETON_TEMPLATE_COORDINATES)},
    skeleton_edges={"0": {"1": {"color": "#00000"}}},
    feature_node_hash="c67522ee",
)
# intentionally using a different import for backwards compatibility check
EXPECTED_ONTOLOGY: encord.objects.OntologyStructure = encord.objects.OntologyStructure(
    objects=[
        OBJECT_1,
        OBJECT_2,
        OBJECT_3,
    ],
    classifications=[CLASSIFICATION_1],
    skeleton_templates={"Line": SKELETON_TEMPLATE_LINE},
)


def test_ontology_structure_round_trip():
    assert EXPECTED_ONTOLOGY == encord.objects.OntologyStructure.from_dict(EXPECTED_ONTOLOGY.to_dict())


def test_json_to_ontology():
    actual = encord.objects.OntologyStructure.from_dict(copy.deepcopy(EDITOR_BLOB))
    assert EXPECTED_ONTOLOGY == actual


def test_ontology_to_json():
    actual = EXPECTED_ONTOLOGY.to_dict()
    assert copy.deepcopy(EDITOR_BLOB) == actual


def test_add_classification():
    ontology = encord.objects.OntologyStructure()
    cls1 = ontology.add_classification()
    assert cls1.uid == 1
    assert cls1.feature_node_hash
    cls2 = ontology.add_classification()
    assert cls2.uid == 2
    assert cls2.feature_node_hash

    feature_node_hash = short_uuid_str()
    cls3 = ontology.add_classification(uid=7, feature_node_hash=feature_node_hash)
    assert cls3.uid == 7
    assert cls3.feature_node_hash == feature_node_hash

    assert cls1.feature_node_hash != cls2.feature_node_hash

    assert len(ontology.classifications) == 3


def test_add_classification_duplicate_values():
    ontology = encord.objects.OntologyStructure()
    obj1 = ontology.add_classification(1, "12345678")
    with pytest.raises(ValueError):
        _ = ontology.add_classification(1)
    with pytest.raises(ValueError):
        _ = ontology.add_classification(2, feature_node_hash=obj1.feature_node_hash)

    assert len(ontology.classifications) == 1


def test_add_object():
    ontology = encord.objects.OntologyStructure()
    obj1 = ontology.add_object("Apple", Shape.BOUNDING_BOX)
    assert obj1.uid == 1
    assert obj1.color
    assert obj1.feature_node_hash
    obj2 = ontology.add_object("Orange", Shape.BOUNDING_BOX)
    assert obj2.uid == 2
    assert obj2.color
    assert obj2.feature_node_hash

    feature_node_hash = short_uuid_str()
    obj3 = ontology.add_object("Lemon", Shape.POLYLINE, 7, feature_node_hash=feature_node_hash)

    assert obj3.uid == 7
    assert obj3.color
    assert obj3.feature_node_hash == feature_node_hash

    assert obj1.feature_node_hash != obj2.feature_node_hash
    assert len(set([obj.color for obj in [obj1, obj2, obj3]])) == 3  # all the colors are different: auto-assigned

    assert len(ontology.objects) == 3


def test_add_object_duplicate_values():
    ontology = encord.objects.OntologyStructure()
    obj1 = ontology.add_object("Apple", Shape.BOUNDING_BOX, 1, "#000000", "12345678")
    with pytest.raises(ValueError):
        _ = ontology.add_object("Orange", Shape.BOUNDING_BOX, 1)
    with pytest.raises(ValueError):
        _ = ontology.add_object("Orange", Shape.BOUNDING_BOX, feature_node_hash=obj1.feature_node_hash)

    assert len(ontology.objects) == 1


def test_add_object_nested_classifications():
    ontology = encord.objects.OntologyStructure()
    obj1 = ontology.add_object("Apple", Shape.BOUNDING_BOX, 1, "#000000", "12345678")

    stripes = obj1.add_attribute(encord.objects.TextAttribute, "Stripes")
    assert stripes.uid == [1, 1]
    assert stripes.feature_node_hash
    assert isinstance(stripes, encord.objects.TextAttribute)
    assert not stripes.required
    assert not stripes.dynamic

    ripeness = obj1.add_attribute(
        encord.objects.RadioAttribute,
        "Ripeness",
        local_uid=7,
        feature_node_hash="12345678",
        required=True,
        dynamic=True,
    )
    assert ripeness.uid == [1, 7]
    assert ripeness.feature_node_hash
    assert isinstance(ripeness, encord.objects.RadioAttribute)
    assert ripeness.required
    assert ripeness.dynamic

    damage = obj1.add_attribute(encord.objects.ChecklistAttribute, "Damage", required=True, dynamic=True)
    assert damage.uid == [1, 8]
    assert damage.feature_node_hash
    assert isinstance(damage, encord.objects.ChecklistAttribute)
    assert damage.required
    assert damage.dynamic


def test_add_object_nested_classifications_duplicate_values():
    ontology = encord.objects.OntologyStructure()
    obj1 = ontology.add_object("Apple", Shape.BOUNDING_BOX, 1, "#000000", "12345678")

    attr1 = obj1.add_attribute(encord.objects.TextAttribute, "Stripes")
    with pytest.raises(ValueError):
        obj1.add_attribute(encord.objects.ChecklistAttribute, "Stars, I guess?", local_uid=1)
    with pytest.raises(ValueError):
        obj1.add_attribute(
            encord.objects.ChecklistAttribute, "Stars, I guess?", feature_node_hash=attr1.feature_node_hash
        )


def test_add_classification_attribute():
    ontology = encord.objects.OntologyStructure()
    cls1 = ontology.add_classification()

    clouds = cls1.add_attribute(encord.objects.RadioAttribute, "Cloud cover")
    assert clouds.uid == [1, 1]
    assert clouds.feature_node_hash
    assert isinstance(clouds, encord.objects.RadioAttribute)
    assert not clouds.required

    with pytest.raises(ValueError):  # only one root attribute per classification is allowed
        cls1.add_attribute(encord.objects.TextAttribute, "metadata")


def test_build_checkbox_options():
    ontology = encord.objects.OntologyStructure()
    cls1 = ontology.add_classification()

    clouds = cls1.add_attribute(encord.objects.ChecklistAttribute, "Cloud cover")
    one = clouds.add_option("Type One")
    assert one.value == "type_one"
    two = clouds.add_option("Type Two", value="two", local_uid=6)
    assert two.value == "two"
    three = clouds.add_option("Type Three", feature_node_hash="12345678")

    assert len(clouds.options) == 3
    assert len({opt.feature_node_hash for opt in clouds.options}) == 3  # all different
    assert three.uid == [1, 1, 7]

    assert isinstance(one, encord.objects.FlatOption)


def test_build_nested_options():
    ontology = encord.objects.OntologyStructure()
    cls1 = ontology.add_classification()

    clouds = cls1.add_attribute(encord.objects.RadioAttribute, "Cloud cover")
    one = clouds.add_option("Type One")
    two = clouds.add_option("Type Two", value="two", local_uid=6)

    assert isinstance(one, encord.objects.NestableOption)
    assert isinstance(two, encord.objects.NestableOption)

    detail1 = one.add_nested_attribute(encord.objects.RadioAttribute, "detail one")
    one.add_nested_attribute(encord.objects.TextAttribute, "detail two")

    detail1value1 = detail1.add_option("value 1")
    assert isinstance(detail1value1, encord.objects.NestableOption)
    assert detail1value1.uid == [1, 1, 1, 1, 1]  # five levels: root, 'clouds', 'type one', 'detail one', 'value 1'


def build_expected_ontology():
    ontology = encord.objects.OntologyStructure()

    _ = ontology.add_object(
        name="Eye",
        color="#D33115",
        shape=encord.objects.Shape.BOUNDING_BOX,
        feature_node_hash="a55abbeb",
    )
    nose = ontology.add_object(
        name="Nose",
        color="#E27300",
        shape=encord.objects.Shape.POLYGON,
        feature_node_hash="86648f32",
    )
    nose_detail = nose.add_attribute(
        encord.objects.ChecklistAttribute,
        feature_node_hash="1e3e5cad",
        name="Additional details about the nose",
        required=True,
    )
    nose_detail.add_option(feature_node_hash="2bc17c88", label="Is it a cute nose?")
    nose_detail.add_option(feature_node_hash="86eaa4f2", label="Is it a wet nose? ")
    example = ontology.add_object(
        name="Example",
        color="#FE9200",
        shape=encord.objects.Shape.POLYLINE,
        feature_node_hash="6eeba59b",
    )
    radio = example.add_attribute(
        encord.objects.RadioAttribute, feature_node_hash="cabfedb5", name="Radio with options"
    )
    nested = radio.add_option(feature_node_hash="5d102ce6", label="Nested Option")
    _ = nested.add_nested_attribute(encord.objects.RadioAttribute, feature_node_hash="59204845", name="Leaf")
    cls = ontology.add_classification(feature_node_hash="a39d81c0")
    cat_standing = cls.add_attribute(
        encord.objects.RadioAttribute,
        feature_node_hash="a6136d14",
        name="Is the cat standing?",
        required=True,
    )
    cat_standing.add_option(feature_node_hash="a3aeb48d", label="Yes")
    cat_standing.add_option(feature_node_hash="d0a4b373", label="No")

    assert ontology.to_dict() == EXPECTED_ONTOLOGY.to_dict()


def test_ontology_getters():
    # Object
    assert EXPECTED_ONTOLOGY.get_child_by_hash(OBJECT_1.feature_node_hash) == OBJECT_1
    assert EXPECTED_ONTOLOGY.get_child_by_hash(OBJECT_1.feature_node_hash, encord.objects.Object)
    with pytest.raises(TypeError):
        EXPECTED_ONTOLOGY.get_child_by_hash(OBJECT_1.feature_node_hash, encord.objects.TextAttribute)

    assert EXPECTED_ONTOLOGY.get_children_by_title(OBJECT_1.name) == [OBJECT_1]
    assert EXPECTED_ONTOLOGY.get_children_by_title(OBJECT_1.name, encord.objects.Object) == [OBJECT_1]
    assert EXPECTED_ONTOLOGY.get_children_by_title(OBJECT_1.name, encord.objects.Classification) == []

    # Option
    assert EXPECTED_ONTOLOGY.get_child_by_hash(FLAT_OPTION_1.feature_node_hash) == FLAT_OPTION_1
    assert EXPECTED_ONTOLOGY.get_child_by_hash(FLAT_OPTION_1.feature_node_hash, encord.objects.FlatOption)
    with pytest.raises(TypeError):
        EXPECTED_ONTOLOGY.get_child_by_hash(FLAT_OPTION_1.feature_node_hash, encord.objects.TextAttribute)

    assert EXPECTED_ONTOLOGY.get_children_by_title(FLAT_OPTION_1.label) == [FLAT_OPTION_1]
    assert EXPECTED_ONTOLOGY.get_children_by_title(FLAT_OPTION_1.label, encord.objects.FlatOption) == [FLAT_OPTION_1]
    assert EXPECTED_ONTOLOGY.get_children_by_title(FLAT_OPTION_1.label, encord.objects.Classification) == []

    # Attribute
    assert EXPECTED_ONTOLOGY.get_child_by_hash(CHECKLIST_ATTRIBUTE.feature_node_hash) == CHECKLIST_ATTRIBUTE
    assert EXPECTED_ONTOLOGY.get_child_by_hash(CHECKLIST_ATTRIBUTE.feature_node_hash, encord.objects.ChecklistAttribute)
    with pytest.raises(TypeError):
        EXPECTED_ONTOLOGY.get_child_by_hash(CHECKLIST_ATTRIBUTE.feature_node_hash, encord.objects.TextAttribute)

    assert EXPECTED_ONTOLOGY.get_children_by_title(CHECKLIST_ATTRIBUTE.name) == [CHECKLIST_ATTRIBUTE]
    assert EXPECTED_ONTOLOGY.get_children_by_title(CHECKLIST_ATTRIBUTE.name, encord.objects.ChecklistAttribute) == [
        CHECKLIST_ATTRIBUTE
    ]
    assert EXPECTED_ONTOLOGY.get_children_by_title(CHECKLIST_ATTRIBUTE.name, encord.objects.Classification) == []

    # Classification
    assert EXPECTED_ONTOLOGY.get_child_by_hash(CLASSIFICATION_1.feature_node_hash) == CLASSIFICATION_1
    assert EXPECTED_ONTOLOGY.get_child_by_hash(CLASSIFICATION_1.feature_node_hash, encord.objects.Classification)
    with pytest.raises(TypeError):
        EXPECTED_ONTOLOGY.get_child_by_hash(CLASSIFICATION_1.feature_node_hash, encord.objects.TextAttribute)
    # NOTE: getting by name does not work. The classification has no name, just its attribute


def test_object_getters():
    # Option
    assert OBJECT_2.get_child_by_hash(FLAT_OPTION_1.feature_node_hash) == FLAT_OPTION_1
    assert OBJECT_2.get_child_by_hash(FLAT_OPTION_1.feature_node_hash, encord.objects.FlatOption)
    with pytest.raises(TypeError):
        OBJECT_2.get_child_by_hash(FLAT_OPTION_1.feature_node_hash, encord.objects.TextAttribute)

    assert OBJECT_2.get_children_by_title(FLAT_OPTION_1.label) == [FLAT_OPTION_1]
    assert OBJECT_2.get_children_by_title(FLAT_OPTION_1.label, encord.objects.FlatOption) == [FLAT_OPTION_1]
    assert OBJECT_2.get_children_by_title(FLAT_OPTION_1.label, encord.objects.ChecklistAttribute) == []

    # Attribute
    assert OBJECT_2.get_child_by_hash(CHECKLIST_ATTRIBUTE.feature_node_hash) == CHECKLIST_ATTRIBUTE
    assert OBJECT_2.get_child_by_hash(CHECKLIST_ATTRIBUTE.feature_node_hash, encord.objects.ChecklistAttribute)
    with pytest.raises(TypeError):
        OBJECT_2.get_child_by_hash(CHECKLIST_ATTRIBUTE.feature_node_hash, encord.objects.TextAttribute)

    assert OBJECT_2.get_children_by_title(CHECKLIST_ATTRIBUTE.name) == [CHECKLIST_ATTRIBUTE]
    assert OBJECT_2.get_children_by_title(CHECKLIST_ATTRIBUTE.name, encord.objects.ChecklistAttribute) == [
        CHECKLIST_ATTRIBUTE
    ]
    assert OBJECT_2.get_children_by_title(CHECKLIST_ATTRIBUTE.name, encord.objects.TextAttribute) == []


def test_classification_getters():
    # Option
    assert CLASSIFICATION_1.get_child_by_hash(NESTABLE_OPTION_2.feature_node_hash) == NESTABLE_OPTION_2
    assert CLASSIFICATION_1.get_child_by_hash(NESTABLE_OPTION_2.feature_node_hash, encord.objects.NestableOption)
    with pytest.raises(TypeError):
        CLASSIFICATION_1.get_child_by_hash(NESTABLE_OPTION_2.feature_node_hash, encord.objects.TextAttribute)

    assert CLASSIFICATION_1.get_children_by_title(NESTABLE_OPTION_2.label) == [NESTABLE_OPTION_2]
    assert CLASSIFICATION_1.get_children_by_title(NESTABLE_OPTION_2.label, encord.objects.NestableOption) == [
        NESTABLE_OPTION_2
    ]
    assert CLASSIFICATION_1.get_children_by_title(NESTABLE_OPTION_2.label, encord.objects.ChecklistAttribute) == []

    # Attribute
    assert CLASSIFICATION_1.get_child_by_hash(RADIO_ATTRIBUTE_3.feature_node_hash) == RADIO_ATTRIBUTE_3
    assert CLASSIFICATION_1.get_child_by_hash(RADIO_ATTRIBUTE_3.feature_node_hash, encord.objects.RadioAttribute)
    with pytest.raises(TypeError):
        CLASSIFICATION_1.get_child_by_hash(RADIO_ATTRIBUTE_3.feature_node_hash, encord.objects.TextAttribute)

    assert CLASSIFICATION_1.get_children_by_title(RADIO_ATTRIBUTE_3.name) == [RADIO_ATTRIBUTE_3]
    assert CLASSIFICATION_1.get_children_by_title(RADIO_ATTRIBUTE_3.name, encord.objects.RadioAttribute) == [
        RADIO_ATTRIBUTE_3
    ]
    assert CLASSIFICATION_1.get_children_by_title(RADIO_ATTRIBUTE_3.name, encord.objects.TextAttribute) == []


def test_attribute_getters():
    # Option
    assert RADIO_ATTRIBUTE_2.get_child_by_hash(NESTABLE_OPTION_3.feature_node_hash) == NESTABLE_OPTION_3
    assert RADIO_ATTRIBUTE_2.get_child_by_hash(NESTABLE_OPTION_3.feature_node_hash, encord.objects.NestableOption)
    with pytest.raises(TypeError):
        RADIO_ATTRIBUTE_2.get_child_by_hash(NESTABLE_OPTION_3.feature_node_hash, encord.objects.TextAttribute)

    assert RADIO_ATTRIBUTE_2.get_children_by_title(NESTABLE_OPTION_3.label) == [NESTABLE_OPTION_3]
    assert RADIO_ATTRIBUTE_2.get_children_by_title(NESTABLE_OPTION_3.label, encord.objects.NestableOption) == [
        NESTABLE_OPTION_3
    ]
    assert RADIO_ATTRIBUTE_2.get_children_by_title(NESTABLE_OPTION_3.label, encord.objects.ChecklistAttribute) == []

    # Attribute
    assert RADIO_ATTRIBUTE_2.get_child_by_hash(RADIO_ATTRIBUTE_1.feature_node_hash) == RADIO_ATTRIBUTE_1
    assert RADIO_ATTRIBUTE_2.get_child_by_hash(RADIO_ATTRIBUTE_1.feature_node_hash, encord.objects.RadioAttribute)
    with pytest.raises(TypeError):
        RADIO_ATTRIBUTE_2.get_child_by_hash(RADIO_ATTRIBUTE_1.feature_node_hash, encord.objects.TextAttribute)

    assert RADIO_ATTRIBUTE_2.get_children_by_title(RADIO_ATTRIBUTE_1.name) == [RADIO_ATTRIBUTE_1]
    assert RADIO_ATTRIBUTE_2.get_children_by_title(RADIO_ATTRIBUTE_1.name, encord.objects.RadioAttribute) == [
        RADIO_ATTRIBUTE_1
    ]
    assert RADIO_ATTRIBUTE_2.get_children_by_title(RADIO_ATTRIBUTE_1.name, encord.objects.TextAttribute) == []


def test_option_getters():
    # Attribute
    assert NESTABLE_OPTION_3.get_child_by_hash(RADIO_ATTRIBUTE_1.feature_node_hash) == RADIO_ATTRIBUTE_1
    assert NESTABLE_OPTION_3.get_child_by_hash(RADIO_ATTRIBUTE_1.feature_node_hash, encord.objects.RadioAttribute)
    with pytest.raises(TypeError):
        NESTABLE_OPTION_3.get_child_by_hash(RADIO_ATTRIBUTE_1.feature_node_hash, encord.objects.TextAttribute)

    assert NESTABLE_OPTION_3.get_children_by_title(RADIO_ATTRIBUTE_1.name) == [RADIO_ATTRIBUTE_1]
    assert NESTABLE_OPTION_3.get_children_by_title(RADIO_ATTRIBUTE_1.name, encord.objects.RadioAttribute) == [
        RADIO_ATTRIBUTE_1
    ]
    assert NESTABLE_OPTION_3.get_children_by_title(RADIO_ATTRIBUTE_1.name, encord.objects.TextAttribute) == []
