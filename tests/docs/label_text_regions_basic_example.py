"""
Code Block Name: Text Regions - Text Files
"""

from encord import EncordUserClient, Project
from encord.objects import Object, ObjectInstance
from encord.objects.coordinates import TextCoordinates
from encord.objects.frames import Range
from encord.objects.attributes import RadioAttribute, TextAttribute, Option

# User input
# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"  # Replace with the file path to your SSH private key
PROJECT_ID = "00000000-0000-0000-0000-000000000000"  # Replace with the unique Project ID
BUNDLE_SIZE = 100

# Authorize connection to Encord
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use domain="https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Get project
project: Project = user_client.get_project(PROJECT_ID)
assert project is not None, f"Project with ID {PROJECT_ID} not found."

# Ontology verification
ontology_structure = project.ontology_structure
assert ontology_structure is not None, "Ontology structure not found in the project."

text_object: Object = ontology_structure.get_child_by_title(title="Edit", type_=Object)
assert text_object is not None, "Ontology object for 'Edit' not found."

correction_radio_attribute = ontology_structure.get_child_by_title(
    type_=RadioAttribute, title="Corrections"
)
assert correction_radio_attribute is not None, "Radio attribute 'Corrections' not found."

english_correction_option = correction_radio_attribute.get_child_by_title(
    type_=Option, title="English corrections"
)
assert english_correction_option is not None, "Option 'English corrections' not found under 'Corrections'."

english_correction_text_attribute = english_correction_option.get_child_by_title(
    type_=TextAttribute, title="Correction text"
)
assert english_correction_text_attribute is not None, (
    "Text attribute 'Correction text' not found under 'English corrections'."
)

# Labels
text_annotations = {
    "paradise-lost.txt": [
        {
            "label_ref": "text_region_001",
            "coordinates": Range(start=5000, end=5050),
            "correction_text": "This needs to be updated for clarity.",
        },
        {
            "label_ref": "text_region_002",
            "coordinates": Range(start=6000, end=6050),
            "correction_text": "Rephrase for better readability.",
        },
    ],
    "War and Peace.txt": [
        {
            "label_ref": "text_region_003",
            "coordinates": Range(start=3000, end=3050),
            "correction_text": "Grammar correction required.",
        },
        {
            "label_ref": "text_region_004",
            "coordinates": Range(start=4000, end=4050),
            "correction_text": "Check for historical accuracy.",
        },
    ],
}

# Initialize label rows
label_row_map = {}

with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for data_title in text_annotations.keys():
        label_rows = project.list_label_rows_v2(data_title_eq=data_title)
        if not label_rows:
            print(f"Skipping: No label row found for {data_title}")
            continue
        lr = label_rows[0]
        lr.initialise_labels(bundle=bundle)
        label_row_map[data_title] = lr

# Apply labels
label_rows_to_save = []

for data_title, annotations in text_annotations.items():
    lr = label_row_map.get(data_title)
    if lr is None:
        print(f"Skipping: No initialized label row found for {data_title}")
        continue

    for ann in annotations:
        coord = TextCoordinates(range=[ann["coordinates"]])

        inst: ObjectInstance = text_object.create_instance()
        inst.set_for_frames(frames=0, coordinates=coord)
        inst.set_answer(attribute=correction_radio_attribute, answer=english_correction_option)
        inst.set_answer(attribute=english_correction_text_attribute, answer=ann["correction_text"])
        lr.add_object_instance(inst)

        print(f"Added [English correction] text region {ann['label_ref']} to {data_title}")

    label_rows_to_save.append(lr)

# Save label rows
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for lr in label_rows_to_save:
        lr.save(bundle=bundle)
        print(f"Saved label row for {lr.data_title}")

print("English correction labels applied.")