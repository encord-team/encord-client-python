"""
Code Block Name: Text attributes
"""

# Import dependencies
import json

from encord import EncordUserClient
from encord.objects import ObjectInstance
from encord.objects.attributes import Attribute, TextAttribute

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"
PROJECT_ID = "00000000-0000-0000-0000-000000000000"
DATA_UNIT = "cherries-is"
OUTPUT_FILE_PATH = "/Users/chris-encord/text_attributes_output.json"
BUNDLE_SIZE = 100

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Specify Project
project = user_client.get_project(PROJECT_ID)
assert project is not None, f"Project with ID {PROJECT_ID} could not be loaded"

# Filter label rows for a specific data title
label_rows = project.list_label_rows_v2(data_title_eq=DATA_UNIT)
assert label_rows, f"No label rows found for data title '{DATA_UNIT}'"

# Initialize labels using bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for label_row in label_rows:
        label_row.initialise_labels(bundle=bundle)


# Function to extract text attributes and store in structured format
def extract_text_attributes(attribute: Attribute, object_instance: ObjectInstance, frame_number: int):
    if isinstance(attribute, TextAttribute):
        text_answer = object_instance.get_answer(attribute)
        return {
            "frame": frame_number + 1,
            "attribute_name": attribute.title,
            "attribute_hash": attribute.feature_node_hash,
            "text_answer": text_answer,
        }
    return None


# Collect results for saving
results = []

# Iterate through all object instances and collect text attribute data
for label_row in label_rows:
    object_instances = label_row.get_object_instances()
    assert object_instances, f"No object instances found in label row {label_row.uid}"

    for object_instance in object_instances:
        annotations = object_instance.get_annotations()
        assert annotations, f"No annotations found for object instance {object_instance.object_hash}"

        ontology_item = object_instance.ontology_item
        assert ontology_item and ontology_item.attributes, (
            f"Missing ontology item or attributes for object {object_instance.object_hash}"
        )

        for annotation in annotations:
            for attribute in ontology_item.attributes:
                attr_data = extract_text_attributes(attribute, object_instance, annotation.frame)
                if attr_data:
                    results.append(attr_data)
                    # Optional: also print to console
                    print(f"Frame {attr_data['frame']}:")
                    print(f"Text Attribute name: {attr_data['attribute_name']}")
                    print(f"Text Attribute hash: {attr_data['attribute_hash']}")
                    print(f"Text Attribute Answer: {attr_data['text_answer']}")

# Save results to JSON
assert OUTPUT_FILE_PATH.endswith(".json"), "Output file path must end with .json"

with open(OUTPUT_FILE_PATH, "w") as f:
    json.dump(results, f, indent=4)

print(f"\nText attribute data saved to: {OUTPUT_FILE_PATH}")
