"""
Code Block Name: Move all tasks to COMPLETE
"""

# Import dependencies
from encord.user_client import EncordUserClient

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"
PROJECT_ID = "00000000-0000-0000-0000-000000000000"

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Open the project you want to work on by specifying the Project ID
project = user_client.get_project(PROJECT_ID)

# Create a bundle
with project.create_bundle() as bundle:
    # Move all tasks into the final stage of the Workflow
    for label_row in project.list_label_rows_v2():
        label_row.workflow_complete(bundle=bundle)
