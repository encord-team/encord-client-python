dynamic_classifications_ontology = {
    "objects": [
        {
            "id": "1",
            "name": "Person",
            "color": "#D33115",
            "shape": "bounding_box",
            "featureNodeHash": "f7c6dc2a",
            "attributes": [
                {
                    "id": "1.1",
                    "name": "Movement Type",
                    "type": "radio",
                    "featureNodeHash": "9a29da90",
                    "required": False,
                    "dynamic": False,
                    "options": [
                        {"id": "1.1.1", "label": "walking", "value": "walking", "featureNodeHash": "64e689a6"},
                        {"id": "1.1.2", "label": "cycling", "value": "cycling", "featureNodeHash": "4862bd65"},
                    ],
                },
                {
                    "id": "1.2",
                    "name": "Additional Notes",
                    "type": "checklist",
                    "featureNodeHash": "3ae45a8d",
                    "required": False,
                    "dynamic": False,
                    "options": [
                        {"id": "1.2.1", "label": "occluded", "value": "occluded", "featureNodeHash": "17adb71a"},
                        {"id": "1.2.2", "label": "rushing", "value": "rushing", "featureNodeHash": "b1ae2585"},
                        {"id": "1.2.3", "label": "stylish", "value": "stylish", "featureNodeHash": "ecd4ed1c"},
                        {
                            "id": "1.2.4",
                            "label": "bad hair day",
                            "value": "bad_hair_day",
                            "featureNodeHash": "cc6d2c41",
                        },
                    ],
                },
            ],
        },
        {"id": "2", "name": "Planter", "color": "#E27300", "shape": "polyline", "featureNodeHash": "ba864672"},
        {
            "id": "3",
            "name": "person_1static_rb",
            "color": "#16406C",
            "shape": "bounding_box",
            "featureNodeHash": "4eef58f9",
            "attributes": [
                {
                    "id": "3.1",
                    "name": "direction",
                    "type": "radio",
                    "featureNodeHash": "c32eeab3",
                    "required": False,
                    "dynamic": False,
                    "options": [
                        {"id": "3.1.1", "label": "north", "value": "north", "featureNodeHash": "2f881565"},
                        {"id": "3.1.2", "label": "south", "value": "south", "featureNodeHash": "1ffadf57"},
                        {"id": "3.1.3", "label": "east", "value": "east", "featureNodeHash": "222e26c3"},
                        {"id": "3.1.4", "label": "west", "value": "west", "featureNodeHash": "458cc372"},
                    ],
                }
            ],
        },
        {
            "id": "4",
            "name": "person_2static_rb-c2",
            "color": "#FE9200",
            "shape": "bounding_box",
            "featureNodeHash": "24b28026",
            "attributes": [
                {
                    "id": "4.1",
                    "name": "direction",
                    "type": "radio",
                    "featureNodeHash": "ddbbd49a",
                    "required": False,
                    "dynamic": False,
                    "options": [
                        {"id": "4.1.1", "label": "north", "value": "north", "featureNodeHash": "0feaacba"},
                        {"id": "4.1.2", "label": "south", "value": "south", "featureNodeHash": "07f9072b"},
                        {"id": "4.1.3", "label": "east", "value": "east", "featureNodeHash": "d0f62c2f"},
                        {"id": "4.1.4", "label": "west", "value": "west", "featureNodeHash": "5f6d8e02"},
                    ],
                },
                {
                    "id": "4.2",
                    "name": "weather",
                    "type": "checklist",
                    "featureNodeHash": "eb1354e8",
                    "required": False,
                    "dynamic": False,
                    "options": [
                        {"id": "4.2.1", "label": "cold", "value": "cold", "featureNodeHash": "ef4c1ad1"},
                        {"id": "4.2.2", "label": "rainy", "value": "rainy", "featureNodeHash": "ea79ea06"},
                    ],
                },
            ],
        },
        {
            "id": "5",
            "name": "person_1dynamic_c1",
            "color": "#FCDC00",
            "shape": "bounding_box",
            "featureNodeHash": "2689db00",
            "attributes": [
                {
                    "id": "5.1",
                    "name": "is occluded?",
                    "type": "checklist",
                    "featureNodeHash": "f72182d1",
                    "required": False,
                    "dynamic": True,
                    "options": [{"id": "5.1.1", "label": "yes", "value": "yes", "featureNodeHash": "25a13ecf"}],
                }
            ],
        },
        {
            "id": "6",
            "name": "person_2d_c2-rb_1s_c2",
            "color": "#DBDF00",
            "shape": "bounding_box",
            "featureNodeHash": "e3df24b2",
            "attributes": [
                {
                    "id": "6.1",
                    "name": "transport mode",
                    "type": "radio",
                    "featureNodeHash": "fb6ec612",
                    "required": False,
                    "dynamic": True,
                    "options": [
                        {"id": "6.1.1", "label": "walking", "value": "walking", "featureNodeHash": "92d9577b"},
                        {"id": "6.1.2", "label": "biking", "value": "biking", "featureNodeHash": "49a886c5"},
                        {"id": "6.1.3", "label": "running", "value": "running", "featureNodeHash": "f100c80b"},
                    ],
                },
                {
                    "id": "6.2",
                    "name": "style",
                    "type": "checklist",
                    "featureNodeHash": "0d655d00",
                    "required": False,
                    "dynamic": True,
                    "options": [
                        {"id": "6.2.1", "label": "hat", "value": "hat", "featureNodeHash": "cfb48734"},
                        {"id": "6.2.2", "label": "cape", "value": "cape", "featureNodeHash": "5a472494"},
                    ],
                },
                {
                    "id": "6.3",
                    "name": "disposition",
                    "type": "radio",
                    "featureNodeHash": "202a17a1",
                    "required": False,
                    "dynamic": False,
                    "options": [
                        {"id": "6.3.1", "label": "rushed", "value": "rushed", "featureNodeHash": "b5ab800a"},
                        {"id": "6.3.2", "label": "relaxed", "value": "relaxed", "featureNodeHash": "6b1d2e2b"},
                    ],
                },
            ],
        },
        {
            "id": "7",
            "name": "person multi nesting",
            "color": "#A4DD00",
            "shape": "bounding_box",
            "featureNodeHash": "E9/drcG3",
            "attributes": [
                {
                    "id": "7.1",
                    "name": "radio 1",
                    "type": "radio",
                    "featureNodeHash": "s/5gT5qv",
                    "required": False,
                    "dynamic": True,
                    "options": [
                        {
                            "id": "7.1.1",
                            "label": "radio 1 a",
                            "value": "radio_1_a",
                            "featureNodeHash": "wpRmKCaB",
                            "options": [
                                {
                                    "id": "7.1.1.1",
                                    "name": "radio 1 a 1",
                                    "type": "radio",
                                    "featureNodeHash": "jhH2nW6O",
                                    "required": False,
                                    "dynamic": False,
                                    "options": [
                                        {
                                            "id": "7.1.1.1.1",
                                            "label": "radio 1 a 1 a",
                                            "value": "radio_1_a_1_a",
                                            "featureNodeHash": "aMxJzb/r",
                                        },
                                        {
                                            "id": "7.1.1.1.2",
                                            "label": "radio 1 a 1 b",
                                            "value": "radio_1_a_1_b",
                                            "featureNodeHash": "UlCprGFA",
                                        },
                                    ],
                                },
                                {
                                    "id": "7.1.1.2",
                                    "name": "radio 1 a 2",
                                    "type": "radio",
                                    "featureNodeHash": "eLMUHX6I",
                                    "required": False,
                                    "dynamic": False,
                                    "options": [
                                        {
                                            "id": "7.1.1.2.1",
                                            "label": "radio 1 a 2 a ",
                                            "value": "radio_1_a_2_a_",
                                            "featureNodeHash": "4G0r787k",
                                        },
                                        {
                                            "id": "7.1.1.2.2",
                                            "label": "radio 1 a 2 b",
                                            "value": "radio_1_a_2_b",
                                            "featureNodeHash": "aBwN4CKp",
                                        },
                                    ],
                                },
                            ],
                        },
                        {"id": "7.1.2", "label": "radio 1 b", "value": "radio_1_b", "featureNodeHash": "8RodRC2J"},
                    ],
                },
                {
                    "id": "7.2",
                    "name": "checklist 1",
                    "type": "checklist",
                    "featureNodeHash": "+24n0UIq",
                    "required": False,
                    "dynamic": True,
                    "options": [
                        {
                            "id": "7.2.1",
                            "label": "checklist 1 a ",
                            "value": "checklist_1_a_",
                            "featureNodeHash": "4WDDzSmi",
                        },
                        {
                            "id": "7.2.2",
                            "label": "checklist 1 b",
                            "value": "checklist_1_b",
                            "featureNodeHash": "GnJxM/8O",
                        },
                    ],
                },
            ],
        },
    ],
    "classifications": [
        {
            "id": "1",
            "featureNodeHash": "44b05516",
            "attributes": [
                {
                    "id": "1.1",
                    "name": "has_people?",
                    "type": "radio",
                    "featureNodeHash": "eb65e33b",
                    "required": False,
                    "dynamic": False,
                    "options": [
                        {"id": "1.1.1", "label": "yes", "value": "yes", "featureNodeHash": "42e1ffe9"},
                        {"id": "1.1.2", "label": "no", "value": "no", "featureNodeHash": "9105fe4c"},
                    ],
                }
            ],
        }
    ],
}
