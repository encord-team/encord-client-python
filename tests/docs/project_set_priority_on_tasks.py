"""
Code Block Name: Set Priority on tasks
"""

# Import dependencies
from encord.user_client import EncordUserClient

# User input
SSH_PATH = "/Users/laverne-encord/prod-sdk-ssh-key-private-key.txt"
PROJECT_ID = "4b8756eb-eecb-415f-a212-4fb57c95b218"
BUNDLE_SIZE = 100  # You can adjust this value as needed, but keep it <= 1000

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Open the project you want to work on by specifying the Project ID
project = user_client.get_project(PROJECT_ID)

# Create a bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:

# Set the priority of all tasks in the project to 88
  for label_row in project.list_label_rows_v2():
    label_row.set_priority(0.88, bundle=bundle)

print("All task priorities changed.")