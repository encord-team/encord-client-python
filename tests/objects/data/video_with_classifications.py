from copy import deepcopy

from encord.objects.types import LabelRowDict
from tests.objects.data.all_types_ontology_structure import RADIO_CLASSIFICATION

labels: LabelRowDict = {
    "label_hash": "28f0e9d2-51e0-459d-8ffa-2e214da653a9",
    "branch_name": "main",
    "created_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "last_edited_at": "Thu, 09 Feb 2023 14:12:03 UTC",
    "data_hash": "cd57cf5c-2541-4a46-a836-444540ee987a",
    "dataset_hash": "b0d93919-a5e8-4418-8dd5-2c51e3977de8",
    "dataset_title": "Dataset with 2 frame video",
    "data_title": "two-frame-video.mp4",
    "data_type": "video",
    "annotation_task_status": "QUEUED",
    "is_shadow_data": False,
    "object_actions": {},
    "label_status": "LABEL_IN_PROGRESS",
    "object_answers": {},
    "classification_answers": {
        "3AqiIPrF": {
            "classificationHash": "3AqiIPrF",
            "featureHash": RADIO_CLASSIFICATION.feature_node_hash,
            "range": [[0, 1]],
            "createdBy": "user1Hash",
            "createdAt": "Tue, 05 Nov 2024 09:41:37 UTC",
            "lastEditedBy": "user1Hash",
            "lastEditedAt": "Tue, 05 Nov 2024 09:41:37 UTC",
            "manualAnnotation": True,
            "classifications": [
                {
                    "name": "Radio classification 1",
                    "value": "radio_classification_1",
                    "answers": [{"name": "cl 1 option 2", "value": "cl_1_option_2", "featureHash": "MjUzMTg1"}],
                    "featureHash": "MjI5MTA5",
                    "manualAnnotation": True,
                },
            ],
        },
    },
    "data_units": {
        "cd57cf5c-2541-4a46-a836-444540ee987a": {
            "data_hash": "cd57cf5c-2541-4a46-a836-444540ee987a",
            "data_title": "two-frame-video.mp4",
            "data_link": "cord-videos-dev/lFW59RQ9jcT4vHZeG14m8QWJKug1/cd57cf5c-2541-4a46-a836-444540ee987a",
            "data_type": "video/mp4",
            "data_sequence": 0,
            "width": 1200,
            "height": 924,
            "data_duration": 0.08,
            "data_fps": 25.0,
            "labels": {
                "0": {
                    "objects": [],
                    "classifications": [
                        {
                            "name": "Radio classification 1",
                            "value": "radio_classification_1",
                            "createdAt": "Tue, 17 Jan 2023 11:44:53 UTC",
                            "createdBy": "dev@encord.com",
                            "confidence": 1,
                            "featureHash": RADIO_CLASSIFICATION.feature_node_hash,
                            "lastEditedAt": "Tue, 17 Jan 2023 11:44:53 UTC",
                            "classificationHash": "3AqiIPrF",
                            "manualAnnotation": True,
                        },
                    ],
                },
                "1": {
                    "objects": [],
                    "classifications": [
                        {
                            "name": "Radio classification 1",
                            "value": "radio_classification_1",
                            "createdAt": "Tue, 17 Jan 2023 11:44:53 UTC",
                            "createdBy": "dev@encord.com",
                            "confidence": 1,
                            "featureHash": RADIO_CLASSIFICATION.feature_node_hash,
                            "lastEditedAt": "Tue, 17 Jan 2023 11:44:53 UTC",
                            "classificationHash": "3AqiIPrF",
                            "manualAnnotation": True,
                        },
                    ],
                },
            },
        }
    },
}

labels_without_answer_meta = deepcopy(labels)
for answer in labels_without_answer_meta["classification_answers"].values():
    answer.pop("createdAt", None)
    answer.pop("createdBy", None)
    answer.pop("lastEditedAt", None)
    answer.pop("lastEditedBy", None)
    answer.pop("manualAnnotation", None)
    answer.pop("range", None)
