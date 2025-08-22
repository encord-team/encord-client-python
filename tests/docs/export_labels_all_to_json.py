"""
Code Block Name: Export labels to JSON
"""

# Import dependencies
import json
import os

from encord import EncordUserClient

SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"  # Replace with file path to your SSH private key
PROJECT_ID = "00000000-0000-0000-0000-000000000000"  # Replace with Project unique ID
BUNDLE_SIZE = 100  # Customize as needed
OUTPUT_JSON = "/Users/chris-encord/export-label-rows.json"  # Replace with file path to save JSON output file

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Specify Project
project = user_client.get_project(PROJECT_ID)
assert project is not None, f"Project with ID {PROJECT_ID} could not be loaded"

# Get label rows for your Project
label_rows = project.list_label_rows_v2(include_children=True, include_all_label_branches=True)
assert label_rows, f"No label rows found in project {PROJECT_ID}"

# Initialize label rows using bundles
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for label_row in label_rows:
        label_row.initialise_labels(bundle=bundle)

# Collect all label row data
all_label_rows = [label_row.to_encord_dict() for label_row in label_rows]
assert all_label_rows, "No label row data collected for export"

# Save the collected label rows data to a JSON file
output_file = OUTPUT_JSON
assert output_file.endswith(".json"), "Output file must be a .json file"

with open(output_file, "w") as file:
    json.dump(all_label_rows, file, indent=4)

print(f"Label rows have been saved to {output_file}.")