EDITOR_BLOB = {
    "objects": [
        {
            "id": "1",
            "name": "Eye",
            "color": "#D33115",
            "shape": "bounding_box",
            "featureNodeHash": "a55abbeb",
            "required": False,
            "archived": False,
        },
        {
            "id": "2",
            "name": "Nose",
            "color": "#E27300",
            "shape": "polygon",
            "featureNodeHash": "86648f32",
            "required": False,
            "archived": False,
            "attributes": [
                {
                    "id": "2.1",
                    "name": "Additional details about the nose",
                    "type": "checklist",
                    "featureNodeHash": "1e3e5cad",
                    "required": True,
                    "archived": False,
                    "dynamic": False,
                    "options": [
                        {
                            "id": "2.1.1",
                            "label": "Is it a cute nose?",
                            "value": "is_it_a_cute_nose?",
                            "featureNodeHash": "2bc17c88",
                            "archived": False,
                        },
                        {
                            "id": "2.1.2",
                            "label": "Is it a wet nose? ",
                            "value": "is_it_a_wet_nose?_",
                            "featureNodeHash": "86eaa4f2",
                            "archived": False,
                        },
                    ],
                }
            ],
        },
        {
            "id": "3",
            "name": "Example",
            "color": "#FE9200",
            "shape": "polyline",
            "featureNodeHash": "6eeba59b",
            "required": False,
            "archived": False,
            "attributes": [
                {
                    "id": "4.1",
                    "name": "Radio with options",
                    "type": "radio",
                    "featureNodeHash": "cabfedb5",
                    "required": False,
                    "archived": False,
                    "dynamic": False,
                    "options": [
                        {
                            "id": "4.1.1",
                            "label": "Nested Option",
                            "value": "nested_option",
                            "featureNodeHash": "5d102ce6",
                            "archived": False,
                            "options": [
                                {
                                    "id": "4.1.1.1",
                                    "name": "Leaf",
                                    "type": "radio",
                                    "featureNodeHash": "59204845",
                                    "required": False,
                                    "archived": False,
                                    "dynamic": False,
                                }
                            ],
                        }
                    ],
                }
            ],
        },
    ],
    "classifications": [
        {
            "id": "1",
            "featureNodeHash": "a39d81c0",
            "attributes": [
                {
                    "id": "1.1",
                    "name": "Is the cat standing?",
                    "type": "radio",
                    "featureNodeHash": "a6136d14",
                    "required": True,
                    "archived": False,
                    "dynamic": False,
                    "options": [
                        {
                            "id": "1.1.1",
                            "label": "Yes",
                            "value": "yes",
                            "featureNodeHash": "a3aeb48d",
                            "archived": False,
                        },
                        {"id": "1.1.2", "label": "No", "value": "no", "featureNodeHash": "d0a4b373", "archived": False},
                    ],
                }
            ],
        }
    ],
    "skeleton_templates": [
        {
            "template": {
                "name": "Line",
                "shape": "skeleton",
                "width": 100.0,
                "height": 100.0,
                "skeleton": {
                    "0": {"x": 0.0, "y": 0.0, "name": "point_0", "color": "#00000", "value": ""},
                    "1": {"x": 1.0, "y": 1.0, "name": "point_1", "color": "#00000", "value": ""},
                },
                "skeletonEdges": {"0": {"1": {"color": "#00000"}}},
                "feature_node_hash": "c67522ee",
            }
        }
    ],
}
