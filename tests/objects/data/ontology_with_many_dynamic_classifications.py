ontology = {
    "objects": [
        {
            "id": "1",
            "name": "box",
            "color": "#D33115",
            "shape": "bounding_box",
            "featureNodeHash": "LJNV5PVK",
            "attributes": [
                {
                    "id": "1.1",
                    "name": "dynamic text",
                    "type": "text",
                    "featureNodeHash": "5RGh3YIU",
                    "required": False,
                    "dynamic": True,
                },
                {
                    "id": "1.2",
                    "name": "dynamic classification",
                    "type": "checklist",
                    "featureNodeHash": "ZJoiBceM",
                    "required": False,
                    "dynamic": True,
                    "options": [
                        {
                            "id": "1.2.1",
                            "label": "classification 1",
                            "value": "classification_1",
                            "featureNodeHash": "aOQGJvce",
                        },
                        {
                            "id": "1.2.2",
                            "label": "classification 2",
                            "value": "classification_2",
                            "featureNodeHash": "tyjScPrk",
                        },
                    ],
                },
                {
                    "id": "1.3",
                    "name": "dynamic radio",
                    "type": "radio",
                    "featureNodeHash": "OMpf1zPf",
                    "required": False,
                    "dynamic": True,
                    "options": [
                        {"id": "1.3.1", "label": "radio 1", "value": "radio_1", "featureNodeHash": "ps0dwXfI"},
                        {"id": "1.3.2", "label": "radio 2", "value": "radio_2", "featureNodeHash": "IwCHSdeL"},
                    ],
                },
            ],
        },
        {
            "id": "2",
            "name": "box 2",
            "color": "#E27300",
            "shape": "bounding_box",
            "featureNodeHash": "GaAKWvvg",
            "attributes": [
                {
                    "id": "2.1",
                    "name": "radio 2",
                    "type": "radio",
                    "featureNodeHash": "TWPByH4G",
                    "required": False,
                    "dynamic": True,
                    "options": [
                        {"id": "2.1.1", "label": "radio 2 1", "value": "radio_2_1", "featureNodeHash": "zhrqAYjQ"},
                        {"id": "2.1.2", "label": "radio 2 2", "value": "radio_2_2", "featureNodeHash": "J/I/karX"},
                    ],
                }
            ],
        },
    ],
    "classifications": [],
}
