"""
Code Block Name: All labels all branches
"""

import json

from encord import EncordUserClient

# User input
SSH_PATH = "/Users/laverne-encord/prod-sdk-ssh-key-private-key.txt"
PROJECT_ID = "8d73bec0-ac61-4d28-b45a-7bffdf4c6b8e"
OUTPUT_FILE_PATH = "/Users/laverne-encord/frame_range_output.json"
BUNDLE_SIZE = 100

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Specify Project. Replace <project_id> with the ID of the Project you want to export labels for.
project = user_client.get_project(PROJECT_ID)

# Downloads a local copy of all the labels
# Without the include_all_label_branches flag only the MAIN branch labels export
label_rows = project.list_label_rows_v2(include_all_label_branches=True)

output_data = []  # This will hold the output data to be saved as JSON

# Initialize label rows using bundles
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for label_row in label_rows:
        label_row.initialise_labels(bundle=bundle)

# Collecting data for JSON output
for label_row in label_rows:
    label_row_data = {
        "title": label_row.data_title,
        "branch": label_row.branch_name,
        "objects": [],
        "classifications": [],
    }

    # Collect object instances
    for object_instance in label_row.get_object_instances():
        object_data = {
            "object_hash": object_instance.object_hash,
            "object_name": object_instance.object_name,
            "feature_hash": object_instance.feature_hash,
            "ontology_item": {
                "uid": object_instance.ontology_item.uid,
                "color": object_instance.ontology_item.color,
                "shape": object_instance.ontology_item.shape,
                "attributes": [
                    {"name": attribute.name, "value": attribute.value}
                    for attribute in object_instance.ontology_item.attributes
                ],
            },
            "annotations": [
                {"frame": annotation.frame, "coordinates": annotation.coordinates}
                for annotation in object_instance.get_annotations()
            ],
        }
        label_row_data["objects"].append(object_data)

    # Collect classification instances
    for classification_instance in label_row.get_classification_instances():
        classification_data = {
            "classification_hash": classification_instance.classification_hash,
            "classification_name": classification_instance.classification_name,
            "feature_hash": classification_instance.feature_hash,
            "classification_answer": {
                "value": classification_instance.get_answer().value,
                "hash": classification_instance.get_answer().feature_node_hash,
            },
            "annotations": [{"frame": annotation.frame} for annotation in classification_instance.get_annotations()],
        }
        label_row_data["classifications"].append(classification_data)

    # Add label row data to the output list
    output_data.append(label_row_data)

# Saving to JSON file
output_file_path = OUTPUT_FILE_PATH  # Replace with the desired file path
with open(output_file_path, "w") as json_file:
    json.dump(output_data, json_file, indent=4)

print(f"Output saved to {output_file_path}")
