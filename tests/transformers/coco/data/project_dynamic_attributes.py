from encord.objects.common import (
    ChecklistAttribute,
    FlatOption,
    NestableOption,
    RadioAttribute,
    Shape,
    TextAttribute,
)
from encord.objects.ontology_object import Object
from encord.objects.ontology_structure import OntologyStructure

labels = [
    {
        "label_hash": "efe0eee7-8e8e-438d-887c-fa3ee600e823",
        "dataset_hash": "386f81dd-ec17-4b83-add7-7121923c24e1",
        "dataset_title": "Multiple data types",
        "data_title": "horse and dog from sdk",
        "data_type": "video",
        "data_units": {
            "a8029f7f-b4fe-4237-96c9-b12a33c5b3d8": {
                "data_hash": "a8029f7f-b4fe-4237-96c9-b12a33c5b3d8",
                "data_title": "horse and dog from sdk",
                "data_type": "video/mp4",
                "data_sequence": 0,
                "labels": {
                    "0": {
                        "objects": [
                            {
                                "name": "Box with attributes",
                                "color": "#D33115",
                                "shape": "bounding_box",
                                "value": "box_with_attributes",
                                "createdAt": "Thu, 17 Nov 2022 14:10:55 GMT",
                                "createdBy": "denis@cord.tech",
                                "confidence": 1,
                                "objectHash": "JizLqHk3",
                                "featureHash": "eEMJNUol",
                                "lastEditedAt": "Thu, 17 Nov 2022 14:11:17 GMT",
                                "lastEditedBy": "denis@cord.tech",
                                "manualAnnotation": True,
                                "boundingBox": {"h": 0.1487, "w": 0.0665, "x": 0.2546, "y": 0.2912},
                                "reviews": [],
                            },
                            {
                                "name": "Box with attributes",
                                "color": "#D33115",
                                "shape": "bounding_box",
                                "value": "box_with_attributes",
                                "createdAt": "Thu, 17 Nov 2022 14:10:57 GMT",
                                "createdBy": "denis@cord.tech",
                                "confidence": 1,
                                "objectHash": "ogYkOiJW",
                                "featureHash": "eEMJNUol",
                                "manualAnnotation": True,
                                "boundingBox": {"h": 0.1706, "w": 0.107, "x": 0.567, "y": 0.5055},
                                "reviews": [],
                            },
                        ],
                        "classifications": [],
                    },
                    "1": {
                        "objects": [
                            {
                                "name": "Box with attributes",
                                "color": "#D33115",
                                "shape": "bounding_box",
                                "value": "box_with_attributes",
                                "createdAt": "Thu, 17 Nov 2022 14:11:21 GMT",
                                "createdBy": "denis@cord.tech",
                                "isDeleted": False,
                                "confidence": 1,
                                "objectHash": "JizLqHk3",
                                "featureHash": "eEMJNUol",
                                "lastEditedAt": "Thu, 17 Nov 2022 14:11:17 GMT",
                                "lastEditedBy": "denis@cord.tech",
                                "manualAnnotation": True,
                                "boundingBox": {"h": 0.1487, "w": 0.0665, "x": 0.2546, "y": 0.2912},
                                "reviews": [],
                            },
                            {
                                "name": "Box with attributes",
                                "color": "#D33115",
                                "shape": "bounding_box",
                                "value": "box_with_attributes",
                                "createdAt": "Thu, 17 Nov 2022 14:12:02 GMT",
                                "createdBy": "denis@cord.tech",
                                "isDeleted": False,
                                "confidence": 1,
                                "objectHash": "ogYkOiJW",
                                "featureHash": "eEMJNUol",
                                "lastEditedAt": "Thu, 17 Nov 2022 14:12:13 GMT",
                                "lastEditedBy": "denis@cord.tech",
                                "manualAnnotation": True,
                                "boundingBox": {"h": 0.1706, "w": 0.107, "x": 0.567, "y": 0.5033},
                                "reviews": [],
                            },
                        ],
                        "classifications": [],
                    },
                    "2": {
                        "objects": [
                            {
                                "name": "Box with attributes",
                                "color": "#D33115",
                                "shape": "bounding_box",
                                "value": "box_with_attributes",
                                "createdAt": "Thu, 17 Nov 2022 14:11:22 GMT",
                                "createdBy": "denis@cord.tech",
                                "isDeleted": False,
                                "confidence": 1,
                                "objectHash": "JizLqHk3",
                                "featureHash": "eEMJNUol",
                                "lastEditedAt": "Thu, 17 Nov 2022 14:11:17 GMT",
                                "lastEditedBy": "denis@cord.tech",
                                "manualAnnotation": True,
                                "boundingBox": {"h": 0.1487, "w": 0.0665, "x": 0.2546, "y": 0.2912},
                                "reviews": [],
                            },
                            {
                                "name": "Box with attributes",
                                "color": "#D33115",
                                "shape": "bounding_box",
                                "value": "box_with_attributes",
                                "createdAt": "Thu, 17 Nov 2022 14:12:20 GMT",
                                "createdBy": "denis@cord.tech",
                                "isDeleted": False,
                                "confidence": 1,
                                "objectHash": "ogYkOiJW",
                                "featureHash": "eEMJNUol",
                                "lastEditedAt": "Thu, 17 Nov 2022 14:12:27 GMT",
                                "lastEditedBy": "denis@cord.tech",
                                "manualAnnotation": True,
                                "boundingBox": {"h": 0.1706, "w": 0.1008, "x": 0.5732, "y": 0.5033},
                                "reviews": [],
                            },
                        ],
                        "classifications": [],
                    },
                },
                "data_fps": 30.0,
                "data_link": "cord-videos-dev/lFW59RQ9jcT4vHZeG14m8QWJKug1/a8029f7f-b4fe-4237-96c9-b12a33c5b3d8",
                "width": 1280,
                "height": 720,
            }
        },
        "object_answers": {
            "JizLqHk3": {
                "objectHash": "JizLqHk3",
                "classifications": [
                    {
                        "name": "non dynamic checklist attribute 1",
                        "value": "non_dynamic_checklist_attribute_1",
                        "answers": [
                            {
                                "name": "non dynamic checklist attribute 1 option 1",
                                "value": "non_dynamic_checklist_attribute_1_option_1",
                                "featureHash": "egqzCteI",
                            },
                            {
                                "name": "non dynamic checklist attribute 1 option 2",
                                "value": "non_dynamic_checklist_attribute_1_option_2",
                                "featureHash": "49bR6HCG",
                            },
                        ],
                        "featureHash": "Ps+P5JNt",
                        "manualAnnotation": True,
                    },
                    {
                        "name": "non dynamic radio attribute 1",
                        "value": "non_dynamic_radio_attribute_1",
                        "answers": [
                            {
                                "name": "non dynamic radio attribute 1 option 1",
                                "value": "non_dynamic_radio_attribute_1_option_1",
                                "featureHash": "Epgowsig",
                            }
                        ],
                        "featureHash": "FZtCKRXA",
                        "manualAnnotation": True,
                    },
                    {
                        "name": "non dynamic text attribute 1",
                        "value": "non_dynamic_text_attribute_1",
                        "answers": "non dynamic answer",
                        "featureHash": "bi4Ri4Qp",
                        "manualAnnotation": True,
                    },
                ],
            },
            "ogYkOiJW": {
                "objectHash": "ogYkOiJW",
                "classifications": [
                    {
                        "name": "",
                        "value": "",
                        "answers": "text inside dynamic attribute",
                        "featureHash": "oVn7MHh6",
                        "manualAnnotation": True,
                    }
                ],
            },
        },
        "classification_answers": {},
        "object_actions": {
            "JizLqHk3": {
                "objectHash": "JizLqHk3",
                "actions": [
                    {
                        "name": "dynamic text attribute 2",
                        "range": [[0, 2]],
                        "value": "box_with_attributes",
                        "answers": "dynamic answer",
                        "dynamic": True,
                        "trackHash": "c71f6bbc-77e0-450b-8cd1-d16a884f5e45",
                        "featureHash": "Pt4zRmE8",
                        "shouldPropagate": True,
                        "manualAnnotation": True,
                    },
                    {
                        "name": "dynamic radio attribute 2",
                        "range": [[0, 0]],
                        "value": "dynamic_radio_attribute_2",
                        "answers": [
                            {
                                "name": "dynamic radio attribute 2 option 2",
                                "value": "dynamic_radio_attribute_2_option_2",
                                "featureHash": "0RV8h1+k",
                            }
                        ],
                        "dynamic": True,
                        "trackHash": "4ef3aeca-9ade-4a78-99af-db42d0b31aeb",
                        "featureHash": "LPK6qTW6",
                        "shouldPropagate": False,
                        "manualAnnotation": True,
                    },
                    {
                        "name": "dynamic checklist attribute 2",
                        "range": [[0, 2]],
                        "value": "dynamic_checklist_attribute_2",
                        "answers": [
                            {
                                "name": "dynamic checklist attribute 2 option 1",
                                "value": "dynamic_checklist_attribute_2_option_1",
                                "featureHash": "ZurpLJ2o",
                            }
                        ],
                        "dynamic": True,
                        "trackHash": "0660b9ff-71bd-47af-a85d-50e4c5baacbd",
                        "featureHash": "EyUInCwX",
                        "shouldPropagate": True,
                        "manualAnnotation": True,
                    },
                ],
            },
            "ogYkOiJW": {
                "objectHash": "ogYkOiJW",
                "actions": [
                    {
                        "name": "dynamic text attribute 2",
                        "range": [[0, 1]],
                        "value": "box_with_attributes",
                        "answers": "dynamic answer two",
                        "dynamic": True,
                        "trackHash": "300ba6ae-eaaf-46c5-9a80-02b452371cd8",
                        "featureHash": "Pt4zRmE8",
                        "shouldPropagate": False,
                        "manualAnnotation": True,
                    },
                    {
                        "name": "dynamic radio attribute 2",
                        "range": [[0, 1]],
                        "value": "dynamic_radio_attribute_2",
                        "answers": [
                            {
                                "name": "dynamic radio attribute 2 option 1",
                                "value": "dynamic_radio_attribute_2_option_1",
                                "featureHash": "fw/E2b1Z",
                            }
                        ],
                        "dynamic": True,
                        "trackHash": "c3a41197-3a63-450e-bfde-e3caa41b749b",
                        "featureHash": "LPK6qTW6",
                        "shouldPropagate": False,
                        "manualAnnotation": True,
                    },
                    {
                        "name": "dynamic checklist attribute 2",
                        "range": [[0, 0]],
                        "value": "dynamic_checklist_attribute_2",
                        "answers": [
                            {
                                "name": "dynamic checklist attribute 2 option 1",
                                "value": "dynamic_checklist_attribute_2_option_1",
                                "featureHash": "ZurpLJ2o",
                            }
                        ],
                        "dynamic": True,
                        "trackHash": "94f5b3ab-1a19-4bbc-9b6b-3b2e11598323",
                        "featureHash": "EyUInCwX",
                        "shouldPropagate": False,
                        "manualAnnotation": True,
                    },
                    {
                        "name": "dynamic text attribute 2",
                        "range": [[2, 2]],
                        "value": "box_with_attributes",
                        "answers": "dynamic two",
                        "dynamic": True,
                        "trackHash": "14e4b710-47dc-4ecc-b155-d93cb4c1aed7",
                        "featureHash": "Pt4zRmE8",
                        "shouldPropagate": True,
                        "manualAnnotation": True,
                    },
                    {
                        "name": "dynamic radio attribute 2",
                        "range": [[2, 2]],
                        "value": "dynamic_radio_attribute_2",
                        "answers": [
                            {
                                "name": "dynamic radio attribute 2 option 2",
                                "value": "dynamic_radio_attribute_2_option_2",
                                "featureHash": "0RV8h1+k",
                            }
                        ],
                        "dynamic": True,
                        "trackHash": "fa572297-81f0-4e63-9ea8-c225fb55de32",
                        "featureHash": "LPK6qTW6",
                        "shouldPropagate": False,
                        "manualAnnotation": True,
                    },
                    {
                        "name": "dynamic checklist attribute 2",
                        "range": [[2, 2]],
                        "value": "dynamic_checklist_attribute_2",
                        "answers": [
                            {
                                "name": "dynamic checklist attribute 2 option 2",
                                "value": "dynamic_checklist_attribute_2_option_2",
                                "featureHash": "uI0oyE0H",
                            },
                            {
                                "name": "dynamic checklist attribute 2 option 1",
                                "value": "dynamic_checklist_attribute_2_option_1",
                                "featureHash": "ZurpLJ2o",
                            },
                        ],
                        "dynamic": True,
                        "trackHash": "78f7793c-c1d7-4b86-b152-eca46bec8c27",
                        "featureHash": "EyUInCwX",
                        "shouldPropagate": False,
                        "manualAnnotation": True,
                    },
                ],
            },
        },
        "label_status": "LABEL_IN_PROGRESS",
    }
]

