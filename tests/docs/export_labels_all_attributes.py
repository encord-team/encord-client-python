"""
Code Block Name: All attributes
"""

# Import dependencies
import json
from collections.abc import Iterable
from typing import Any, Optional, TypedDict, Union

from encord import EncordUserClient
from encord.objects import ObjectInstance, Option
from encord.objects.attributes import Attribute, ChecklistAttribute, RadioAttribute, TextAttribute

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"
# SSH_PATH = get_ssh_key() # replace it with SSH key
PROJECT_ID = "00000000-0000-0000-0000-000000000000"
DATA_UNIT = "cherries-010.jpg"
OUTPUT_FILE_PATH = "/Users/chris-encord/all_attributes_output.json"
BUNDLE_SIZE = 100

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Load project and label rows
project = user_client.get_project(PROJECT_ID)
assert project is not None, f"Project with ID {PROJECT_ID} could not be loaded"

label_rows = project.list_label_rows_v2(data_title_eq=DATA_UNIT)
assert label_rows, f"No label rows found for data unit: {DATA_UNIT}"

# Initialize label rows using bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for label_row in label_rows:
        label_row.initialise_labels(bundle=bundle)

# Container for structured results
results = []


class AnswerData(TypedDict):
    title: str
    hash: str
    nested_attributes: list["AttrData"]


class AttrData(TypedDict):
    frame: int
    attribute_name: str
    attribute_hash: str
    attribute_type: Optional[str]
    answers: list[Union[AnswerData, dict[str, Any]]]


# Function to collect and print attributes
def extract_and_print_attributes(attribute: Attribute, object_instance: ObjectInstance, frame_number: int) -> AttrData:
    attr_data: AttrData = {
        "frame": frame_number + 1,
        "attribute_name": attribute.title,
        "attribute_hash": attribute.feature_node_hash,
        "attribute_type": None,
        "answers": [],
    }

    if isinstance(attribute, TextAttribute):
        attr_data["attribute_type"] = "TextAttribute"
        text_answer = object_instance.get_answer(attribute)
        attr_data["answers"].append({"text": text_answer or "No attribute answer"})

    elif isinstance(attribute, RadioAttribute):
        attr_data["attribute_type"] = "RadioAttribute"
        radio_answer = object_instance.get_answer(attribute)
        assert isinstance(radio_answer, Option)  # RadioAttribute answer is always an Option object
        if radio_answer:
            answer_data: AnswerData = {
                "title": radio_answer.title,
                "hash": radio_answer.feature_node_hash,
                "nested_attributes": [],
            }

            for nested_attribute in radio_answer.attributes:
                nested_result = extract_and_print_attributes(nested_attribute, object_instance, frame_number)
                if nested_result:
                    answer_data["nested_attributes"].append(nested_result)

            attr_data["answers"].append(answer_data)
        else:
            attr_data["answers"].append({"note": "No attribute answer"})

    elif isinstance(attribute, ChecklistAttribute):
        attr_data["attribute_type"] = "ChecklistAttribute"

        checklist_answers = object_instance.get_answer(attribute)
        # Answers of checklist attribute is always a list of Option objects
        assert isinstance(checklist_answers, Iterable)
        if checklist_answers:
            for checklist_answer in checklist_answers:
                assert isinstance(checklist_answer, Option)  # Enforcing type here
                attr_data["answers"].append(
                    {"title": checklist_answer.title, "hash": checklist_answer.feature_node_hash}
                )
        else:
            attr_data["answers"].append({"note": "No attribute answer"})

    # Print the same info (optional)
    print(f"Frame {attr_data['frame']}: {attr_data['attribute_type']} name: {attr_data['attribute_name']}")
    for answer in attr_data["answers"]:
        if "title" in answer:
            print(f"Answer: {answer['title']}")
            print(f"Answer hash: {answer['hash']}")
        elif "text" in answer:
            print(f"Answer: {answer['text']}")
        elif "note" in answer:
            print(f"Note: {answer['note']}")
        if "nested_attributes" in answer:
            for nested in answer["nested_attributes"]:
                print(f"Nested attribute: {nested['attribute_name']} ({nested['attribute_hash']})")

    return attr_data


# Process all label rows
for label_row in label_rows:
    object_instances = label_row.get_object_instances()
    assert object_instances, f"No object instances found in label row {label_row.label_hash}"

    for object_instance in object_instances:
        annotations = object_instance.get_annotations()
        assert annotations, f"No annotations found for object instance {object_instance.object_hash}"

        assert object_instance.ontology_item and object_instance.ontology_item.attributes, (
            f"No attributes found for object {object_instance.object_hash}"
        )

        for annotation in annotations:
            for attribute in object_instance.ontology_item.attributes:
                extracted = extract_and_print_attributes(attribute, object_instance, annotation.frame)
                if extracted:
                    results.append(extracted)

# Save to JSON
assert OUTPUT_FILE_PATH.endswith(".json"), "Output file path must be a JSON file"

with open(OUTPUT_FILE_PATH, "w") as f:
    json.dump(results, f, indent=4)

print(f"\nAll attribute data saved to: {OUTPUT_FILE_PATH}")
