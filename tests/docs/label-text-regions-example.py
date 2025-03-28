# Import dependencies
from encord import EncordUserClient, Project
from encord.objects import ChecklistAttribute, Object, ObjectInstance, Option, RadioAttribute, TextAttribute
from encord.objects.coordinates import TextCoordinates
from encord.objects.frames import Range

# User input
SSH_PATH = "/Users/laverne-encord/prod-sdk-ssh-key-private-key.txt"
PROJECT_ID = "dbb776e8-feaa-4401-97d3-52395bac6c02"
BUNDLE_SIZE = 100

# Create user client using ssh key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    domain="https://api.encord.com",
)

# Get project
project: Project = user_client.get_project(PROJECT_ID)
assert project is not None, f"Project with ID {PROJECT_ID} not found."

# Get ontology structure
ontology_structure = project.ontology_structure
assert ontology_structure is not None, "Ontology structure not found in the project."

# Find ontology object for Text Region
text_object: Object = ontology_structure.get_child_by_title(title="Edit", type_=Object)
assert text_object is not None, "Ontology object for 'Edit' not found."

# Define radio attributes for corrections
correction_radio_attribute = ontology_structure.get_child_by_title(type_=RadioAttribute, title="Corrections")
assert correction_radio_attribute is not None, "Radio attribute 'Corrections' not found."

english_correction_option = correction_radio_attribute.get_child_by_title(type_=Option, title="English corrections")
assert (
    english_correction_option is not None
), "Option 'English corrections' not found under 'Corrections' radio attribute."

chinese_correction_option = correction_radio_attribute.get_child_by_title(type_=Option, title="繁體中文修正")
assert chinese_correction_option is not None, "Option '繁體中文修正' not found under 'Corrections' radio attribute."

# Define checklist attributes for each correction type
english_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="English")
assert english_checklist_attribute is not None, "Checklist attribute 'English' not found."

en_ca_option = english_checklist_attribute.get_child_by_title(type_=Option, title="en-ca")
assert en_ca_option is not None, "Option 'en-ca' not found under 'English' checklist attribute."

en_gb_option = english_checklist_attribute.get_child_by_title(type_=Option, title="en-gb")
assert en_gb_option is not None, "Option 'en-gb' not found under 'English' checklist attribute."

en_us_option = english_checklist_attribute.get_child_by_title(type_=Option, title="en-us")
assert en_us_option is not None, "Option 'en-us' not found under 'English' checklist attribute."

chinese_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="繁體中文")
assert chinese_checklist_attribute is not None, "Checklist attribute '繁體中文' not found."

zh_tw_option = chinese_checklist_attribute.get_child_by_title(type_=Option, title="zh-tw")
assert zh_tw_option is not None, "Option 'zh-tw' not found under '繁體中文' checklist attribute."

zh_hk_option = chinese_checklist_attribute.get_child_by_title(type_=Option, title="zh-hk")
assert zh_hk_option is not None, "Option 'zh-hk' not found under '繁體中文' checklist attribute."

# Define text attributes for user-provided corrections
english_correction_text_attribute = english_correction_option.get_child_by_title(
    type_=TextAttribute, title="Correction text"
)
assert (
    english_correction_text_attribute is not None
), "Text attribute 'Correction text' not found under 'English corrections' option."

chinese_correction_text_attribute = ontology_structure.get_child_by_title(type_=TextAttribute, title="更正")
assert chinese_correction_text_attribute is not None, "Text attribute '更正' not found."

# Mapping of text files to multiple text regions with manual corrections
text_annotations = {
    "Paradise Lost.txt": [
        {
            "label_ref": "text_region_001",
            "coordinates": Range(start=5000, end=5050),
            "languages": "en-ca, en-us",
            "correction_text": "This needs to be updated for clarity.",
        },
        {
            "label_ref": "text_region_002",
            "coordinates": Range(start=6000, end=6050),
            "languages": "en-gb, en-us",
            "correction_text": "Rephrase for better readability.",
        },
    ],
    "War and Peace.txt": [
        {
            "label_ref": "text_region_003",
            "coordinates": Range(start=3000, end=3050),
            "languages": "en-ca, en-gb",
            "correction_text": "Grammar correction required.",
        },
        {
            "label_ref": "text_region_004",
            "coordinates": Range(start=4000, end=4050),
            "languages": "en-ca",
            "correction_text": "Check for historical accuracy.",
        },
    ],
}


# Cache label rows after initialization
label_row_map = {}

