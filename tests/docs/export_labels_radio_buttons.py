"""
Code Block Name: Radio buttons
"""

# Import dependencies
import json
import os

from encord import EncordUserClient
from encord.objects import ObjectInstance
from encord.objects.attributes import Attribute, RadioAttribute

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"
PROJECT_ID = "00000000-0000-0000-0000-000000000000"
DATA_UNIT = "cherries-010.jpg"
OUTPUT_FILE_PATH = "/Users/chris-encord/radio_attribute_output.json"
BUNDLE_SIZE = 100

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Get project and label rows
project = user_client.get_project(PROJECT_ID)
assert project is not None, f"Project with ID {PROJECT_ID} could not be loaded"

label_rows = project.list_label_rows_v2(data_title_eq=DATA_UNIT)
assert label_rows, f"No label rows found for data unit: {DATA_UNIT}"

# Initialize label rows using bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for label_row in label_rows:
        label_row.initialise_labels(bundle=bundle)

# Prepare data structure to collect all results
output_data = []


# Function to extract info from RadioAttribute (recursively if nested)
def extract_attributes(attribute: Attribute, object_instance: ObjectInstance, frame_number: int):
    frame_data = []

    if isinstance(attribute, RadioAttribute):
        attribute_answers = object_instance.get_answer(attribute)
        if not isinstance(attribute_answers, list):
            attribute_answers = [attribute_answers]

        for answer in attribute_answers:
            if answer is None:
                continue  # Skip empty answers

            answer_data = {
                "frame": frame_number + 1,
                "attribute_name": attribute.title,
                "attribute_hash": attribute.feature_node_hash,
                "answer_title": answer.title,
                "answer_hash": answer.feature_node_hash,
                "nested_attributes": [],
            }

            if hasattr(answer, "attributes") and answer.attributes:
                for nested_attribute in answer.attributes:
                    nested_data = extract_attributes(nested_attribute, object_instance, frame_number)
                    if nested_data:
                        answer_data["nested_attributes"].extend(nested_data)

            frame_data.append(answer_data)

    return frame_data


# Loop through label rows and extract attribute data
for label_row in label_rows:
    object_instances = label_row.get_object_instances()
    assert object_instances, f"No object instances found in label row {label_row.uid}"

    for object_instance in object_instances:
        annotations = object_instance.get_annotations()
        assert annotations, f"No annotations found for object instance {object_instance.object_hash}"

        ontology_item = object_instance.ontology_item
        assert ontology_item and ontology_item.attributes, (
            f"No ontology item or attributes found for object {object_instance.object_hash}"
        )

        for annotation in annotations:
            for attribute in ontology_item.attributes:
                attr_data = extract_attributes(attribute, object_instance, annotation.frame)
                if attr_data:
                    output_data.extend(attr_data)

# Save results to JSON
assert OUTPUT_FILE_PATH.endswith(".json"), "Output file path must end with .json"

with open(OUTPUT_FILE_PATH, "w") as f:
    json.dump(output_data, f, indent=4)

print(f"Radio attribute data saved to {OUTPUT_FILE_PATH}")
