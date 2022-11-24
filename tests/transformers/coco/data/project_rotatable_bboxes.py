from encord.objects.classification import Classification
from encord.objects.common import (
    ChecklistAttribute,
    FlatOption,
    NestableOption,
    RadioAttribute,
    Shape,
)
from encord.objects.ontology_object import Object
from encord.objects.ontology_structure import OntologyStructure

labels_rotatable_bboxes = {
    "label_hash": "5c341e8b-6f50-4a05-b636-5f6575063565",
    "dataset_hash": "ce19e958-1355-463d-aee5-3f64fef1ab0a",
    "dataset_title": "cvat import pizza",
    "data_title": "image-group-27e19",
    "data_type": "img_group",
    "data_units": {
        "8834e4f8-1d50-464c-baca-1717f970612d": {
            "data_hash": "8834e4f8-1d50-464c-baca-1717f970612d",
            "data_title": "Hawaiian Pizza.jpg",
            "data_link": "https://storage.googleapis.com/encord-local-dev.appspot.com/cord-images-dev/lFW59RQ9jcT4vHZeG14m8QWJKug1/8834e4f8-1d50-464c-baca-1717f970612d?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=firebase-adminsdk-efw44%40encord-local-dev.iam.gserviceaccount.com%2F20221111%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20221111T141510Z&X-Goog-Expires=604800&X-Goog-SignedHeaders=host&X-Goog-Signature=ac8e7f7fe9c159309f4574434b78101446c3dcf5c00609cf2e0a20c36dd29d23d9c586684827f92bedebc4bcfe75d8c402bcb59a3196beb67d5593436c190963ffbea5bdf9fda8a34242aa6a5e026e8a41a113db1629ef2321c194cbbf79ac239f9385e8eadfc37b24b68f843de9957e407950ea48fcc4d2584039d962be5b71ab7e5a67787c1fa77bdf8f25bf6da359ff21108e650fe7845a30adece188906d9fc3610f58c461c51fdd377536729cc405189f5268f8af9cb9b92fc827ff2c962236e15f96b6c5aef49eb1ff85ed6ed302e93cd8a159165dc67e57a702e11dccd856cd0b986fcb502c95d87bffc8f11f0b7dffab734521b879098347e1418028",
            "data_type": "image/jpg",
            "data_sequence": "0",
            "width": 540,
            "height": 841,
            "labels": {
                "objects": [
                    {
                        "name": "Pineapple",
                        "color": "#202020",
                        "shape": "rotatable_bounding_box",
                        "value": "pineapple",
                        "createdAt": "Thu, 06 Jan 2022 11:01:52 UTC",
                        "createdBy": "denis@cord.tech",
                        "confidence": 1,
                        "objectHash": "2a66ba97-3e6c-48c1-bb49-052d00f523a0",
                        "featureHash": "0a58701c-07bf-4005-b561-fdfa5be4cf14",
                        "manualAnnotation": True,
                        "rotatableBoundingBox": {
                            "h": 0.0524,
                            "w": 0.1426,
                            "x": 0.5892,
                            "y": 0.0581,
                            "theta": 218.2,
                        },
                        "reviews": [],
                    },
                    {
                        "name": "Pineapple",
                        "color": "#202020",
                        "shape": "rotatable_bounding_box",
                        "value": "pineapple",
                        "createdAt": "Thu, 06 Jan 2022 11:01:52 UTC",
                        "createdBy": "denis@cord.tech",
                        "confidence": 1,
                        "objectHash": "ada3228c-2bd3-49cb-b18a-f7433c68b7c0",
                        "featureHash": "0a58701c-07bf-4005-b561-fdfa5be4cf14",
                        "manualAnnotation": True,
                        "rotatableBoundingBox": {"h": 0.0927, "w": 0.066, "x": 0.5371, "y": 0.707, "theta": 0},
                        "reviews": [],
                    },
                    {
                        "name": "Pineapple",
                        "color": "#202020",
                        "shape": "rotatable_bounding_box",
                        "value": "pineapple",
                        "createdAt": "Thu, 06 Jan 2022 11:01:52 UTC",
                        "createdBy": "denis@cord.tech",
                        "confidence": 1,
                        "objectHash": "38c6fe5b-dd58-4399-a6cb-74035c2dec58",
                        "featureHash": "0a58701c-07bf-4005-b561-fdfa5be4cf14",
                        "manualAnnotation": True,
                        "rotatableBoundingBox": {"h": 0.0644, "w": 0.0729, "x": 0.6086, "y": 0.7079, "theta": 0},
                        "reviews": [],
                    },
                    {
                        "name": "Pineapple",
                        "color": "#202020",
                        "shape": "rotatable_bounding_box",
                        "value": "pineapple",
                        "createdAt": "Thu, 06 Jan 2022 11:01:52 UTC",
                        "createdBy": "denis@cord.tech",
                        "confidence": 1,
                        "objectHash": "f2db9e47-1edb-442b-94bf-023462a787c1",
                        "featureHash": "0a58701c-07bf-4005-b561-fdfa5be4cf14",
                        "manualAnnotation": True,
                        "rotatableBoundingBox": {
                            "h": 0.0623,
                            "w": 0.1227,
                            "x": 0.1518,
                            "y": 0.0641,
                            "theta": 349.8,
                        },
                        "reviews": [],
                    },
                ],
                "classifications": [
                    {
                        "name": "Tastiness Classification",
                        "value": "tastiness_classification",
                        "createdAt": "Thu, 06 Jan 2022 11:01:52 UTC",
                        "createdBy": "denis@cord.tech",
                        "confidence": 1,
                        "featureHash": "fd38edb3-5b3b-48bd-becd-894b7fa6a325",
                        "classificationHash": "dbc12c85-fd0e-489b-b812-945fb0a9c8b2",
                        "manualAnnotation": True,
                        "reviews": [],
                    }
                ],
            },
        }
    },
    "object_answers": {
        "2a66ba97-3e6c-48c1-bb49-052d00f523a0": {
            "objectHash": "2a66ba97-3e6c-48c1-bb49-052d00f523a0",
            "classifications": [],
        },
        "ada3228c-2bd3-49cb-b18a-f7433c68b7c0": {
            "objectHash": "ada3228c-2bd3-49cb-b18a-f7433c68b7c0",
            "classifications": [],
        },
        "38c6fe5b-dd58-4399-a6cb-74035c2dec58": {
            "objectHash": "38c6fe5b-dd58-4399-a6cb-74035c2dec58",
            "classifications": [],
        },
        "f2db9e47-1edb-442b-94bf-023462a787c1": {
            "objectHash": "f2db9e47-1edb-442b-94bf-023462a787c1",
            "classifications": [],
        },
    },
    "classification_answers": {
        "dbc12c85-fd0e-489b-b812-945fb0a9c8b2": {
            "classificationHash": "dbc12c85-fd0e-489b-b812-945fb0a9c8b2",
            "classifications": [
                {
                    "name": "Tastiness Level",
                    "value": "tastiness_level",
                    "answers": [
                        {
                            "name": "Very Tasty",
                            "value": "very_tasty",
                            "featureHash": "c456ae2e-a60d-4bb5-9d9e-2822743a7645",
                        }
                    ],
                    "featureHash": "338931a4-32e2-4f19-aa62-84e12aa410c3",
                    "manualAnnotation": True,
                }
            ],
        }
    },
    "object_actions": {},
    "label_status": "LABEL_IN_PROGRESS",
}
ontology_rotatable_bboxes = OntologyStructure(
    objects=[
        Object(
            uid=1,
            name="Salami",
            color="#a7a3c8",
            shape=Shape.ROTATABLE_BOUNDING_BOX,
            feature_node_hash="d8495e57-69d8-44b4-9617-2fd9f628886b",
            attributes=[
                ChecklistAttribute(
                    uid=[1, 2],
                    feature_node_hash="4ae232f3-89dc-4b39-b9e5-4ac16cdc8cb7",
                    name="Spicy",
                    required=False,
                    dynamic=False,
                    options=[
                        FlatOption(
                            uid=[1, 1],
                            feature_node_hash="f212bd28-a5a7-48db-8193-be05e0f08afe",
                            label="Spicy",
                            value="spicy",
                        )
                    ],
                )
            ],
        ),
        Object(
            uid=2,
            name="Pineapple",
            color="#202020",
            shape=Shape.ROTATABLE_BOUNDING_BOX,
            feature_node_hash="0a58701c-07bf-4005-b561-fdfa5be4cf14",
            attributes=[],
        ),
    ],
    classifications=[
        Classification(
            uid=1,
            feature_node_hash="fd38edb3-5b3b-48bd-becd-894b7fa6a325",
            attributes=[
                RadioAttribute(
                    uid=[1],
                    feature_node_hash="338931a4-32e2-4f19-aa62-84e12aa410c3",
                    name="Tastiness Level",
                    required=False,
                    options=[
                        NestableOption(
                            uid=[1, 1],
                            feature_node_hash="41814c00-3d2f-4e29-a6f6-06217cee42ef",
                            label="Not Tasty",
                            value="not_tasty",
                            nested_options=[],
                        ),
                        NestableOption(
                            uid=[1, 2],
                            feature_node_hash="c0be2142-c556-4d62-ad70-8e6b45dde448",
                            label="Tasty",
                            value="tasty",
                            nested_options=[],
                        ),
                        NestableOption(
                            uid=[1, 3],
                            feature_node_hash="c456ae2e-a60d-4bb5-9d9e-2822743a7645",
                            label="Very Tasty",
                            value="very_tasty",
                            nested_options=[],
                        ),
                    ],
                )
            ],
        )
    ],
)
output_rotatable_bboxes = {
    "annotations": [
        {
            "area": 3393.4430736000004,
            "attributes": {
                "encord_track_uuid": "2a66ba97-3e6c-48c1-bb49-052d00f523a0",
                "rotation": 218.2,
                "track_id": 0,
            },
            "bbox": [318.16799999999995, 48.8621, 77.004, 44.068400000000004],
            "category_id": 1,
            "id": 0,
            "image_id": 0,
            "iscrowd": 0,
            "keypoints": None,
            "num_keypoints": None,
            "segmentation": [
                [
                    318.16799999999995,
                    48.8621,
                    395.17199999999997,
                    48.8621,
                    395.17199999999997,
                    92.9305,
                    318.16799999999995,
                    92.9305,
                ]
            ],
        },
        {
            "area": 2778.5193480000003,
            "attributes": {"encord_track_uuid": "ada3228c-2bd3-49cb-b18a-f7433c68b7c0", "rotation": 0, "track_id": 1},
            "bbox": [290.034, 594.587, 35.64, 77.9607],
            "category_id": 1,
            "id": 1,
            "image_id": 0,
            "iscrowd": 0,
            "keypoints": None,
            "num_keypoints": None,
            "segmentation": [[290.034, 594.587, 325.674, 594.587, 325.674, 672.5477, 290.034, 672.5477]],
        },
        {
            "area": 2132.0783064,
            "attributes": {"encord_track_uuid": "38c6fe5b-dd58-4399-a6cb-74035c2dec58", "rotation": 0, "track_id": 2},
            "bbox": [328.644, 595.3439, 39.36600000000001, 54.160399999999996],
            "category_id": 1,
            "id": 2,
            "image_id": 0,
            "iscrowd": 0,
            "keypoints": None,
            "num_keypoints": None,
            "segmentation": [[328.644, 595.3439, 368.01, 595.3439, 368.01, 649.5043, 328.644, 649.5043]],
        },
        {
            "area": 3471.5415294,
            "attributes": {
                "encord_track_uuid": "f2db9e47-1edb-442b-94bf-023462a787c1",
                "rotation": 349.8,
                "track_id": 3,
            },
            "bbox": [81.972, 53.908100000000005, 66.258, 52.3943],
            "category_id": 1,
            "id": 3,
            "image_id": 0,
            "iscrowd": 0,
            "keypoints": None,
            "num_keypoints": None,
            "segmentation": [
                [81.972, 53.908100000000005, 148.23, 53.908100000000005, 148.23, 106.3024, 81.972, 106.3024]
            ],
        },
    ],
    "categories": [
        {"id": 0, "name": "Salami", "supercategory": "rotatable_bounding_box"},
        {"id": 1, "name": "Pineapple", "supercategory": "rotatable_bounding_box"},
    ],
    "images": [
        {
            "coco_url": "https://storage.googleapis.com/encord-local-dev.appspot.com/cord-images-dev/lFW59RQ9jcT4vHZeG14m8QWJKug1/8834e4f8-1d50-464c-baca-1717f970612d?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=firebase-adminsdk-efw44%40encord-local-dev.iam.gserviceaccount.com%2F20221111%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20221111T141510Z&X-Goog-Expires=604800&X-Goog-SignedHeaders=host&X-Goog-Signature=ac8e7f7fe9c159309f4574434b78101446c3dcf5c00609cf2e0a20c36dd29d23d9c586684827f92bedebc4bcfe75d8c402bcb59a3196beb67d5593436c190963ffbea5bdf9fda8a34242aa6a5e026e8a41a113db1629ef2321c194cbbf79ac239f9385e8eadfc37b24b68f843de9957e407950ea48fcc4d2584039d962be5b71ab7e5a67787c1fa77bdf8f25bf6da359ff21108e650fe7845a30adece188906d9fc3610f58c461c51fdd377536729cc405189f5268f8af9cb9b92fc827ff2c962236e15f96b6c5aef49eb1ff85ed6ed302e93cd8a159165dc67e57a702e11dccd856cd0b986fcb502c95d87bffc8f11f0b7dffab734521b879098347e1418028",
            "file_name": "images/8834e4f8-1d50-464c-baca-1717f970612d.jpg",
            "height": 841,
            "id": 0,
            "image_title": "Hawaiian Pizza.jpg",
            "width": 540,
        }
    ],
    "info": {
        "contributor": None,
        "date_created": None,
        "description": "image-group-27e19",
        "url": None,
        "version": None,
        "year": None,
    },
}