# First initialize label rows in a bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for data_title in text_annotations.keys():
        label_rows = project.list_label_rows_v2(data_title_eq=data_title)
        assert label_rows is not None, f"Error: label rows retrieval failed for {data_title}."

        if not label_rows:
            print(f"Skipping: No label row found for {data_title}")
            continue

        label_row = label_rows[0]
        label_row.initialise_labels(bundle=bundle)

        # Cache the initialized label row for further use
        label_row_map[data_title] = label_row
        assert data_title in label_row_map, f"Error: Label row for {data_title} not cached correctly."

# Apply annotations
label_rows_to_save = []

for data_title, annotations in text_annotations.items():
    label_row = label_row_map.get(data_title)
    assert label_row is not None, f"Error: No initialized label row found for {data_title}."

    for annotation in annotations:
        selected_languages = annotation.get("languages", "").split(", ")
        assert (
            selected_languages
        ), f"Error: No languages specified for annotation with label_ref {annotation['label_ref']}."

        # Create Object Instance for English corrections if applicable
        if any(lang in ["en-ca", "en-gb", "en-us"] for lang in selected_languages):
            english_instance: ObjectInstance = text_object.create_instance()
            assert (
                english_instance is not None
            ), f"Error: Failed to create ObjectInstance for English corrections for {annotation['label_ref']}."

            english_instance.set_for_frames(
                frames=0,
                coordinates=TextCoordinates(range=[annotation["coordinates"]]),
            )
            assert (
                english_instance.frames == 0
            ), f"Error: Frames not correctly set for English instance of {annotation['label_ref']}."
            assert english_instance.coordinates.range == [
                annotation["coordinates"]
            ], f"Error: Coordinates not correctly set for English instance of {annotation['label_ref']}."

            english_instance.set_answer(attribute=correction_radio_attribute, answer=english_correction_option)
            assert (
                english_instance.get_answer(correction_radio_attribute) == english_correction_option
            ), "Error: English correction option not set correctly."

            english_selected_options = [
                option
                for lang, option in {"en-ca": en_ca_option, "en-gb": en_gb_option, "en-us": en_us_option}.items()
                if lang in selected_languages
            ]
            assert (
                english_selected_options
            ), f"Error: No options selected for English corrections for {annotation['label_ref']}."

            if english_checklist_attribute and english_selected_options:
                english_instance.set_answer(attribute=english_checklist_attribute, answer=english_selected_options)

            english_instance.set_answer(
                attribute=english_correction_text_attribute, answer=annotation["correction_text"]
            )
            label_row.add_object_instance(english_instance)

        # Create Object Instance for Chinese corrections if applicable
        if any(lang in ["zh-tw", "zh-hk"] for lang in selected_languages):
            chinese_instance: ObjectInstance = text_object.create_instance()
            assert (
                chinese_instance is not None
            ), f"Error: Failed to create ObjectInstance for Chinese corrections for {annotation['label_ref']}."

            chinese_instance.set_for_frames(
                frames=0,
                coordinates=TextCoordinates(range=[annotation["coordinates"]]),
            )
            assert (
                chinese_instance.frames == 0
            ), f"Error: Frames not correctly set for Chinese instance of {annotation['label_ref']}."
            assert chinese_instance.coordinates.range == [
                annotation["coordinates"]
            ], f"Error: Coordinates not correctly set for Chinese instance of {annotation['label_ref']}."

            chinese_instance.set_answer(attribute=correction_radio_attribute, answer=chinese_correction_option)
            assert (
                chinese_instance.get_answer(correction_radio_attribute) == chinese_correction_option
            ), "Error: Chinese correction option not set correctly."

            chinese_selected_options = [
                option
                for lang, option in {"zh-tw": zh_tw_option, "zh-hk": zh_hk_option}.items()
                if lang in selected_languages
            ]
            assert (
                chinese_selected_options
            ), f"Error: No options selected for Chinese corrections for {annotation['label_ref']}."

            if chinese_checklist_attribute and chinese_selected_options:
                chinese_instance.set_answer(attribute=chinese_checklist_attribute, answer=chinese_selected_options)

            chinese_instance.set_answer(
                attribute=chinese_correction_text_attribute, answer=annotation["correction_text"]
            )
            label_row.add_object_instance(chinese_instance)

        print(f"Added text region {annotation['label_ref']} to {data_title}")

    label_rows_to_save.append(label_row)

# Save changes using a bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for label_row in label_rows_to_save:
        assert label_row is not None, "Error: Label row to save is None."
        label_row.save(bundle=bundle)
        print(f"Saved label row for {label_row.data_title}")

print("Multiple labels with manually provided correction text applied successfully!")
