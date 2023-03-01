"""
These tests will live in the SDK integration tests
"""
import logging
import os
import sys

import pytest

from encord import EncordUserClient, Project
from encord.configs import ENCORD_DOMAIN
from encord.objects.coordinates import BoundingBoxCoordinates

ENABLE_MANUAL_TESTS = False


LOCAL_DOMAIN = "http://127.0.0.1:8000"
DEV_DOMAIN = "https://dev.api.encord.com"
STAGING_DOMAIN = "https://staging.api.encord.com"
PROD_DOMAIN = ENCORD_DOMAIN

USED_DOMAIN = PROD_DOMAIN

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)s] [%(funcName)s()] %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)
logger = logging.getLogger(__name__)

# PROJECT_RESOURCE_ID = "6ced337c-4330-42b1-b44d-4b367284b30f"  # Third Project - local dev
PROJECT_RESOURCE_ID = "95abd72c-dd09-4274-aea9-ad4fcb31a49b"  # labels with reviews - prod
# PROJECT_RESOURCE_ID = "4ab65a47-293f-4cab-93f5-1ff5ca67038d"  # Project with one single image annotated - local dev
# PROJECT_RESOURCE_ID = (
#     "0db22af4-03eb-448d-92ab-3697c319334c"  # project for DICOM dataset with dynamic classifications - local dev
# )
# PROJECT_RESOURCE_ID = "efbe39ee-d8c5-4bb0-baee-48c7aaed02ec"  # Project with 3 native images in image group and dynamic classifications - local dev


def get_user_client() -> EncordUserClient:
    if USED_DOMAIN == DEV_DOMAIN:
        ssh_key = os.environ.get("SSH_KEY_DEV")
    else:
        ssh_key = os.environ.get("SSH_KEY")
    return EncordUserClient.create_with_ssh_private_key(
        ssh_key,
        domain=USED_DOMAIN,
    )


def get_project_ssh() -> Project:
    cord_user_client = get_user_client()

    return cord_user_client.get_project(PROJECT_RESOURCE_ID)


# @pytest.mark.skipif(not ENABLE_MANUAL_TESTS, reason="Manual tests are disabled")
# def test_label_structure_manual_v1():
#     project = get_project_ssh()
#     for label_row in project.label_rows:
#         label_hash = label_row["label_hash"]
#         # if label_hash is not None and label_row["data_title"] == "failing_video_new.mp4":
#         if label_hash is not None and label_row["data_title"] == "two-frame-video.mp4":
#             label_structure = project.get_label_row_class(label_hash)
#             print(label_structure)
#             break


@pytest.mark.skipif(not ENABLE_MANUAL_TESTS, reason="Manual tests are disabled")
def test_label_structure_manual_v2():
    project = get_project_ssh()
    for label_row in project.label_rows:
        print(project.get_label_row(label_row["label_hash"], include_reviews=True))

    return
    label_rows = project.list_label_rows_v2(label_hashes=["28f0e9d2-51e0-459d-8ffa-2e214da653a9"])
    print("got label rows")
    print(len(label_rows))
    label_rows[0].initialise_labels()
    print(label_rows[0].to_encord_dict())

    # for label_row in label_rows:
    #     label_row.initialise_labels()
    #     labels_1 = label_row.to_encord_dict()
    #
    #     ontology = label_row.ontology_structure
    #     box_object = ontology.get_children_by_title("box")[0]
    #     box_instance = box_object.create_instance()
    #     box_instance.set_for_frame(
    #         BoundingBoxCoordinates(
    #             height=5,
    #             width=6,
    #             top_left_x=2,
    #             top_left_y=3,
    #         ),
    #         1,
    #     )
    #
    #     label_row.add_object(box_instance)
    #     label_row.upload_labels()

    # label_row.initialise_labels()
    # labels_2 = label_row.to_encord_dict()
    # assert labels_1 == labels_2
