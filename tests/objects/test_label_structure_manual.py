"""
These tests will live in the SDK integration tests
"""
import logging
import os
import sys

import pytest

from encord import EncordUserClient, Project
from encord.configs import ENCORD_DOMAIN

ENABLE_MANUAL_TESTS = True


LOCAL_DOMAIN = "http://127.0.0.1:8000"
DEV_DOMAIN = "https://dev.api.encord.com"
STAGING_DOMAIN = "https://staging.api.encord.com"
PROD_DOMAIN = ENCORD_DOMAIN

USED_DOMAIN = LOCAL_DOMAIN

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)s] [%(funcName)s()] %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)
logger = logging.getLogger(__name__)

PROJECT_RESOURCE_ID = "6ced337c-4330-42b1-b44d-4b367284b30f"  # Third Project - local dev


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


@pytest.mark.skipif(not ENABLE_MANUAL_TESTS, reason="Manual tests are disabled")
def test_label_structure_manual():
    project = get_project_ssh()
    for label_row in project.label_rows:
        label_hash = label_row["label_hash"]
        if label_hash is not None and label_row["data_title"] == "failing_video_new.mp4":
            label_structure = project.get_label_row_class(label_hash)
            print(label_structure)
            break
