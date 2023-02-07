import json
import logging
import os

import pytest

import encord.objects.classification
import encord.objects.common
import encord.objects.ontology_labels_impl
import encord.objects.ontology_object
from encord.objects import ontology_structure
from encord.objects.common import Shape
from encord.objects.utils import short_uuid_str

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CURRENT_DIR, "data")
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

EXPECTED_ONTOLOGY: encord.objects.ontology_labels_impl.OntologyStructure = (
    encord.objects.ontology_labels_impl.OntologyStructure(
        objects=[
            encord.objects.ontology_labels_impl.Object(
                uid=1,
                name="Eye",
                color="#D33115",
                shape=encord.objects.common.Shape.BOUNDING_BOX,
                feature_node_hash="a55abbeb",
            ),
            encord.objects.ontology_labels_impl.Object(
                uid=2,
                name="Nose",
                color="#E27300",
                shape=encord.objects.common.Shape.POLYGON,
                feature_node_hash="86648f32",
                attributes=[
                    encord.objects.common.ChecklistAttribute(
                        uid=[2, 1],
                        feature_node_hash="1e3e5cad",
                        name="Additional details about the nose",
                        required=True,
                        dynamic=False,
                        options=[
                            encord.objects.common.FlatOption(
                                uid=[2, 1, 1],
                                feature_node_hash="2bc17c88",
                                label="Is it a cute nose?",
                                value="is_it_a_cute_nose?",
                            ),
                            encord.objects.common.FlatOption(
                                uid=[2, 1, 2],
                                feature_node_hash="86eaa4f2",
                                label="Is it a wet nose? ",
                                value="is_it_a_wet_nose?_",
                            ),
                        ],
                    )
                ],
            ),
            encord.objects.ontology_labels_impl.Object(
                uid=3,
                name="Example",
                color="#FE9200",
                shape=encord.objects.common.Shape.POLYLINE,
                feature_node_hash="6eeba59b",
                attributes=[
                    encord.objects.common.RadioAttribute(
                        uid=[4, 1],
                        feature_node_hash="cabfedb5",
                        name="Radio with options",
                        required=False,
                        dynamic=False,
                        options=[
                            encord.objects.common.NestableOption(
                                uid=[4, 1, 1],
                                feature_node_hash="5d102ce6",
                                label="Nested Option",
                                value="nested_option",
                                nested_options=[
                                    encord.objects.common.RadioAttribute(
                                        uid=[4, 1, 1, 1],
                                        feature_node_hash="59204845",
                                        name="Leaf",
                                        required=False,
                                        dynamic=False,
                                    )
                                ],
                            )
                        ],
                    )
                ],
            ),
        ],
        classifications=[
            encord.objects.ontology_labels_impl.Classification(
                uid=1,
                feature_node_hash="a39d81c0",
                attributes=[
                    encord.objects.common.RadioAttribute(
                        uid=[1, 1],
                        feature_node_hash="a6136d14",
                        name="Is the cat standing?",
                        required=True,
                        dynamic=False,
                        options=[
                            encord.objects.common.NestableOption(
                                uid=[1, 1, 1],
                                feature_node_hash="a3aeb48d",
                                label="Yes",
                                value="yes",
                            ),
                            encord.objects.common.NestableOption(
                                uid=[1, 1, 2],
                                feature_node_hash="d0a4b373",
                                label="No",
                                value="no",
                            ),
                        ],
                    )
                ],
            )
        ],
    )
)


def test_json_to_ontology():
    # GIVEN
    file_path = os.path.join(DATA_DIR, "editor_blob.json")
    with open(file_path, "r", encoding="utf8") as f:
        editor_dict = json.load(f)

    # WHEN
    actual = encord.objects.ontology_labels_impl.OntologyStructure.from_dict(editor_dict)

    # THEN
    assert EXPECTED_ONTOLOGY == actual


