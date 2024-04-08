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
    "is_valid": True,
    "export_hash": "8e64c5ec-b1ec-4108-aeed-39b5ccf7d92f",
    "exported_at": "Mon, 08 Apr 2024 12:58:21 UTC",
    "export_history": [
        {
            "export_hash": "8e64c5ec-b1ec-4108-aeed-39b5ccf7d92f",
            "exported_at": "Mon, 08 Apr 2024 12:58:21 UTC",
            "user_email": "jim@encord.com",
        },
        {
            "export_hash": "d650931e-6886-46e3-8e96-eba4134b9d7c",
            "exported_at": "Mon, 08 Apr 2024 12:55:02 UTC",
            "user_email": "jim@encord.com",
        },
        {
            "export_hash": "bf1e3e0a-7fec-4532-894b-7d54c5bcb130",
            "exported_at": "Mon, 08 Apr 2024 12:45:06 UTC",
            "user_email": "jim@encord.com",
        },
        {
            "export_hash": "44824e9a-8810-4c63-a71e-4177f7828561",
            "exported_at": "Mon, 08 Apr 2024 12:44:38 UTC",
            "user_email": "jim@encord.com",
        },
        {
            "export_hash": "abb24677-9ecb-475d-9ea9-c95908298bb1",
            "exported_at": "Mon, 08 Apr 2024 12:42:28 UTC",
            "user_email": "jim@encord.com",
        },
        {
            "export_hash": "d6918565-3781-4f35-9794-f761eaee238a",
            "exported_at": "Mon, 08 Apr 2024 12:40:27 UTC",
            "user_email": "jim@encord.com",
        },
        {
            "export_hash": "d9baf44e-18dd-4902-8b96-e7acab648a16",
            "exported_at": "Mon, 08 Apr 2024 12:34:47 UTC",
            "user_email": "jim@encord.com",
        },
        {
            "export_hash": "cb914996-c053-4a26-ab70-881d5600b198",
            "exported_at": "Wed, 03 Apr 2024 16:38:50 UTC",
            "user_email": "jim@encord.com",
        },
        {
            "export_hash": "3b1692e2-9477-4c0c-9b94-6495bc43a8b8",
            "exported_at": "Wed, 03 Apr 2024 15:34:47 UTC",
            "user_email": "jim@encord.com",
        },
    ],
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
