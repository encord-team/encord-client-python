from encord.objects.coordinates import SkeletonCoordinate, SkeletonCoordinates, Visibility

ontology = {
    "objects": [{"id": "1", "name": "Square", "color": "#D33115", "shape": "skeleton", "featureNodeHash": "lwsBaDE5"}],
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
                "name": "Square",
                "shape": "skeleton",
                "width": 0.23513107100307273,
                "height": 0.25,
                "skeleton": {
                    "0": {
                        "x": 0.5148689289969273,
                        "y": 0.5,
                        "name": "point_0",
                        "color": "#000000",
                        "value": "point_0",
                        "featureHash": "A9sGmBca",
                    },
                    "1": {
                        "x": 0.75,
                        "y": 0.5,
                        "name": "point_1",
                        "color": "#000000",
                        "value": "point_1",
                        "featureHash": "UWKgC/Db",
                    },
                    "2": {
                        "x": 0.675,
                        "y": 0.25,
                        "name": "point_2",
                        "color": "#000000",
                        "value": "point_2",
                        "featureHash": "mBt9AAhc",
                    },
                    "3": {
                        "x": 0.675,
                        "y": 0.25,
                        "name": "point_3",
                        "color": "#000000",
                        "value": "point_3",
                        "featureHash": "mBt9AAhd",
                    },
                },
                "skeletonEdges": {
                    "0": {"1": {"color": "#000000"}},
                    "1": {"2": {"color": "#000000"}},
                    "2": {"3": {"color": "#000000"}},
                    "3": {"0": {"color": "#000000"}},
                },
                "feature_node_hash": "lwsBaDE5",
            }
        },
    ],
}

labels = {
    "label_hash": "1286d378-437b-4f9c-9bfa-d0bd29288faf",
    "branch_name": "main",
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
                        "featureHash": "lwsBaDE5",
                        "objectHash": "o7XU+3ux",
                        "name": "Square",
                        "value": "square",
                        "color": "#D33115",
                        "shape": "skeleton",
                        "confidence": 1,
                        "createdBy": "jim@encord.com",
                        "createdAt": "Mon, 11 Mar 2024 11:21:36 GMT",
                        "skeleton": {
                            "0": {
                                "x": 0.3,
                                "y": 0.3,
                                "name": "point_0",
                                "color": "#000000",
                                "value": "point_0",
                                "featureHash": "A9sGmBca",
                                "visibility": "visible",
                            },
                            "1": {
                                "x": 0.7,
                                "y": 0.3,
                                "name": "point_1",
                                "color": "#000000",
                                "value": "point_1",
                                "featureHash": "UWKgC/Db",
                                "visibility": "occluded",
                            },
                            "2": {
                                "x": 0.7,
                                "y": 0.7,
                                "name": "point_2",
                                "color": "#000000",
                                "value": "point_2",
                                "featureHash": "mBt9AAhc",
                                "visibility": "invisible",
                            },
                            "3": {
                                "x": 0.3,
                                "y": 0.7,
                                "name": "point_3",
                                "color": "#000000",
                                "value": "point_3",
                                "featureHash": "mBt9AAhd",
                                "visibility": "selfOccluded",
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
            visibility=Visibility.VISIBLE,
        ),
        SkeletonCoordinate(
            x=0.4649,
            y=0.8816,
            name="point_1",
            color="#000000",
            feature_hash="KGp1oToz",
            value="point_1",
            visibility=Visibility.OCCLUDED,
        ),
        SkeletonCoordinate(
            x=0.2356,
            y=0.9396,
            name="point_2",
            color="#000000",
            feature_hash="OqR+F4dN",
            value="point_2",
            visibility=Visibility.INVISIBLE,
        ),
    ],
    name="Triangle",
)

expected_coordinates_square = SkeletonCoordinates(
    values=[
        SkeletonCoordinate(
            x=0.3,
            y=0.3,
            name="point_0",
            color="#000000",
            feature_hash="A9sGmBca",
            value="point_0",
            visibility=Visibility.VISIBLE,
        ),
        SkeletonCoordinate(
            x=0.7,
            y=0.3,
            name="point_1",
            color="#000000",
            feature_hash="UWKgC/Db",
            value="point_1",
            visibility=Visibility.OCCLUDED,
        ),
        SkeletonCoordinate(
            x=0.7,
            y=0.7,
            name="point_2",
            color="#000000",
            feature_hash="mBt9AAhc",
            value="point_2",
            visibility=Visibility.INVISIBLE,
        ),
        SkeletonCoordinate(
            x=0.3,
            y=0.7,
            name="point_3",
            color="#000000",
            feature_hash="mBt9AAhd",
            value="point_3",
            visibility=Visibility.SELF_OCCLUDED,
        ),
    ],
    name="Square",
)