def test_ontology_to_json():
    # GIVEN
    file_path = os.path.join(DATA_DIR, "editor_blob.json")
    with open(file_path, "r", encoding="utf8") as f:
        editor_dict = json.load(f)

    # WHEN
    actual = EXPECTED_ONTOLOGY.to_dict()

    # THEN
    assert editor_dict == actual


def test_add_classification():
    ontology = encord.objects.ontology_labels_impl.OntologyStructure()
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
    ontology = encord.objects.ontology_labels_impl.OntologyStructure()
    obj1 = ontology.add_classification(1, "12345678")
    with pytest.raises(ValueError):
        obj2 = ontology.add_classification(1)
    with pytest.raises(ValueError):
        obj2 = ontology.add_classification(2, feature_node_hash=obj1.feature_node_hash)

    assert len(ontology.classifications) == 1


def test_add_object():
    ontology = encord.objects.ontology_labels_impl.OntologyStructure()
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
    ontology = encord.objects.ontology_labels_impl.OntologyStructure()
    obj1 = ontology.add_object("Apple", Shape.BOUNDING_BOX, 1, "#000000", "12345678")
    with pytest.raises(ValueError):
        obj2 = ontology.add_object("Orange", Shape.BOUNDING_BOX, 1)
    with pytest.raises(ValueError):
        obj2 = ontology.add_object("Orange", Shape.BOUNDING_BOX, feature_node_hash=obj1.feature_node_hash)

    assert len(ontology.objects) == 1


def test_add_object_nested_classifications():
    ontology = encord.objects.ontology_labels_impl.OntologyStructure()
    obj1 = ontology.add_object("Apple", Shape.BOUNDING_BOX, 1, "#000000", "12345678")

    stripes = obj1.add_attribute(encord.objects.common.TextAttribute, "Stripes")
    assert stripes.uid == [1, 1]
    assert stripes.feature_node_hash
    assert isinstance(stripes, encord.objects.common.TextAttribute)
    assert not stripes.required
    assert not stripes.dynamic
    assert not stripes.has_options_field()

    ripeness = obj1.add_attribute(
        encord.objects.common.RadioAttribute,
        "Ripeness",
        local_uid=7,
        feature_node_hash="12345678",
        required=True,
        dynamic=True,
    )
    assert ripeness.uid == [1, 7]
    assert ripeness.feature_node_hash
    assert isinstance(ripeness, encord.objects.common.RadioAttribute)
    assert ripeness.required
    assert ripeness.dynamic
    assert ripeness.has_options_field()

    damage = obj1.add_attribute(encord.objects.common.ChecklistAttribute, "Damage", required=True, dynamic=True)
    assert damage.uid == [1, 8]
    assert damage.feature_node_hash
    assert isinstance(damage, encord.objects.common.ChecklistAttribute)
    assert damage.required
    assert damage.dynamic
    assert damage.has_options_field()


def test_add_object_nested_classifications_duplicate_values():
    ontology = encord.objects.ontology_labels_impl.OntologyStructure()
    obj1 = ontology.add_object("Apple", Shape.BOUNDING_BOX, 1, "#000000", "12345678")

    attr1 = obj1.add_attribute(encord.objects.common.TextAttribute, "Stripes")
    with pytest.raises(ValueError):
        obj1.add_attribute(encord.objects.common.ChecklistAttribute, "Stars, I guess?", local_uid=1)
    with pytest.raises(ValueError):
        obj1.add_attribute(
            encord.objects.common.ChecklistAttribute, "Stars, I guess?", feature_node_hash=attr1.feature_node_hash
        )


def test_add_classification_attribute():
    ontology = encord.objects.ontology_labels_impl.OntologyStructure()
    cls1 = ontology.add_classification()

    clouds = cls1.add_attribute(encord.objects.common.RadioAttribute, "Cloud cover")
    assert clouds.uid == [1, 1]
    assert clouds.feature_node_hash
    assert isinstance(clouds, encord.objects.common.RadioAttribute)
    assert not clouds.required
    assert clouds.has_options_field()

    with pytest.raises(ValueError):  # only one root attribute per classification is allowed
        cls1.add_attribute(encord.objects.common.TextAttribute, "metadata")


