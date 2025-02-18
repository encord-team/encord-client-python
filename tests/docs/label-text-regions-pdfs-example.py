# Import dependencies
from pathlib import Path
from typing import List, Dict

from encord import EncordUserClient, Project
from encord.objects import ChecklistAttribute, Object, ObjectInstance, Option, RadioAttribute, TextAttribute
from encord.objects.frames import Range
from encord.objects.coordinates import TextCoordinates

# SSH and Project details
SSH_PATH = "/Users/laverne-encord/prod-sdk-ssh-key-private-key.txt"
PROJECT_ID = "dbb776e8-feaa-4401-97d3-52395bac6c02"

# Create user client using ssh key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    domain="https://api.encord.com",
)

# Get project
project: Project = user_client.get_project(PROJECT_ID)

# Get ontology structure
ontology_structure = project.ontology_structure

# Find ontology object for Text Region
text_object: Object = ontology_structure.get_child_by_title(title="Edit", type_=Object)
if text_object is None:
    raise ValueError("Ontology object for 'Edit' not found.")

# Define radio attributes for corrections
correction_radio_attribute = ontology_structure.get_child_by_title(type_=RadioAttribute, title="Corrections")
english_correction_option = correction_radio_attribute.get_child_by_title(type_=Option, title="English corrections")
chinese_correction_option = correction_radio_attribute.get_child_by_title(type_=Option, title="繁體中文修正")

# Define checklist attributes for each correction type
english_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="English")
en_ca_option = english_checklist_attribute.get_child_by_title(type_=Option, title="en-ca")
en_gb_option = english_checklist_attribute.get_child_by_title(type_=Option, title="en-gb")
en_us_option = english_checklist_attribute.get_child_by_title(type_=Option, title="en-us")

chinese_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="繁體中文")
zh_tw_option = chinese_checklist_attribute.get_child_by_title(type_=Option, title="zh-tw")
zh_hk_option = chinese_checklist_attribute.get_child_by_title(type_=Option, title="zh-hk")

# Define text attributes for user-provided corrections
english_correction_text_attribute = english_correction_option.get_child_by_title(type_=TextAttribute, title="Correction text")
chinese_correction_text_attribute = ontology_structure.get_child_by_title(type_=TextAttribute, title="更正")

# Mapping of text files to multiple text regions with manual corrections
text_annotations: Dict[str, List[Dict]] = {
    "Paradise Lost.txt": [
        {
            "label_ref": "text_region_001", 
            "coordinates": Range(start=5000, end=5050),
            "languages": "en-ca, en-us",
            "correction_text": "This needs to be updated for clarity."
        },
        {
            "label_ref": "text_region_002", 
            "coordinates": Range(start=6000, end=6050),
            "languages": "en-gb, en-us", 
            "correction_text": "Rephrase for better readability."
        }
    ],
    "War and Peace.txt": [
        {
            "label_ref": "text_region_003", 
            "coordinates": Range(start=3000, end=3050),
            "languages": "en-ca, en-gb",
            "correction_text": "Grammar correction required."
        },
        {
            "label_ref": "text_region_004", 
            "coordinates": Range(start=4000, end=4050), 
            "languages": "en-ca",
            "correction_text": "Check for historical accuracy."
        }
    ],
}

# Iterate over each data unit and apply multiple labels
for data_title, annotations in text_annotations.items():
    label_rows = project.list_label_rows_v2(data_title_eq=data_title)
    if not label_rows:
        print(f"Skipping: No label row found for {data_title}")
        continue
    
    label_row = label_rows[0]
    label_row.initialise_labels()

    for annotation in annotations:
        selected_languages = annotation.get("languages", "").split(", ")  # Extract languages

        # Create Object Instance for English corrections if applicable
        if any(lang in ["en-ca", "en-gb", "en-us"] for lang in selected_languages):
            english_instance: ObjectInstance = text_object.create_instance()
            english_instance.set_for_frames(
                frames=0,
                coordinates=TextCoordinates(range=[annotation["coordinates"]]),
            )
            english_instance.set_answer(attribute=correction_radio_attribute, answer=english_correction_option)

            # Apply checklist options based on provided languages
            english_selected_options = [option for lang, option in {
                "en-ca": en_ca_option, "en-gb": en_gb_option, "en-us": en_us_option
            }.items() if lang in selected_languages]

            if english_checklist_attribute and english_selected_options:
                english_instance.set_answer(attribute=english_checklist_attribute, answer=english_selected_options)

            english_instance.set_answer(attribute=english_correction_text_attribute, answer=annotation["correction_text"])
            label_row.add_object_instance(english_instance)

        # Create Object Instance for Chinese corrections if applicable
        if any(lang in ["zh-tw", "zh-hk"] for lang in selected_languages):
            chinese_instance: ObjectInstance = text_object.create_instance()
            chinese_instance.set_for_frames(
                frames=0,
                coordinates=TextCoordinates(range=[annotation["coordinates"]]),
            )
            chinese_instance.set_answer(attribute=correction_radio_attribute, answer=chinese_correction_option)

            # Apply checklist options based on provided languages
            chinese_selected_options = [option for lang, option in {
                "zh-tw": zh_tw_option, "zh-hk": zh_hk_option
            }.items() if lang in selected_languages]

            if chinese_checklist_attribute and chinese_selected_options:
                chinese_instance.set_answer(attribute=chinese_checklist_attribute, answer=chinese_selected_options)

            chinese_instance.set_answer(attribute=chinese_correction_text_attribute, answer=annotation["correction_text"])
            label_row.add_object_instance(chinese_instance)

        print(f"Added text region {annotation['label_ref']} to {data_title}")

    label_row.save()
    print(f"Saved label row for {data_title}")

print("Multiple labels with manually provided correction text applied successfully!")
