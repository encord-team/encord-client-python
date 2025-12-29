from tests.objects.data.all_types_ontology_structure import RADIO_CLASSIFICATION, TEXT_OBJECT

PLAIN_TEXT_LABELS = {
    "label_hash": "0aea5ac7-cbc0-4451-a242-e22445d2c9fa",
    "branch_name": "main",
    "created_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "last_edited_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "data_hash": "aaa6bc82-9f89-4545-adbb-f271bf28cf99",
    "annotation_task_status": "QUEUED",
    "is_shadow_data": False,
    "dataset_hash": "b02ba3d9-883b-4c5e-ba09-751072ccfc57",
    "dataset_title": "Text Dataset",
    "data_title": "text.txt",
    "data_type": "plain_text",
    "spaces": {},
    "data_units": {
        "cd53f484-c9ab-4fd1-9c14-5b34d4e42ba2": {
            "data_hash": "cd53f484-c9ab-4fd1-9c14-5b34d4e42ba2",
            "data_title": "text.txt",
            "data_type": "text/plain",
            "data_sequence": 0,
            "data_link": "text-link",
            "labels": {},
        }
    },
    "object_answers": {
        "textObjectHash": {
            "objectHash": "textObjectHash",
            "featureHash": TEXT_OBJECT.feature_node_hash,
            "classifications": [],
            "range": [[0, 5]],
            "createdBy": "user1Hash",
            "createdAt": "Tue, 05 Nov 2024 09:41:37 UTC",
            "lastEditedBy": "user1Hash",
            "lastEditedAt": "Tue, 05 Nov 2024 09:41:37 UTC",
            "manualAnnotation": True,
            "name": "text object",
            "value": "text_object",
            "color": TEXT_OBJECT.color,
            "shape": "text",
        },
    },
    "classification_answers": {
        "textClassificationHash": {
            "classificationHash": "textClassificationHash",
            "featureHash": "jPOcEsbw",
            "spaces": None,
            "classifications": [
                {
                    "name": "Text classification",
                    "value": "text_classification",
                    "answers": "Text Answer",
                    "featureHash": "OxrtEM+v",
                    "manualAnnotation": True,
                },
            ],
            "range": [],
            "createdBy": "user1Hash",
            "createdAt": "Tue, 05 Nov 2024 09:41:37 UTC",
            "lastEditedBy": "user1Hash",
            "lastEditedAt": "Tue, 05 Nov 2024 09:41:37 UTC",
            "manualAnnotation": True,
        },
        "radioClassificationHash": {
            "classificationHash": "radioClassificationHash",
            "featureHash": RADIO_CLASSIFICATION.feature_node_hash,
            "spaces": None,
            "classifications": [
                {
                    "name": "Radio classification 1",
                    "value": "radio_classification_1",
                    "answers": [
                        {
                            "name": "cl 1 option 1",
                            "value": "cl_1_option_1",
                            "featureHash": "MTcwMjM5",
                        }
                    ],
                    "featureHash": "MjI5MTA5",
                    "manualAnnotation": True,
                },
                {
                    "name": "cl 1 2 text",
                    "value": "cl_1_2_text",
                    "answers": "Nested Text Answer",
                    "featureHash": "MTg0MjIw",
                    "manualAnnotation": True,
                },
            ],
            "range": [],
            "createdBy": "user1Hash",
            "createdAt": "Tue, 05 Nov 2024 09:41:37 UTC",
            "lastEditedBy": "user1Hash",
            "lastEditedAt": "Tue, 05 Nov 2024 09:41:37 UTC",
            "manualAnnotation": True,
        },
        "checklistClassificationHash": {
            "classificationHash": "checklistClassificationHash",
            "featureHash": "3DuQbFxo",
            "spaces": None,
            "classifications": [
                {
                    "name": "Checklist classification",
                    "value": "checklist_classification",
                    "answers": [
                        {
                            "name": "Checklist classification answer 1",
                            "value": "checklist_classification_answer_1",
                            "featureHash": "fvLjF0qZ",
                        },
                        {
                            "name": "Checklist classification answer 2",
                            "value": "checklist_classification_answer_2",
                            "featureHash": "a4r7nK9i",
                        },
                    ],
                    "featureHash": "9mwWr3OE",
                    "manualAnnotation": True,
                },
            ],
            "range": [],
            "createdBy": "user1Hash",
            "createdAt": "Tue, 05 Nov 2024 09:41:37 UTC",
            "lastEditedBy": "user1Hash",
            "lastEditedAt": "Tue, 05 Nov 2024 09:41:37 UTC",
            "manualAnnotation": True,
        },
    },
    "object_actions": {},
    "label_status": "LABEL_IN_PROGRESS",
}

EMPTY_PLAIN_TEXT_LABELS = {
    "label_hash": "0aea5ac7-cbc0-4451-a242-e22445d2c9fa",
    "branch_name": "main",
    "created_at": "2023-02-09 14:12:03",
    "last_edited_at": "2023-02-09 14:12:03",
    "data_hash": "aaa6bc82-9f89-4545-adbb-f271bf28cf99",
    "annotation_task_status": "QUEUED",
    "is_shadow_data": False,
    "dataset_hash": "b02ba3d9-883b-4c5e-ba09-751072ccfc57",
    "dataset_title": "Text Dataset",
    "data_title": "text.txt",
    "data_type": "plain_text",
    "data_units": {
        "cd53f484-c9ab-4fd1-9c14-5b34d4e42ba2": {
            "data_hash": "cd53f484-c9ab-4fd1-9c14-5b34d4e42ba2",
            "data_title": "text.txt",
            "data_type": "text/plain",
            "data_sequence": 0,
            "data_link": "text-link",
            "labels": {},
        }
    },
    "object_answers": {},
    "classification_answers": {},
    "object_actions": {},
    "label_status": "LABEL_IN_PROGRESS",
}
