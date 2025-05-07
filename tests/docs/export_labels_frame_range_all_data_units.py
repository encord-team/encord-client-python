"""
Code Block Name: Frame range for all tasks
"""

# Import dependencies
import json
from collections.abc import Iterable

from encord import EncordUserClient
from encord.objects import ObjectInstance
from encord.objects.attributes import Attribute
from encord.objects.ontology_element import OntologyElement

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"
PROJECT_ID = "8d73bec0-ac61-4d28-b45a-7bffdf4c6b8e"
OUTPUT_FILE_PATH = "/Users/chris-encord/frame_range_output.json"
START_FRAME_NUMBER = 0
END_FRAME_NUMBER = 2
BUNDLE_SIZE = 100

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Load project
project = user_client.get_project(PROJECT_ID)
assert project is not None, f"Project with ID {PROJECT_ID} could not be loaded"

# Retrieve all label rows
label_rows = project.list_label_rows_v2()
assert label_rows, "No label rows returned from the project"

# Initialize label rows using bundles
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for label_row in label_rows:
        label_row.initialise_labels(bundle=bundle)


# Function to extract attribute info
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


# Store results here
results = []

# Iterate over label rows
for label_row in label_rows:
    row_data = {
        "label_row_hash": label_row.label_hash,
        "data_title": label_row.data_title,
        "objects": [],
        "classifications": [],
    }

    # Process object annotations
    object_instances = label_row.get_object_instances()

    for object_instance in object_instances:
        annotations = object_instance.get_annotations()
        assert annotations, f"No annotations found for object instance {object_instance.object_hash}"

        ontology_item = object_instance.ontology_item
        assert (
            ontology_item and ontology_item.attributes
        ), f"Ontology item or attributes missing for object {object_instance.object_hash}"

        for annotation in annotations:
            if START_FRAME_NUMBER <= annotation.frame <= END_FRAME_NUMBER:
                obj_info = {
                    "frame": annotation.frame,
                    "object_hash": object_instance.object_hash,
                    "object_name": object_instance.object_name,
                    "feature_hash": object_instance.feature_hash,
                    "uid": str(ontology_item.uid),
                    "color": ontology_item.color,
                    "shape": ontology_item.shape,
                    "label_location": str(annotation.coordinates),
                    "attributes": [],
                }

                print("Frame:", annotation.frame)
                print("objectHash:", object_instance.object_hash)
                print("Object name:", object_instance.object_name)
                print("featureHash:", object_instance.feature_hash)
                print("uid:", obj_info["uid"])
                print("Object color:", obj_info["color"])
                print("Ontology shape:", obj_info["shape"])
                print(f"Label location: {annotation.coordinates}")

                for attribute in ontology_item.attributes:
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
                    value = answer.value
                    answer_hash = answer.feature_node_hash
                except Exception:
                    value = None
                    answer_hash = None

                classification_info = {
                    "frame": annotation.frame,
                    "classification_hash": classification_instance.classification_hash,
                    "classification_name": classification_instance.classification_name,
                    "feature_hash": classification_instance.feature_hash,
                    "value": value,
                    "answer_hash": answer_hash,
                }

                print("Classification hash:", classification_info["classification_hash"])
                print("Classification name:", classification_info["classification_name"])
                print("Feature hash:", classification_info["feature_hash"])
                print("Classification value:", classification_info["value"])
                print("Classification answer hash:", classification_info["answer_hash"])

                row_data["classifications"].append(classification_info)

    results.append(row_data)

# Save everything to JSON
assert OUTPUT_FILE_PATH.endswith(".json"), "Output file path must end with .json"

with open(OUTPUT_FILE_PATH, "w") as f:
    json.dump(results, f, indent=4)

print(f"\nAnnotation data saved to: {OUTPUT_FILE_PATH}")
