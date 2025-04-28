"""
Code Block Name: Remove Datasets from Project
"""

from encord import EncordUserClient, Project

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"
PROJECT_ID = "f7890e41-6de8-4e66-be06-9fbe182df457"
DATASET_ID_01 = "6ffd7c78-f585-434b-8897-1178b147aeaa"
DATASET_ID_02 = "4100d33d-e109-4e53-9c84-ba4b6bdfea79"
DATASET_ID_03 = "e0623a14-a8fd-4ed3-b491-8f785a2ba28d"

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Open the project you want to work on by specifying the Project ID
project = user_client.get_project(PROJECT_ID)

remove_these_datasets = project.remove_datasets(
    [
        DATASET_ID_01,
        DATASET_ID_02,
        DATASET_ID_03,
        # ...
    ]
)
print(f"All Datasets in the Project= {project.list_datasets()}")
