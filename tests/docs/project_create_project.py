"""
Code Block Name: Create Project
"""

# Import dependencies
from encord.user_client import EncordUserClient

# User input
SSH_PATH = "/Users/laverne-encord/prod-sdk-ssh-key-private-key.txt"
PROJECT_TITLE = "My Project 01"
DATASET_ID_01 = "ccb9438b-d9d3-4351-a243-61948f74d062"
DATASET_ID_02 = "4fc8934a-8728-4a80-9b4d-2954afe1a0b5"
DATASET_ID_03 = "26a8c7e2-9259-4853-bf0c-1b7610d4e057"
WORKFLOW_TEMPLATE_ID = "79f68604-7998-4cd3-9c68-d170b690dbb9"

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Create a project
project = user_client.create_project(
    project_title= PROJECT_TITLE,
    dataset_hashes= [DATASET_ID_01, DATASET_ID_02, DATASET_ID_03],
    workflow_template_hash= WORKFLOW_TEMPLATE_ID
)

# Prints the Project ID of the Project you just created
print(project)