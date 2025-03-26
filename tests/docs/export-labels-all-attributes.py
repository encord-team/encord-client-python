from collections.abc import Iterable
from encord import EncordUserClient
from encord.objects.attributes import Attribute, TextAttribute, RadioAttribute, ChecklistAttribute
from encord.objects import ObjectInstance
import json

# User input
SSH_PATH = "/Users/laverne-encord/prod-sdk-ssh-key-private-key.txt"
# SSH_PATH = get_ssh_key() # replace it with SSH key
PROJECT_ID = "8d73bec0-ac61-4d28-b45a-7bffdf4c6b8e"
DATA_UNIT = "cherries-010.jpg"
OUTPUT_FILE_PATH = "/Users/laverne-encord/all_attributes_output.json"  # Example: "all_attributes_output.json"
BUNDLE_SIZE = 100

# Instantiate Encord client
user_client = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH
)

# Load project and label rows
project = user_client.get_project(PROJECT_ID)
label_rows = project.list_label_rows_v2(data_title_eq=DATA_UNIT)

# Initialize label rows using bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for label_row in label_rows:
        label_row.initialise_labels(bundle=bundle)

# Container for structured results
results = []

# Function to collect and print attributes
def extract_and_print_attributes(attribute: Attribute, object_instance: ObjectInstance, frame_number: int):
    attr_data = {
        "frame": frame_number + 1,
        "attribute_name": attribute.title,
        "attribute_hash": attribute.feature_node_hash,
        "attribute_type": None,
        "answers": []
    }

    if isinstance(attribute, TextAttribute):
        attr_data["attribute_type"] = "TextAttribute"
        text_answer = object_instance.get_answer(attribute)
        attr_data["answers"].append({"text": text_answer or "No attribute answer"})

    elif isinstance(attribute, RadioAttribute):
        attr_data["attribute_type"] = "RadioAttribute"
        answer = object_instance.get_answer(attribute)
        if answer:
            answer_data = {
                "title": answer.title,
                "hash": answer.feature_node_hash,
                "nested_attributes": []
            }

            if hasattr(answer, 'attributes') and answer.attributes:
                for nested_attribute in answer.attributes:
                    nested_result = extract_and_print_attributes(nested_attribute, object_instance, frame_number)
                    if nested_result:
                        answer_data["nested_attributes"].append(nested_result)

            attr_data["answers"].append(answer_data)
        else:
            attr_data["answers"].append({"note": "No attribute answer"})

    elif isinstance(attribute, ChecklistAttribute):
        attr_data["attribute_type"] = "ChecklistAttribute"
        answers = object_instance.get_answer(attribute)
        if answers:
            if not isinstance(answers, Iterable):
                answers = [answers]
            for answer in answers:
                attr_data["answers"].append({
                    "title": answer.title,
                    "hash": answer.feature_node_hash
                })
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
    for object_instance in label_row.get_object_instances():
        for annotation in object_instance.get_annotations():
            for attribute in object_instance.ontology_item.attributes:
                extracted = extract_and_print_attributes(attribute, object_instance, annotation.frame)
                if extracted:
                    results.append(extracted)

# Save to JSON
with open(OUTPUT_FILE_PATH, "w") as f:
    json.dump(results, f, indent=4)

print(f"\nAll attribute data saved to: {OUTPUT_FILE_PATH}")
