# Import dependencies
from encord import EncordUserClient
from encord.objects.attributes import Attribute, ChecklistAttribute
from encord.objects import ObjectInstance
import json

# User input
SSH_PATH = "/Users/laverne-encord/prod-sdk-ssh-key-private-key.txt"
# SSH_PATH = get_ssh_key() # replace it with SSH key
PROJECT_ID = "8d73bec0-ac61-4d28-b45a-7bffdf4c6b8e"
DATA_UNIT = "cherries-010.jpg"
OUTPUT_FILE_PATH = "/Users/laverne-encord/checklist_attributes_output.json"  # Example: "checklist_attributes_output.json"
BUNDLE_SIZE = 100

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Load the project and filter label rows
project = user_client.get_project(PROJECT_ID)
label_rows = project.list_label_rows_v2(data_title_eq=DATA_UNIT)

# Initialize label rows using bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for label_row in label_rows:
        label_row.initialise_labels(bundle=bundle)

# Function to extract checklist attributes in structured format
def extract_attributes(attribute: Attribute, object_instance: ObjectInstance, frame_number: int):
    if isinstance(attribute, ChecklistAttribute):
        attribute_answers = object_instance.get_answer(attribute)
        if not isinstance(attribute_answers, list):
            attribute_answers = [attribute_answers]

        return {
            "frame": frame_number + 1,
            "attribute_name": attribute.title,
            "attribute_hash": attribute.feature_node_hash,
            "answers": [
                {
                    "title": answer.title,
                    "hash": answer.feature_node_hash,
                }
                for answer in attribute_answers
            ]
        }
    return None

# Collect data for saving
results = []

# Iterate through label rows and extract checklist attribute data
for label_row in label_rows:
    for object_instance in label_row.get_object_instances():
        for annotation in object_instance.get_annotations():
            for attribute in object_instance.ontology_item.attributes:
                attr_data = extract_attributes(attribute, object_instance, annotation.frame)
                if attr_data:
                    results.append(attr_data)
                    # Optional: also print to console
                    print(f"Frame {attr_data['frame']}:")
                    print(f"Checklist Attribute name: {attr_data['attribute_name']}")
                    for answer in attr_data["answers"]:
                        print(f"Checklist answer: {answer['title']}")
                        print(f"Checklist answer hash: {answer['hash']}")

# Save to JSON
with open(OUTPUT_FILE_PATH, "w") as f:
    json.dump(results, f, indent=4)

print(f"\nChecklist attribute data saved to: {OUTPUT_FILE_PATH}")