ontology = OntologyStructure(
    objects=[
        Object(
            uid=1,
            name="Box with attributes",
            color="#D33115",
            shape=Shape.BOUNDING_BOX,
            feature_node_hash="eEMJNUol",
            attributes=[
                TextAttribute(
                    uid=[1, 1], feature_node_hash="bi4Ri4Qp", name="non dynamic text attribute 1", required=False
                ),
                RadioAttribute(
                    uid=[1, 2],
                    feature_node_hash="FZtCKRXA",
                    name="non dynamic radio attribute 1",
                    required=False,
                    options=[
                        NestableOption(
                            uid=[1, 2, 1],
                            feature_node_hash="Epgowsig",
                            label="non dynamic radio attribute 1 option 1",
                            value="non_dynamic_radio_attribute_1_option_1",
                            nested_options=[],
                        ),
                        NestableOption(
                            uid=[1, 2, 2],
                            feature_node_hash="GuyampgR",
                            label="non dynamic radio attribute 1 option 2",
                            value="non_dynamic_radio_attribute_1_option_2",
                            nested_options=[],
                        ),
                    ],
                ),
                ChecklistAttribute(
                    uid=[1, 3],
                    feature_node_hash="Ps+P5JNt",
                    name="non dynamic checklist attribute 1",
                    required=False,
                    options=[
                        FlatOption(
                            uid=[1, 3, 1],
                            feature_node_hash="egqzCteI",
                            label="non dynamic checklist attribute 1 option 1",
                            value="non_dynamic_checklist_attribute_1_option_1",
                        ),
                        FlatOption(
                            uid=[1, 3, 2],
                            feature_node_hash="49bR6HCG",
                            label="non dynamic checklist attribute 1 option 2",
                            value="non_dynamic_checklist_attribute_1_option_2",
                        ),
                    ],
                ),
                TextAttribute(
                    uid=[1, 4], feature_node_hash="Pt4zRmE8", name="dynamic text attribute 2", required=False
                ),
                RadioAttribute(
                    uid=[1, 5],
                    feature_node_hash="LPK6qTW6",
                    name="dynamic radio attribute 2",
                    required=False,
                    options=[
                        NestableOption(
                            uid=[1, 5, 1],
                            feature_node_hash="fw/E2b1Z",
                            label="dynamic radio attribute 2 option 1",
                            value="dynamic_radio_attribute_2_option_1",
                            nested_options=[
                                TextAttribute(uid=[1, 5, 1, 1], feature_node_hash="oVn7MHh6", name="", required=False)
                            ],
                        ),
                        NestableOption(
                            uid=[1, 5, 2],
                            feature_node_hash="0RV8h1+k",
                            label="dynamic radio attribute 2 option 2",
                            value="dynamic_radio_attribute_2_option_2",
                            nested_options=[],
                        ),
                    ],
                ),
                ChecklistAttribute(
                    uid=[1, 6],
                    feature_node_hash="EyUInCwX",
                    name="dynamic checklist attribute 2",
                    required=False,
                    options=[
                        FlatOption(
                            uid=[1, 6, 1],
                            feature_node_hash="ZurpLJ2o",
                            label="dynamic checklist attribute 2 option 1",
                            value="dynamic_checklist_attribute_2_option_1",
                        ),
                        FlatOption(
                            uid=[1, 6, 2],
                            feature_node_hash="uI0oyE0H",
                            label="dynamic checklist attribute 2 option 2",
                            value="dynamic_checklist_attribute_2_option_2",
                        ),
                    ],
                ),
            ],
        ),
        Object(
            uid=2,
            name="Box with nested attributes",
            color="#E27300",
            shape=Shape.BOUNDING_BOX,
            feature_node_hash="CT5zyXPl",
            attributes=[
                RadioAttribute(
                    uid=[2, 1],
                    feature_node_hash="YmTkzuCu",
                    name="nested radio 1 ",
                    required=False,
                    options=[
                        NestableOption(
                            uid=[2, 1, 1],
                            feature_node_hash="9RaY888c",
                            label="nested radio 1 option 1",
                            value="nested_radio_1_option_1",
                            nested_options=[
                                RadioAttribute(
                                    uid=[2, 1, 1, 1],
                                    feature_node_hash="l7KMhGAZ",
                                    name="nested radio 1 option 1 1",
                                    required=False,
                                    options=[
                                        NestableOption(
                                            uid=[2, 1, 1, 1, 1],
                                            feature_node_hash="mFhqK3Jj",
                                            label="nested radio 1 option 1 1 option 1",
                                            value="nested_radio_1_option_1_1_option_1",
                                            nested_options=[],
                                        ),
                                        NestableOption(
                                            uid=[2, 1, 1, 1, 2],
                                            feature_node_hash="v948Rf8E",
                                            label="nested radio 1 option 1 1 option 2",
                                            value="nested_radio_1_option_1_1_option_2",
                                            nested_options=[],
                                        ),
                                    ],
                                )
                            ],
                        ),
                        NestableOption(
                            uid=[2, 1, 2],
                            feature_node_hash="SaZhTN18",
                            label="nested radio 1 option 2",
                            value="nested_radio_1_option_2",
                            nested_options=[],
                        ),
                    ],
                )
            ],
        ),
    ],
    classifications=[],
)

