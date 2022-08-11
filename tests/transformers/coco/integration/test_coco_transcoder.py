import os

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


