"""
Code Block Name: Copy Project - Advanced
"""

# Import dependencies
from encord import EncordUserClient
from encord.orm.project import CopyDatasetAction, CopyDatasetOptions, CopyLabelsOptions, ReviewApprovalState

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"
PROJECT_ID = "00000000-0000-0000-0000-000000000000"
NEW_PROJECT_TITLE = "My New Project 001"  # Specify the new Project's title
NEW_PROJECT_DECSCRIPTION = "This new Project is for use with ACME Co."  # Specify the new Project's description
NEW_DATASET_TITLE = "My New Dataset 001"  # Specify the new Dataset's title
NEW_DATASET_DESCRIPTION = "This new Dataset is for use with My New Project 001"  # Specify the new Dataset's description
DATASET_ID_01 = "00000000-0000-0000-0000-000000000000"  # Specify a Dataset belonging to the Project being copied
DATASET_ID_02 = "00000000-0000-0000-0000-000000000000"  # Specify a Dataset belonging to the Project being copied
DATA_UNIT_ID_01 = (
    "00000000-0000-0000-0000-000000000000"  # Specify a data_hash for a data unit belonging to a Dataset being copied
)
DATA_UNIT_ID_02 = (
    "00000000-0000-0000-0000-000000000000"  # Specify a data_hash for a data unit belonging to a Dataset being copied
)
DATA_UNIT_ID_03 = (
    "00000000-0000-0000-0000-000000000000"  # Specify a data_hash for a data unit belonging to a Dataset being copied
)
DATA_UNIT_ID_04 = (
    "00000000-0000-0000-0000-000000000000"  # Specify a data_hash for a data unit belonging to a Dataset being copied
)
DATA_UNIT_ID_05 = (
    "00000000-0000-0000-0000-000000000000"  # Specify a data_hash for a data unit belonging to a Dataset being copied
)
DATA_UNIT_ID_06 = (
    "00000000-0000-0000-0000-000000000000"  # Specify a data_hash for a data unit belonging to a Dataset being copied
)
LABEL_ID_01 = "DX2mzwdT"  # Specify an objectHash for a label/classification on a data unit being copied
LABEL_ID_02 = "WNkfZ/7u"  # Specify an objectHash for a label/classification on a data unit being copied


# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Open the project you want to work on by specifying the Project ID
project = user_client.get_project(PROJECT_ID)

# Copy the project
project.copy_project(
    new_title=NEW_PROJECT_TITLE,
    new_description=NEW_PROJECT_DECSCRIPTION,
    copy_collaborators=True,  # Specify whether Project collaborators are copied to the new Project
    copy_datasets=CopyDatasetOptions(
        action=CopyDatasetAction.CLONE,  # This also creates a new Dataset
        dataset_title=NEW_DATASET_TITLE,
        dataset_description=NEW_DATASET_DESCRIPTION,
        datasets_to_data_hashes_map={
            DATASET_ID_01: [DATA_UNIT_ID_01, DATA_UNIT_ID_02, DATA_UNIT_ID_03],
            DATASET_ID_02: [DATA_UNIT_ID_04, DATA_UNIT_ID_05, DATA_UNIT_ID_06],
        },
    ),
    copy_labels=CopyLabelsOptions(
        accepted_label_statuses=[ReviewApprovalState.APPROVED],  # Copy all labels in the 'Approved' state.
        accepted_label_hashes=[LABEL_ID_01, LABEL_ID_02],  # Copy labels with the listed IDs.
    ),
)
