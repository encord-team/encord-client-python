import numpy as np

from encord import EncordUserClient, Project
from encord.objects import ChecklistAttribute, Object, ObjectInstance, Option, RadioAttribute, TextAttribute
from encord.objects.coordinates import BitmaskCoordinates

# Prepare the bitmask
numpy_coordinates = np.ones((483, 322), dtype=bool)

# SSH and Project details
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"
PROJECT_ID = "00000000-0000-0000-0000-000000000000"

# Create user client
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    domain="https://api.encord.com",
)

# Get project
project: Project = user_client.get_project(PROJECT_ID)
ontology_structure = project.ontology_structure

# Get ontology object
text_object: Object = ontology_structure.get_child_by_title(title="Edit", type_=Object)
if text_object is None:
    raise ValueError("Ontology object for 'Edit' not found.")

# Define attributes
correction_radio_attribute = ontology_structure.get_child_by_title(type_=RadioAttribute, title="Corrections")
english_correction_option = correction_radio_attribute.get_child_by_title(type_=Option, title="English corrections")
chinese_correction_option = correction_radio_attribute.get_child_by_title(type_=Option, title="繁體中文修正")

# Define checklist attributes
english_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="English")
en_ca_option = english_checklist_attribute.get_child_by_title(type_=Option, title="en-ca")
en_gb_option = english_checklist_attribute.get_child_by_title(type_=Option, title="en-gb")
en_us_option = english_checklist_attribute.get_child_by_title(type_=Option, title="en-us")

chinese_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="繁體中文")
zh_tw_option = chinese_checklist_attribute.get_child_by_title(type_=Option, title="zh-tw")
zh_hk_option = chinese_checklist_attribute.get_child_by_title(type_=Option, title="zh-hk")

# Define text attributes
english_correction_text_attribute = ontology_structure.get_child_by_title(type_=TextAttribute, title="Correction text")
chinese_correction_text_attribute = ontology_structure.get_child_by_title(type_=TextAttribute, title="更正")

# Mapping of text files to multiple text regions
text_annotations = {
    "the-iliad.pdf": {
        103: [
            {
                "label_ref": "text_region_001",
                "coordinates": BitmaskCoordinates(numpy_coordinates),
                "languages": "en-ca, en-us",
                "correction_text": "This needs to be updated for clarity.",
            }
        ],
    },
}

# Iterate over each data unit
for data_title, annotations in text_annotations.items():
    label_rows = project.list_label_rows_v2(data_title_eq=data_title)
    if not label_rows:
        print(f"Skipping: No label row found for {data_title}")
        continue

    label_row = label_rows[0]
    label_row.initialise_labels()

    for page_number, page_annotations in annotations.items():
        for annotation in page_annotations:
            selected_languages = annotation.get("languages", "").split(", ")

            # Ensure BitmaskCoordinates
            if not isinstance(annotation["coordinates"], BitmaskCoordinates):
                raise TypeError(f"Expected BitmaskCoordinates, got {type(annotation['coordinates'])}")

            # Create object instance
            instance: ObjectInstance = text_object.create_instance()
            instance.set_for_frames(coordinates=annotation["coordinates"], frames=page_number)

            # Apply correction type
            if any(lang in ["en-ca", "en-gb", "en-us"] for lang in selected_languages):
                instance.set_answer(attribute=correction_radio_attribute, answer=english_correction_option)
                checklist_options = [
                    opt
                    for lang, opt in {"en-ca": en_ca_option, "en-gb": en_gb_option, "en-us": en_us_option}.items()
                    if lang in selected_languages
                ]
                if checklist_options:
                    instance.set_answer(attribute=english_checklist_attribute, answer=checklist_options)
                instance.set_answer(attribute=english_correction_text_attribute, answer=annotation["correction_text"])

            elif any(lang in ["zh-tw", "zh-hk"] for lang in selected_languages):
                instance.set_answer(attribute=correction_radio_attribute, answer=chinese_correction_option)
                checklist_options = [
                    opt
                    for lang, opt in {"zh-tw": zh_tw_option, "zh-hk": zh_hk_option}.items()
                    if lang in selected_languages
                ]
                if checklist_options:
                    instance.set_answer(attribute=chinese_checklist_attribute, answer=checklist_options)
                instance.set_answer(attribute=chinese_correction_text_attribute, answer=annotation["correction_text"])

            label_row.add_object_instance(instance)

    label_row.save()
    print(f"Saved label row for {data_title}")

print("Bitmask text annotations applied successfully!")
