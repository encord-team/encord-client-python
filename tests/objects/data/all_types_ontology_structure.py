from encord.objects import (
    ChecklistAttribute,
    FlatOption,
    NestableOption,
    Object,
    OntologyStructure,
    RadioAttribute,
    TextAttribute,
)
from encord.objects.common import Shape
from encord.objects.ontology_labels_impl import Classification

all_types_structure = OntologyStructure(
    objects=[
        Object(
            uid=1, name="Box", color="#D33115", shape=Shape.BOUNDING_BOX, feature_node_hash="MjI2NzEy", archived=False, attributes=[]
        ),
        Object(
            uid=2, name="Polygon", color="#E27300", shape=Shape.POLYGON, feature_node_hash="ODkxMzAx", archived=False, attributes=[]
        ),
        Object(
            uid=3, name="Polyline", color="#16406C", shape=Shape.POLYLINE, feature_node_hash="OTcxMzIy", archived=False, attributes=[]
        ),
        Object(
            uid=4,
            name="Keypoint Dynamic Answers",
            color="#FE9200",
            shape=Shape.POINT,
            feature_node_hash="MTY2MTQx",
            archived=False,
            attributes=[
                TextAttribute(
                    uid=[5, 1], feature_node_hash="OTkxMjU1", name="First name", required=False, archived=False, dynamic=True
                ),
                ChecklistAttribute(
                    uid=[5, 2],
                    feature_node_hash="ODcxMDAy",
                    name="Mood",
                    required=False,
                    archived=False,
                    dynamic=True,
                    options=[
                        FlatOption(uid=[5, 2, 1], feature_node_hash="MTE5MjQ3", label="Angry", value="angry", archived=False),
                        FlatOption(uid=[5, 2, 2], feature_node_hash="Nzg3MDE3", label="Sad", value="sad", archived=False),
                    ],
                ),
                RadioAttribute(
                    uid=[6, 1],
                    feature_node_hash="MTExM9I3",
                    name="Radio level 1 ",
                    required=False,
                    archived=False,
                    dynamic=True,
                    options=[
                        NestableOption(
                            uid=[6, 1, 1],
                            feature_node_hash="MT9xNDQ5",
                            label="1 option 1",
                            value="1_option_1",
                            archived=False,
                            nested_options=[
                                TextAttribute(
                                    uid=[6, 1, 1, 1],
                                    feature_node_hash="MjE2O9E0",
                                    name="1 1 text",
                                    required=False,
                                    archived=False,
                                    dynamic=False,
                                )
                            ],
                        ),
                        NestableOption(
                            uid=[6, 1, 2],
                            feature_node_hash="9TcxMjAy",
                            label="1 option 2",
                            value="1_option_2",
                            archived=False,
                            nested_options=[
                                RadioAttribute(
                                    uid=[6, 1, 2, 1],
                                    feature_node_hash="NDYyM9Qx",
                                    name="1 2 radio 1",
                                    required=False,
                                    archived=False,
                                    dynamic=False,
                                    options=[
                                        NestableOption(
                                            uid=[6, 1, 2, 1, 1],
                                            feature_node_hash="MTY0M9U2",
                                            label="1 2 1 option 1",
                                            value="1_2_1_option_1",
                                            archived=False,
                                            nested_options=[],
                                        ),
                                        NestableOption(
                                            uid=[6, 1, 2, 1, 2],
                                            feature_node_hash="MTI49jQy",
                                            label="1 2 1 option ",
                                            value="1_2_1_option_",
                                            archived=False,
                                            nested_options=[],
                                        ),
                                    ],
                                )
                            ],
                        ),
                    ],
                ),
            ],
        ),
        Object(
            uid=5,
            name="Nested Box",
            color="#FCDC00",
            shape=Shape.BOUNDING_BOX,
            feature_node_hash="MTA2MjAx",
            archived=False,
            attributes=[
                TextAttribute(
                    uid=[5, 1], feature_node_hash="OTkxMjU1", name="First name", required=False, archived=False, dynamic=False
                ),
                ChecklistAttribute(
                    uid=[5, 2],
                    feature_node_hash="ODcxMDAy",
                    name="Mood",
                    required=False,
                    archived=False,
                    dynamic=False,
                    options=[
                        FlatOption(uid=[5, 2, 1], feature_node_hash="MTE5MjQ3", label="Angry", value="angry", archived=False),
                        FlatOption(uid=[5, 2, 2], feature_node_hash="Nzg3MDE3", label="Sad", value="sad", archived=False),
                    ],
                ),
            ],
        ),
        Object(
            uid=6,
            name="Deeply Nested Polygon",
            color="#DBDF00",
            shape=Shape.POLYGON,
            feature_node_hash="MTM1MTQy",
            archived=False,
            attributes=[
                TextAttribute(
                    uid=[5, 1], feature_node_hash="OTk555U1", name="First name", required=False, archived=False, dynamic=False
                ),
                ChecklistAttribute(
                    uid=[5, 2],
                    feature_node_hash="ODc555Ay",
                    name="Mood",
                    required=False,
                    archived=False,
                    dynamic=False,
                    options=[
                        FlatOption(uid=[5, 2, 1], feature_node_hash="MT5555Q3", label="Angry", value="angry", archived=False),
                        FlatOption(uid=[5, 2, 2], feature_node_hash="Nzg5555E3", label="Sad", value="sad", archived=False),
                    ],
                ),
                RadioAttribute(
                    uid=[6, 1],
                    feature_node_hash="MTExMjI3",
                    name="Radio level 1 ",
                    required=False,
                    archived=False,
                    dynamic=False,
                    options=[
                        NestableOption(
                            uid=[6, 1, 1],
                            feature_node_hash="MTExNDQ5",
                            label="1 option 1",
                            value="1_option_1",
                            archived=False,
                            nested_options=[
                                TextAttribute(
                                    uid=[6, 1, 1, 1],
                                    feature_node_hash="MjE2OTE0",
                                    name="1 1 text",
                                    required=False,
                                    archived=False,
                                    dynamic=False,
                                )
                            ],
                        ),
                        NestableOption(
                            uid=[6, 1, 2],
                            feature_node_hash="MTcxMjAy",
                            label="1 option 2",
                            value="1_option_2",
                            archived=False,
                            nested_options=[
                                ChecklistAttribute(
                                    uid=[5, 2],
                                    feature_node_hash="ODc666Ay",
                                    name="Mood",
                                    required=False,
                                    archived=False,
                                    dynamic=False,
                                    options=[
                                        FlatOption(
                                            uid=[5, 2, 1], feature_node_hash="MT66665Q3", label="Angry", value="angry", archived=False
                                        ),
                                        FlatOption(
                                            uid=[5, 2, 2], feature_node_hash="Nzg66665E3", label="Sad", value="sad", archived=False
                                        ),
                                    ],
                                )
                            ],
                        ),
                    ],
                ),
            ],
        ),
        Object(
            uid=7,
            name="cone object",
            color="#A4DD00",
            shape=Shape.SKELETON,
            feature_node_hash="MTczNjQx",
            archived=False,
            attributes=[],
        ),
        Object(
            uid=8,
            name="audio object",
            color="#A4FF00",
            shape=Shape.AUDIO,
            feature_node_hash="KVfzNkFy",
            archived=False,
            attributes=[],
        ),
        Object(
            uid=9,
            name="text object",
            color="#A4FF00",
            shape=Shape.TEXT,
            feature_node_hash="textFeatureNodeHash",
            archived=False,
            attributes=[],
        ),
    ],
    classifications=[
        Classification(
            uid=1,
            feature_node_hash="NzIxNTU1",
            attributes=[
                RadioAttribute(
                    uid=[1, 1],
                    feature_node_hash="MjI5MTA5",
                    name="Radio classification 1",
                    required=False,
                    archived=False,
                    dynamic=False,
                    options=[
                        NestableOption(
                            uid=[1, 1, 1],
                            feature_node_hash="MTcwMjM5",
                            label="cl 1 option 1",
                            value="cl_1_option_1",
                            archived=False,
                            nested_options=[],
                        ),
                        NestableOption(
                            uid=[1, 1, 2],
                            feature_node_hash="MjUzMTg1",
                            label="cl 1 option 2",
                            value="cl_1_option_2",
                            archived=False,
                            nested_options=[
                                TextAttribute(
                                    uid=[1, 1, 2, 1],
                                    feature_node_hash="MTg0MjIw",
                                    name="cl 1 2 text",
                                    required=False,
                                    archived=False,
                                    dynamic=False,
                                )
                            ],
                        ),
                    ],
                )
            ],
        ),
        Classification(
            uid=2,
            feature_node_hash="jPOcEsbw",
            attributes=[
                TextAttribute(
                    uid=[2, 1],
                    feature_node_hash="OxrtEM+v",
                    name="Text classification",
                    required=False,
                    archived=False,
                    dynamic=False,
                )
            ],
        ),
        Classification(
            uid=3,
            feature_node_hash="3DuQbFxo",
            attributes=[
                ChecklistAttribute(
                    uid=[3, 1],
                    feature_node_hash="9mwWr3OE",
                    name="Checklist classification",
                    required=False,
                    archived=False,
                    dynamic=False,
                    options=[
                        FlatOption(
                            uid=[3, 1, 1],
                            feature_node_hash="fvLjF0qZ",
                            label="Checklist classification answer 1",
                            value="checklist_classification_answer_1",
                            archived=False,
                        ),
                        FlatOption(
                            uid=[3, 1, 2],
                            feature_node_hash="a4r7nK9i",
                            label="Checklist classification answer 2",
                            value="checklist_classification_answer_2",
                            archived=False,
                        ),
                    ],
                )
            ],
        ),
    ],
)