def test_build_checkbox_options():
    ontology = encord.objects.ontology_labels_impl.OntologyStructure()
    cls1 = ontology.add_classification()

    clouds = cls1.add_attribute(encord.objects.common.ChecklistAttribute, "Cloud cover")
    one = clouds.add_option("Type One")
    assert one.value == "type_one"
    two = clouds.add_option("Type Two", value="two", local_uid=6)
    assert two.value == "two"
    three = clouds.add_option("Type Three", feature_node_hash="12345678")

    assert len(clouds.options) == 3
    assert len({opt.feature_node_hash for opt in clouds.options}) == 3  # all different
    assert three.uid == [1, 1, 7]

    assert isinstance(one, encord.objects.common.FlatOption)


def test_build_nested_options():
    ontology = encord.objects.ontology_labels_impl.OntologyStructure()
    cls1 = ontology.add_classification()

    clouds = cls1.add_attribute(encord.objects.common.RadioAttribute, "Cloud cover")
    one = clouds.add_option("Type One")
    two = clouds.add_option("Type Two", value="two", local_uid=6)

    assert isinstance(one, encord.objects.common.NestableOption)
    assert isinstance(two, encord.objects.common.NestableOption)

    detail1 = one.add_nested_option(encord.objects.common.RadioAttribute, "detail one")
    detail2 = one.add_nested_option(encord.objects.common.TextAttribute, "detail two")

    detail1value1 = detail1.add_option("value 1")
    assert isinstance(detail1value1, encord.objects.common.NestableOption)
    assert detail1value1.uid == [1, 1, 1, 1, 1]  # five levels: root, 'clouds', 'type one', 'detail one', 'value 1'


def build_expected_ontology():

    ontology = encord.objects.ontology_labels_impl.OntologyStructure()

    eye = ontology.add_object(
        name="Eye",
        color="#D33115",
        shape=encord.objects.common.Shape.BOUNDING_BOX,
        feature_node_hash="a55abbeb",
    )
    nose = ontology.add_object(
        name="Nose",
        color="#E27300",
        shape=encord.objects.common.Shape.POLYGON,
        feature_node_hash="86648f32",
    )
    nose_detail = nose.add_attribute(
        encord.objects.common.ChecklistAttribute,
        feature_node_hash="1e3e5cad",
        name="Additional details about the nose",
        required=True,
    )
    nose_detail.add_option(feature_node_hash="2bc17c88", label="Is it a cute nose?")
    nose_detail.add_option(feature_node_hash="86eaa4f2", label="Is it a wet nose? ")
    example = ontology.add_object(
        name="Example",
        color="#FE9200",
        shape=encord.objects.common.Shape.POLYLINE,
        feature_node_hash="6eeba59b",
    )
    radio = example.add_attribute(
        encord.objects.common.RadioAttribute, feature_node_hash="cabfedb5", name="Radio with options"
    )
    nested = radio.add_option(feature_node_hash="5d102ce6", label="Nested Option")
    leaf = nested.add_nested_option(encord.objects.common.RadioAttribute, feature_node_hash="59204845", name="Leaf")
    cls = ontology.add_classification(feature_node_hash="a39d81c0")
    cat_standing = cls.add_attribute(
        encord.objects.common.RadioAttribute,
        feature_node_hash="a6136d14",
        name="Is the cat standing?",
        required=True,
    )
    cat_standing.add_option(feature_node_hash="a3aeb48d", label="Yes")
    cat_standing.add_option(feature_node_hash="d0a4b373", label="No")

    assert ontology.to_dict() == EXPECTED_ONTOLOGY.to_dict()
