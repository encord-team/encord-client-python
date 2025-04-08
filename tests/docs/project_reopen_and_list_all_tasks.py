"""
Code Block Name: Reopen and list all tasks
"""

import json
from encord.user_client import EncordUserClient

# User input
SSH_PATH = "/Users/laverne-encord/prod-sdk-ssh-key-private-key.txt"
PROJECT_ID = "4b8756eb-eecb-415f-a212-4fb57c95b218"
OUTPUT_FILE_PATH = "/Users/laverne-encord/all-tasks-output.json"  # Specify the path where you want to save the JSON

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Open the project you want to work on by specifying the Project ID
project = user_client.get_project(PROJECT_ID)

# Collect data to be saved
output_data = []

# Create a bundle and automatically execute everything attached to the bundle
with project.create_bundle() as bundle:
    # Return all data units in the task back to the first Workflow stage
    for label_row in project.list_label_rows_v2():
        label_row.workflow_reopen(bundle=bundle)
        # Append the label row data to output_data
        output_data.append({
            'label_row_id': label_row.label_hash,
            'data': label_row.data_title
        })

# Save output data to JSON file
with open(OUTPUT_FILE_PATH, 'w') as json_file:
    json.dump(output_data, json_file, indent=4)

print(f"Data successfully saved to {OUTPUT_FILE_PATH}")
