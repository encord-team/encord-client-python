# Import dependencies
from encord import EncordUserClient
import json

SSH_PATH = "/Users/laverne-encord/prod-sdk-ssh-key-private-key.txt"
# SSH_PATH = get_ssh_key() # replace it with ssh key
PROJECT_ID = "8d73bec0-ac61-4d28-b45a-7bffdf4c6b8e"
BUNDLE_SIZE = 100  # Customize as needed

# Create user client using ssh key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Specify Project
project = user_client.get_project(PROJECT_ID)

# Get label rows for your Project
label_rows = project.list_label_rows_v2()

# Initialize label rows using bundles
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for label_row in label_rows:
        label_row.initialise_labels(bundle=bundle)

# Collect all label row data
all_label_rows = [label_row.to_encord_dict() for label_row in label_rows]

# Save the collected label rows data to a JSON file
output_file = "/Users/laverne-encord/export-label-rows.json"
with open(output_file, "w") as file:
    json.dump(all_label_rows, file, indent=4)

print(f"Label rows have been saved to {output_file}.")
