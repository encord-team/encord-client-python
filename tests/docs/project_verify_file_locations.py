"""
Code Block Name: Verify where Project files are stored
"""

import json

from encord import EncordUserClient

# User input
SSH_PATH = "/Users/laverne-encord/prod-sdk-ssh-key-private-key.txt"
PROJECT_ID = "d59828bb-d60f-4a66-b4b0-5681c5684d5d"
OUTPUT_FILE_PATH = (
    "/Users/laverne-encord/file-locations-output.json"  # Specify the path where you want to save the JSON
)

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Specify Project. Replace <project_id> with the ID of the Project you want to export labels for.
project = user_client.get_project(PROJECT_ID)

# Collect data to be saved
output_data = []

# Retrieve and store the label rows
for log_line in project.list_label_rows_v2():
    data_list = project.get_data(log_line.data_hash, get_signed_url=True)
    output_data.append(data_list)

# Save output data to JSON file
with open(OUTPUT_FILE_PATH, "w") as json_file:
    json.dump(output_data, json_file, indent=4)

print(f"Data successfully saved to {OUTPUT_FILE_PATH}")
