from encord.objects.coordinates import SkeletonCoordinate, SkeletonCoordinates

ontology = {
    "objects": [
        {"id": "1", "name": "Triangle", "color": "#D33115", "shape": "skeleton", "featureNodeHash": "lwsBaDE4"}
    ],
    "classifications": [
        {
            "id": "1",
            "featureNodeHash": "RiMTY4XH",
            "attributes": [
                {
                    "id": "1.1",
                    "name": "Species",
                    "type": "radio",
                    "featureNodeHash": "nwC6m8CY",
                    "required": False,
                    "dynamic": False,
                    "options": [
                        {"id": "1.1.1", "label": "Cat", "value": "Cat", "featureNodeHash": "1dCoCi8n"},
                        {"id": "1.1.2", "label": "Dog", "value": "Dog", "featureNodeHash": "Z9Bb73XM"},
                    ],
                }
            ],
        }
    ],
    "skeleton_templates": [
        {
            "template": {
                "name": "Triangle",
                "width": 0.486,
                "height": 0.32199999999999995,
                "skeleton": {
                    "0": {
                        "x": 0.382,
                        "y": 0.262,
                        "name": "point_0",
                        "color": "#000000",
                        "value": "point_0",
                        "feature_hash": "1wthOoHe",
                    },
                    "1": {
                        "x": 0.21,
                        "y": 0.514,
                        "name": "point_1",
                        "color": "#000000",
                        "value": "point_1",
                        "feature_hash": "KGp1oToz",
                    },
                    "2": {
                        "x": 0.696,
                        "y": 0.584,
                        "name": "point_2",
                        "color": "#000000",
                        "value": "point_2",
                        "feature_hash": "OqR+F4dN",
                    },
                },
                "skeleton_edges": {},
                "feature_node_hash": "lwsBaDE4",
            }
        }
    ],
}

labels = {
    "label_hash": "1286d378-437b-4f9c-9bfa-d0bd29288faf",
    "created_at": "2024-03-05 11:03:21",
    "last_edited_at": "2024-03-11 11:21:41",
    "dataset_hash": "2a8f5434-2fde-478d-9eee-14433113212e",
    "dataset_title": "20 Cats and Dogs",
    "data_title": "9970.jpg",
    "data_hash": "454da3e3-23c4-46c6-9ed4-100d9af5ba33",
    "data_type": "image",
    "is_image_sequence": False,
    "video_link": False,
    "data_units": {
        "454da3e3-23c4-46c6-9ed4-100d9af5ba33": {
            "data_hash": "454da3e3-23c4-46c6-9ed4-100d9af5ba33",
            "data_title": "9970.jpg",
            "data_type": "image/jpeg",
            "data_sequence": 0,
            "labels": {
                "objects": [
                    {
                        "featureHash": "lwsBaDE4",
                        "objectHash": "o7XU+3uz",
                        "name": "Triangle",
                        "value": "triangle",
                        "color": "#D33115",
                        "shape": "skeleton",
                        "confidence": 1,
                        "createdBy": "jim@encord.com",
                        "createdAt": "Mon, 11 Mar 2024 11:21:36 GMT",
                        "skeleton": {
                            "0": {
                                "x": 0.3838,
                                "y": 0.6729,
                                "name": "point_0",
                                "color": "#000000",
                                "value": "point_0",
                                "featureHash": "1wthOoHe",
                            },
                            "1": {
                                "x": 0.4649,
                                "y": 0.8816,
                                "name": "point_1",
                                "color": "#000000",
                                "value": "point_1",
                                "featureHash": "KGp1oToz",
                            },
                            "2": {
                                "x": 0.2356,
                                "y": 0.9396,
                                "name": "point_2",
                                "color": "#000000",
                                "value": "point_2",
                                "featureHash": "OqR+F4dN",
                            },
                        },
                        "manualAnnotation": True,
                    }
                ],
                "classifications": [],
            },
            "data_link": "cord-images-dev/j4uLykcoV8Xe8iogXAKxc95QPQa2/b013a65f-c553-417e-b55a-3f0b9acd5370",
            "width": 500,
            "height": 375,
        }
    },
    "object_answers": {"o7XU+3uz": {"objectHash": "o7XU+3uz", "classifications": []}},
    "classification_answers": {},
    "object_actions": {},
    "label_status": "LABELLED",
}
expected_coordinates = SkeletonCoordinates(
    values=[
        SkeletonCoordinate(
            x=0.3838,
            y=0.6729,
            name="point_0",
            color="#000000",
            feature_hash="1wthOoHe",
            value="point_0",
            visibility=None,
        ),
        SkeletonCoordinate(
            x=0.4649,
            y=0.8816,
            name="point_1",
            color="#000000",
            feature_hash="KGp1oToz",
            value="point_1",
            visibility=None,
        ),
        SkeletonCoordinate(
            x=0.2356,
            y=0.9396,
            name="point_2",
            color="#000000",
            feature_hash="OqR+F4dN",
            value="point_2",
            visibility=None,
        ),
    ],
    name="Triangle",
)
