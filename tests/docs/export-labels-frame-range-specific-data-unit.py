# Import dependencies
import json

from encord import EncordUserClient
from encord.objects import ObjectInstance
from encord.objects.attributes import Attribute

# User input
SSH_PATH = "/Users/laverne-encord/prod-sdk-ssh-key-private-key.txt"
PROJECT_ID = "8d73bec0-ac61-4d28-b45a-7bffdf4c6b8e"
DATA_UNIT = "cherries-is"
OUTPUT_FILE_PATH = "/Users/laverne-encord/frame_range_output.json"
START_FRAME_NUMBER = 0
END_FRAME_NUMBER = 35
BUNDLE_SIZE = 100

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Load the project
project = user_client.get_project(PROJECT_ID)
assert project is not None, f"Project with ID {PROJECT_ID} could not be loaded"

# Get filtered label rows
label_rows = project.list_label_rows_v2(data_title_eq=DATA_UNIT)
assert label_rows, f"No label rows found for data unit: {DATA_UNIT}"

# Initialize labels using bundles
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for label_row in label_rows:
        label_row.initialise_labels(bundle=bundle)


# Function to extract attributes in a structured format
def extract_attributes(attribute: Attribute, object_instance: ObjectInstance):
    try:
        answer = object_instance.get_answer(attribute)
    except Exception:
        answer = None
    return {
        "attribute_name": attribute.title,
        "attribute_hash": attribute.feature_node_hash,
        "attribute_answer": str(answer),
    }


# Result collection
results = []

# Loop over label rows
for label_row in label_rows:
    row_data = {
        "label_row_hash": label_row.label_hash,
        "data_title": label_row.data_title,
        "objects": [],
        "classifications": [],
    }

    # Process object annotations
    object_instances = label_row.get_object_instances()
    assert object_instances, f"No object instances found in label row {label_row.uid}"

    for object_instance in object_instances:
        annotations = object_instance.get_annotations()
        assert annotations, f"No annotations found for object instance {object_instance.object_hash}"

        assert (
            object_instance.ontology_item and object_instance.ontology_item.attributes
        ), f"No attributes found for object {object_instance.object_hash}"

        for annotation in annotations:
            if START_FRAME_NUMBER <= annotation.frame <= END_FRAME_NUMBER:
                obj_info = {
                    "frame": annotation.frame,
                    "object_hash": object_instance.object_hash,
                    "object_name": object_instance.object_name,
                    "feature_hash": object_instance.feature_hash,
                    "uid": str(object_instance.ontology_item.uid),
                    "color": object_instance.ontology_item.color,
                    "shape": object_instance.ontology_item.shape,
                    "label_location": str(annotation.coordinates),
                    "attributes": [],
                }

                print("Frame:", annotation.frame)
                print("objectHash:", object_instance.object_hash)
                print("Object name:", object_instance.object_name)
                print("featureHash:", object_instance.feature_hash)
                print("uid:", obj_info["uid"])
                print("Object color:", object_instance.ontology_item.color)
                print("Ontology shape:", object_instance.ontology_item.shape)
                print(f"Label location: {annotation.coordinates}")

                for attribute in object_instance.ontology_item.attributes:
                    attr_data = extract_attributes(attribute, object_instance)
                    obj_info["attributes"].append(attr_data)

                    print(f"Attribute name: {attr_data['attribute_name']}")
                    print(f"Attribute hash: {attr_data['attribute_hash']}")
                    print(f"Attribute answer: {attr_data['attribute_answer']}")

                row_data["objects"].append(obj_info)

    # Process classification annotations
    classification_instances = label_row.get_classification_instances()
    assert classification_instances is not None, f"No classification instances found in label row {label_row.uid}"

    for classification_instance in classification_instances:
        annotations = classification_instance.get_annotations()
        assert (
            annotations
        ), f"No annotations found for classification instance {classification_instance.classification_hash}"

        for annotation in annotations:
            if START_FRAME_NUMBER <= annotation.frame <= END_FRAME_NUMBER:
                try:
                    answer = classification_instance.get_answer()
                    answer_value = answer.value
                    answer_hash = answer.feature_node_hash
                except Exception:
                    answer_value = None
                    answer_hash = None

                classification_info = {
                    "frame": annotation.frame,
                    "classification_hash": classification_instance.classification_hash,
                    "classification_name": classification_instance.classification_name,
                    "feature_hash": classification_instance.feature_hash,
                    "value": answer_value,
                    "answer_hash": answer_hash,
                }

                print("Classification hash:", classification_info["classification_hash"])
                print("Classification name:", classification_info["classification_name"])
                print("Feature hash:", classification_info["feature_hash"])
                print("Classification value:", classification_info["value"])
                print("Classification answer hash:", classification_info["answer_hash"])

                row_data["classifications"].append(classification_info)

    results.append(row_data)

# Save to JSON
assert OUTPUT_FILE_PATH.endswith(".json"), "Output file path must be a JSON file"

with open(OUTPUT_FILE_PATH, "w") as f:
    json.dump(results, f, indent=4)

print(f"\nData saved to: {OUTPUT_FILE_PATH}")
