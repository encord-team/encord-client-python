import os

from encord_coco.coco_transcoders_copied import (
    ConvertFromCordAnnotationFormatToCOCOAnnotationFormat,
)

from encord import EncordUserClient
from encord.objects.ontology import Ontology

DEV_DOMAIN = "https://dev.api.cord.tech"
LOCAL_DOMAIN = "http://127.0.0.1:8000"
STAGING_DOMAIN = "https://staging.api.cord.tech"

USED_DOMAIN = LOCAL_DOMAIN

# PROJECT_RESOURCE_ID = "11cb4f95-7483-4867-b0c4-0a0fb23464a6"  # Task with 3 PNG
# PROJECT_RESOURCE_ID = "37d47b8d-c5d9-46ef-8591-5190a4f932f3"  # Polyline example on local dev
# PROJECT_RESOURCE_ID = "83e4204a-5b3b-403a-b1db-45a404fbf3e3"  # Polyline example on dev
# PROJECT_RESOURCE_ID = "1a0a2e01-9d75-4781-95c1-0e2efe0d31e9"  # dicom project on staging
# PROJECT_RESOURCE_ID = "73822617-4183-4202-99e9-3bbfd0f9f0ee"  # Inference and training project on local dev
PROJECT_RESOURCE_ID = "ee79c249-8b84-4d4c-8528-d73cab7a1ae3"  # Project with many images dataset on local dev

# DATASET_RESOURCE_ID = "f56be19d-4202-46a2-8f40-5e2eef649ffe"  # CVAT dataset
# DATASET_RESOURCE_ID = "d7cbfc0e-9fe5-4b55-af5e-773e2e3a0bc4"  # "Video Dataset" local dev
DATASET_RESOURCE_ID = "d1e7710c-4ba8-4e64-b9f7-c2c2268b1c86"  # "Mixed datatype dataset" local dev
# DATASET_RESOURCE_ID = "972f3869-84e5-4d33-ad62-74d107d8b618"  # "video dataset 3" staging
# DATASET_RESOURCE_ID = "f8b4cad7-8b9d-4e4e-b1f3-7917c574f849"  # "cloud integration 6" (aws) local dev
# DATASET_RESOURCE_ID = "c35208ae-15e7-4123-8040-7c14867da13f"  # "s3 multi ignore errors take 2, 19.05" (aws) staging


def get_project_ssh():
    cord_user_client = EncordUserClient.create_with_ssh_private_key(os.environ.get("SSH_KEY"), domain=USED_DOMAIN)

    return cord_user_client.get_project(PROJECT_RESOURCE_ID)


def test_get_labels():
    project = get_project_ssh()
    print(project.label_rows)
    for label_row in project.label_rows:
        data_title = label_row["data_title"]
        if data_title == "cute-cat.mp4" and label_row["label_hash"] is not None:
            labels = project.get_label_row(label_row["label_hash"])
            print(f"{data_title} = {labels}")


def test_get_ontology():
    project = get_project_ssh()
    print(Ontology.from_dict(project.ontology))


def test_coco_transcoder():
    project = get_project_ssh()
    # print(project.label_rows)
    label = project.get_label_row("b24c83ad-0ed8-4b95-a6b7-f2c3336f37ad")
    x = ConvertFromCordAnnotationFormatToCOCOAnnotationFormat(label)
    print(x)

    output = {
        "info": {
            "contributor": None,
            "date_created": None,
            "url": "https://storage.googleapis.com/encord-local-dev.appspot.com/cord-videos-dev/lFW59RQ9jcT4vHZeG14m8QWJKug1/358578a4-2ee8-4eda-bb82-f9649ecfc6d4?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=firebase-adminsdk-efw44%40encord-local-dev.iam.gserviceaccount.com%2F20220713%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20220713T143816Z&X-Goog-Expires=604800&X-Goog-SignedHeaders=host&X-Goog-Signature=2b03a47b57d47cae1dd6051e463e4f8ad42f337e72ef4619d054358e5b0ff6931f4ee67b027111101d9478acd571b114b1c38d48d1cd1124abffc38006819fa9aedfddbbd584d24db152976b7c22402ef7a4bb8831b7ddbe26c0b9efb94d5ed45bd5dc73d65668391f9cc2ea78154c13389f788de45f8b1f635bf213eee4bbc0fa01e0c5e956856989904fb262527d9e7740316ced92ecafca577903a48016fe28d8f46e8f3bd17fc8685895eb3c992a878d5282838aa38ea579e5cbaaffb0f88117d4f16b3c37de8ac147ef0f28d4f0ae8451f37186418517a22384f0bca2a6c0b9ffcd2e50d4f25ea7835db38e6b3fbcdd02d4b3e105ccd66ef721ec38356f",
            "version": None,
            "year": None,
            "description": "horse-and-dog.mp4",
        },
        "licenses": [],
        "categories": [
            {"supercategory": "box", "id": 0, "name": "box_9d80e119"},
            {"supercategory": "box", "id": 1, "name": "box_f866bdda"},
            {"supercategory": "box", "id": 2, "name": "box_a09c1fee"},
            {"supercategory": "box", "id": 3, "name": "box_b5173242"},
        ],
        "images": [
            {"id": 0, "height": 2, "width": 1, "file_name": "horse-and-dog.mp4"},
            {"id": 4, "height": 2, "width": 1, "file_name": "horse-and-dog.mp4"},
        ],
        "annotations": [
            {
                "area": 0.02795052,
                "bbox": [0.1525, 0.3456, 0.0874, 0.3198],
                "category_id": 0,
                "id": 0,
                "image_id": 0,
                "iscrowd": 0,
                "segmentation": [[0.1525, 0.3456, 0.2399, 0.3456, 0.2399, 0.6654, 0.1525, 0.6654]],
            },
            {
                "area": 0.0104648,
                "bbox": [0.6214, 1.1404, 0.0412, 0.254],
                "category_id": 1,
                "id": 1,
                "image_id": 0,
                "iscrowd": 0,
                "segmentation": [[0.6214, 1.1404, 0.6626, 1.1404, 0.6626, 1.3944, 0.6214, 1.3944]],
            },
            {
                "area": 0.00456876,
                "bbox": [0.7349, 1.0418, 0.0294, 0.1554],
                "category_id": 2,
                "id": 2,
                "image_id": 0,
                "iscrowd": 0,
                "segmentation": [[0.7349, 1.0418, 0.7643, 1.0418, 0.7643, 1.1972, 0.7349, 1.1972]],
            },
            {
                "area": 0.013377,
                "bbox": [0.6954, 0.8118, 0.0546, 0.245],
                "category_id": 3,
                "id": 3,
                "image_id": 4,
                "iscrowd": 0,
                "segmentation": [[0.6954, 0.8118, 0.75, 0.8118, 0.75, 1.0568, 0.6954, 1.0568]],
            },
        ],
    }
