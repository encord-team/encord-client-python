from tests.objects.data.all_ontology_types import global_classification_dict

GLOBAL_CLASSIFICATION_LABELS = {
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
    "label_status": "LABEL_IN_PROGRESS",
    "spaces": {},
    "data_units": {
        "cd57cf5c-2541-4a46-a836-444540ee987a": {
            "data_hash": "cd57cf5c-2541-4a46-a836-444540ee987a",
            "data_title": "two-frame-video.mp4",
            "data_link": "cord-videos-dev/lFW59RQ9jcT4vHZeG14m8QWJKug1/cd57cf5c-2541-4a46-a836-444540ee987a",
            "data_type": "video/mp4",
            "data_sequence": 0,
            "width": 1200,
            "height": 924,
            "labels": {},
            "data_duration": 0.08,
            "data_fps": 25.0,
        }
    },
    "object_actions": {},
    "object_answers": {},
    "classification_answers": {
        "globalClassificationHash": {
            "classificationHash": "globalClassificationHash",
            "featureHash": global_classification_dict["featureNodeHash"],
            "classifications": [
                {
                    "name": "Global classification",
                    "value": "global_classification",
                    "answers": [
                        {
                            "name": "Global Answer 1",
                            "value": "global_answer_1",
                            "featureHash": "3vLjF0q1",
                        }
                    ],
                    "featureHash": "2mwWr3Of",
                    "manualAnnotation": True,
                },
            ],
            "range": [],
            "createdBy": "user1Hash@encord.com",
            "createdAt": "Tue, 05 Nov 2024 09:41:37 UTC",
            "lastEditedBy": "user1Hash@encord.com",
            "lastEditedAt": "Tue, 05 Nov 2024 09:41:37 UTC",
            "manualAnnotation": True,
        },
    },
}
