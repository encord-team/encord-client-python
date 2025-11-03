"""
Code Block Name: Add Datasets to Project
"""

from encord import EncordUserClient

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"
PROJECT_ID = "00000000-0000-0000-0000-000000000000"
DATASET_ID_01 = "00000000-0000-0000-0000-000000000000"
DATASET_ID_02 = "00000000-0000-0000-0000-000000000000"
DATASET_ID_03 = "00000000-0000-0000-0000-000000000000"

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Open the project you want to work on by specifying the Project ID
project = user_client.get_project(PROJECT_ID)

add_these_datasets = project.add_datasets(
    [
        DATASET_ID_01,
        DATASET_ID_02,
        DATASET_ID_03,
        # ...
    ]
)
print(f"All Datasets for Project= {project.list_datasets()}")
