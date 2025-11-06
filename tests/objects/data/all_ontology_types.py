global_classification_dict = {  # should match GLOBAL_CLASSIFICATION.to_dict()
    "id": "4",
    "featureNodeHash": "3DuQbFx4",
    "level": "global",
    "attributes": [
        {
            "id": "4.1",
            "name": "Global classification",
            "type": "checklist",
            "featureNodeHash": "2mwWr3Of",
            "required": False,
            "dynamic": False,
            "archived": False,
            "options": [
                {
                    "id": "4.1.1",
                    "label": "Global Answer 1",
                    "value": "global_answer_1",
                    "featureNodeHash": "3vLjF0q1",
                    "archived": False,
                },
                {
                    "id": "4.1.2",
                    "label": "Global Answer 2",
                    "value": "checklist_classification_answer_2",
                    "featureNodeHash": "74r7nK9e",
                    "archived": False,
                },
            ],
        }
    ],
}

all_ontology_types = {
    "objects": [
        {"id": "1", "name": "Box", "color": "#D33115", "shape": "bounding_box", "featureNodeHash": "MjI2NzEy"},
        {"id": "2", "name": "Polygon", "color": "#E27300", "shape": "polygon", "featureNodeHash": "ODkxMzAx"},
        {"id": "3", "name": "Polyline", "color": "#16406C", "shape": "polyline", "featureNodeHash": "OTcxMzIy"},
        {"id": "4", "name": "Keypoint", "color": "#FE9200", "shape": "point", "featureNodeHash": "MTY2MTQx"},
        {
            "id": "5",
            "name": "Nested Box",
            "color": "#FCDC00",
            "shape": "bounding_box",
            "featureNodeHash": "MTA2MjAx",
            "attributes": [
                {
                    "id": "5.1",
                    "name": "First name",
                    "type": "text",
                    "featureNodeHash": "OTkxMjU1",
                    "required": False,
                    "dynamic": False,
                },
                {
                    "id": "5.2",
                    "name": "Mood",
                    "type": "checklist",
                    "featureNodeHash": "ODcxMDAy",
                    "required": False,
                    "dynamic": False,
                    "options": [
                        {"id": "5.2.1", "label": "Angry", "value": "angry", "featureNodeHash": "MTE5MjQ3"},
                        {"id": "5.2.2", "label": "Sad", "value": "sad", "featureNodeHash": "Nzg3MDE3"},
                    ],
                },
            ],
        },
        {
            "id": "6",
            "name": "Deeply Nested Polygon",
            "color": "#DBDF00",
            "shape": "polygon",
            "featureNodeHash": "MTM1MTQy",
            "attributes": [
                {
                    "id": "6.1",
                    "name": "Radio level 1 ",
                    "type": "radio",
                    "featureNodeHash": "MTExMjI3",
                    "required": False,
                    "dynamic": False,
                    "options": [
                        {
                            "id": "6.1.1",
                            "label": "1 option 1",
                            "value": "1_option_1",
                            "featureNodeHash": "MTExNDQ5",
                            "options": [
                                {
                                    "id": "6.1.1.1",
                                    "name": "1 1 text",
                                    "type": "text",
                                    "featureNodeHash": "MjE2OTE0",
                                    "required": False,
                                    "dynamic": False,
                                }
                            ],
                        },
                        {
                            "id": "6.1.2",
                            "label": "1 option 2",
                            "value": "1_option_2",
                            "featureNodeHash": "MTcxMjAy",
                            "options": [
                                {
                                    "id": "6.1.2.1",
                                    "name": "1 2 radio 1",
                                    "type": "radio",
                                    "featureNodeHash": "NDYyMjQx",
                                    "required": False,
                                    "dynamic": False,
                                    "options": [
                                        {
                                            "id": "6.1.2.1.1",
                                            "label": "1 2 1 option 1",
                                            "value": "1_2_1_option_1",
                                            "featureNodeHash": "MTY0MzU2",
                                        },
                                        {
                                            "id": "6.1.2.1.2",
                                            "label": "1 2 1 option ",
                                            "value": "1_2_1_option_",
                                            "featureNodeHash": "MTI4MjQy",
                                        },
                                    ],
                                }
                            ],
                        },
                    ],
                }
            ],
        },
        {"id": "7", "name": "cone object", "color": "#A4DD00", "shape": "skeleton", "featureNodeHash": "MTczNjQx"},
        {"id": "8", "name": "audio 1", "color": "#A4DD00", "shape": "audio", "featureNodeHash": "9dt+r+op"},
        {"id": "9", "name": "audio 2", "color": "#A4DD00", "shape": "audio", "featureNodeHash": "VDeQk05m"},
        {"id": "10", "name": "audio 3", "color": "#A4DD00", "shape": "audio", "featureNodeHash": "bjvtzFgi"},
        {"id": "11", "name": "audio 4", "color": "#A4DD00", "shape": "audio", "featureNodeHash": "3X3+Ydcy"},
        {
            "id": "12",
            "name": "text object",
            "color": "#A4DD00",
            "shape": "text",
            "featureNodeHash": "textObjectFeatureNodeHash",
        },
    ],
    "classifications": [
        {
            "id": "1",
            "featureNodeHash": "NzIxNTU1",
            "attributes": [
                {
                    "id": "1.1",
                    "name": "Radio classification 1",
                    "type": "radio",
                    "featureNodeHash": "MjI5MTA5",
                    "required": False,
                    "dynamic": False,
                    "options": [
                        {
                            "id": "1.1.1",
                            "label": "cl 1 option 1",
                            "value": "cl_1_option_1",
                            "featureNodeHash": "MTcwMjM5",
                        },
                        {
                            "id": "1.1.2",
                            "label": "cl 1 option 2",
                            "value": "cl_1_option_2",
                            "featureNodeHash": "MjUzMTg1",
                            "options": [
                                {
                                    "id": "1.1.2.1",
                                    "name": "cl 1 2 text",
                                    "type": "text",
                                    "featureNodeHash": "MTg0MjIw",
                                    "required": False,
                                    "dynamic": False,
                                }
                            ],
                        },
                    ],
                }
            ],
        },
        {
            "id": "2",
            "featureNodeHash": "jPOcEsbw",
            "attributes": [
                {
                    "id": "2.1",
                    "name": "Text classification",
                    "type": "text",
                    "featureNodeHash": "OxrtEM+v",
                    "required": False,
                    "dynamic": False,
                }
            ],
        },
        {
            "id": "3",
            "featureNodeHash": "3DuQbFxo",
            "attributes": [
                {
                    "id": "3.1",
                    "name": "Checklist classification",
                    "type": "checklist",
                    "featureNodeHash": "9mwWr3OE",
                    "required": False,
                    "dynamic": False,
                    "options": [
                        {
                            "id": "3.1.1",
                            "label": "Checklist classification answer 1",
                            "value": "checklist_classification_answer_1",
                            "featureNodeHash": "fvLjF0qZ",
                        },
                        {
                            "id": "3.1.2",
                            "label": "Checklist classification answer 2",
                            "value": "checklist_classification_answer_2",
                            "featureNodeHash": "a4r7nK9i",
                        },
                    ],
                }
            ],
        },
        global_classification_dict,
    ],
}
