import json
import os

import encord.objects.classification
import encord.objects.common
import encord.objects.ontology_object
from encord.objects import ontology

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CURRENT_DIR, "data")

EXPECTED_ONTOLOGY: ontology.Ontology = ontology.Ontology(
    objects=[
        encord.objects.ontology_object.Object(
            uid=1,
            name="Eye",
            color="#D33115",
            shape=encord.objects.common.Shape.BOUNDING_BOX,
            feature_node_hash="a55abbeb",
        ),
        encord.objects.ontology_object.Object(
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
        encord.objects.ontology_object.Object(
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
                                )
                            ],
                        )
                    ],
                )
            ],
        ),
    ],
    classifications=[
        encord.objects.classification.Classification(
            uid=1,
            feature_node_hash="a39d81c0",
            attributes=[
                encord.objects.common.RadioAttribute(
                    uid=[1, 1],
                    feature_node_hash="a6136d14",
                    name="Is the cat standing?",
                    required=True,
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


def test_json_to_ontology():
    # GIVEN
    file_path = os.path.join(DATA_DIR, "editor_blob.json")
    with open(file_path, "r", encoding="utf8") as f:
        editor_dict = json.load(f)

    # WHEN
    actual = ontology.Ontology.from_dict(editor_dict)

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