expected_coco_json = {
    "annotations": [
        {
            "area": 9113.28768,
            "attributes": {
                "encord_track_uuid": "JizLqHk3",
                "non dynamic checklist attribute 1 option 1": True,
                "non dynamic checklist attribute 1 option 2": True,
                "non dynamic radio attribute 1": "non dynamic " "radio " "attribute 1 " "option 1",
                "non dynamic text attribute 1": "non dynamic " "answer",
                "track_id": 0,
            },
            "bbox": [325.888, 209.66400000000002, 85.12, 107.064],
            "category_id": 1,
            "id": 0,
            "image_id": 0,
            "iscrowd": 0,
            "keypoints": None,
            "num_keypoints": None,
            "segmentation": [
                [325.888, 209.66400000000002, 411.008, 209.66400000000002, 411.008, 316.728, 325.888, 316.728]
            ],
        },
        {
            "area": 16823.070720000003,
            "attributes": {"encord_track_uuid": "ogYkOiJW", "track_id": 1},
            "bbox": [725.76, 363.96, 136.96, 122.83200000000001],
            "category_id": 1,
            "id": 1,
            "image_id": 0,
            "iscrowd": 0,
            "keypoints": None,
            "num_keypoints": None,
            "segmentation": [[725.76, 363.96, 862.72, 363.96, 862.72, 486.792, 725.76, 486.792]],
        },
        {
            "area": 9113.28768,
            "attributes": {
                "encord_track_uuid": "JizLqHk3",
                "non dynamic checklist attribute 1 option 1": True,
                "non dynamic checklist attribute 1 option 2": True,
                "non dynamic radio attribute 1": "non dynamic " "radio " "attribute 1 " "option 1",
                "non dynamic text attribute 1": "non dynamic " "answer",
                "track_id": 0,
            },
            "bbox": [325.888, 209.66400000000002, 85.12, 107.064],
            "category_id": 1,
            "id": 2,
            "image_id": 1,
            "iscrowd": 0,
            "keypoints": None,
            "num_keypoints": None,
            "segmentation": [
                [325.888, 209.66400000000002, 411.008, 209.66400000000002, 411.008, 316.728, 325.888, 316.728]
            ],
        },
        {
            "area": 16823.070720000003,
            "attributes": {"encord_track_uuid": "ogYkOiJW", "track_id": 1},
            "bbox": [725.76, 362.376, 136.96, 122.83200000000001],
            "category_id": 1,
            "id": 3,
            "image_id": 1,
            "iscrowd": 0,
            "keypoints": None,
            "num_keypoints": None,
            "segmentation": [
                [725.76, 362.376, 862.72, 362.376, 862.72, 485.20799999999997, 725.76, 485.20799999999997]
            ],
        },
        {
            "area": 9113.28768,
            "attributes": {
                "encord_track_uuid": "JizLqHk3",
                "non dynamic checklist attribute 1 option 1": True,
                "non dynamic checklist attribute 1 option 2": True,
                "non dynamic radio attribute 1": "non dynamic " "radio " "attribute 1 " "option 1",
                "non dynamic text attribute 1": "non dynamic " "answer",
                "track_id": 0,
            },
            "bbox": [325.888, 209.66400000000002, 85.12, 107.064],
            "category_id": 1,
            "id": 4,
            "image_id": 2,
            "iscrowd": 0,
            "keypoints": None,
            "num_keypoints": None,
            "segmentation": [
                [325.888, 209.66400000000002, 411.008, 209.66400000000002, 411.008, 316.728, 325.888, 316.728]
            ],
        },
        {
            "area": 15848.275968000002,
            "attributes": {"encord_track_uuid": "ogYkOiJW", "track_id": 1},
            "bbox": [733.696, 362.376, 129.024, 122.83200000000001],
            "category_id": 1,
            "id": 5,
            "image_id": 2,
            "iscrowd": 0,
            "keypoints": None,
            "num_keypoints": None,
            "segmentation": [
                [733.696, 362.376, 862.72, 362.376, 862.72, 485.20799999999997, 733.696, 485.20799999999997]
            ],
        },
    ],
    "categories": [
        {"id": 1, "name": "Box with attributes", "supercategory": "bounding_box"},
        {"id": 2, "name": "Box with nested attributes", "supercategory": "bounding_box"},
    ],
    "images": [
        {
            "coco_url": "cord-videos-dev/lFW59RQ9jcT4vHZeG14m8QWJKug1/a8029f7f-b4fe-4237-96c9-b12a33c5b3d8",
            "file_name": "videos/a8029f7f-b4fe-4237-96c9-b12a33c5b3d8/0.jpg",
            "height": 720,
            "id": 0,
            "video_title": "horse and dog from sdk",
            "width": 1280,
        },
        {
            "coco_url": "cord-videos-dev/lFW59RQ9jcT4vHZeG14m8QWJKug1/a8029f7f-b4fe-4237-96c9-b12a33c5b3d8",
            "file_name": "videos/a8029f7f-b4fe-4237-96c9-b12a33c5b3d8/1.jpg",
            "height": 720,
            "id": 1,
            "video_title": "horse and dog from sdk",
            "width": 1280,
        },
        {
            "coco_url": "cord-videos-dev/lFW59RQ9jcT4vHZeG14m8QWJKug1/a8029f7f-b4fe-4237-96c9-b12a33c5b3d8",
            "file_name": "videos/a8029f7f-b4fe-4237-96c9-b12a33c5b3d8/2.jpg",
            "height": 720,
            "id": 2,
            "video_title": "horse and dog from sdk",
            "width": 1280,
        },
    ],
    "info": {
        "contributor": None,
        "date_created": None,
        "description": "horse and dog from sdk",
        "url": None,
        "version": None,
        "year": None,
    },
}
