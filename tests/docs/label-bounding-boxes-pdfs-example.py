# Import dependencies
from encord import EncordUserClient, Project
from encord.objects import ChecklistAttribute, Object, ObjectInstance, Option, RadioAttribute, TextAttribute
from encord.objects.coordinates import BoundingBoxCoordinates

SSH_PATH = "/Users/laverne-encord/staging-sdk-ssh-key-private-key.txt"
# SSH_PATH = get_ssh_key() # replace it with ssh key
PROJECT_ID = "12f1ebfb-bfdc-4682-a82b-bc20e5e01416"
BUNDLE_SIZE = 100

# Create user client
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://staging.api.encord.com",
)

# Get project
project: Project = user_client.get_project(PROJECT_ID)
ontology_structure = project.ontology_structure

# Get ontology object
box_ontology_object: Object = ontology_structure.get_child_by_title(title="PDF BB", type_=Object)
assert box_ontology_object is not None, "Bounding box object 'PDF BB' not found in ontology."

# Define radio attribute for correction types
correction_radio_attribute = ontology_structure.get_child_by_title(type_=RadioAttribute, title="Corrections BB")
assert correction_radio_attribute is not None, "Radio attribute 'Corrections BB' not found in ontology."

english_correction_option = correction_radio_attribute.get_child_by_title(type_=Option, title="English corrections")
chinese_correction_option = correction_radio_attribute.get_child_by_title(type_=Option, title="繁體中文修正")
assert all([english_correction_option, chinese_correction_option]), "One or more correction type options missing in radio attribute."

# Define checklist attributes
english_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="English")
assert english_checklist_attribute is not None, "Checklist attribute 'English' not found in ontology."

en_ca_option = english_checklist_attribute.get_child_by_title(type_=Option, title="en-ca")
en_gb_option = english_checklist_attribute.get_child_by_title(type_=Option, title="en-gb")
en_us_option = english_checklist_attribute.get_child_by_title(type_=Option, title="en-us")
assert all([en_ca_option, en_gb_option, en_us_option]), "One or more English checklist options are missing."

chinese_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="繁體中文")
assert chinese_checklist_attribute is not None, "Checklist attribute '繁體中文' not found in ontology."

zh_tw_option = chinese_checklist_attribute.get_child_by_title(type_=Option, title="zh-tw")
zh_hk_option = chinese_checklist_attribute.get_child_by_title(type_=Option, title="zh-hk")
assert all([zh_tw_option, zh_hk_option]), "One or more Chinese checklist options are missing."

# Define text attributes
english_correction_text_attribute = ontology_structure.get_child_by_title(type_=TextAttribute, title="Correction text")
assert english_correction_text_attribute is not None, "Text attribute 'Correction text' not found in ontology."

chinese_correction_text_attribute = ontology_structure.get_child_by_title(type_=TextAttribute, title="更正")
assert chinese_correction_text_attribute is not None, "Text attribute '更正' not found in ontology."

# Example label data (you can adjust this)
pdf_labels = {
    "the-iliad.pdf": {
        # Specify the page number in the PDF. In the example below, page number 103 is labeled
        103: {
            "label_ref": "pdf_label_001",
            "coordinates": BoundingBoxCoordinates(height=0.4, width=0.4, top_left_x=0.1, top_left_y=0.1),
            "correction_type": "English corrections",
            "checklist_options": "en-ca, en-gb",
            "text_correction": "Fixed typo in English text.",
        }
    },
    "dracula.pdf": {
        # Specify the page number in the PDF. In the example below, page number 17 is labeled
        17: {
            "label_ref": "pdf_label_002",
            "coordinates": BoundingBoxCoordinates(height=0.3, width=0.5, top_left_x=0.2, top_left_y=0.2),
            "correction_type": "繁體中文修正",
            "checklist_options": "zh-tw",
            "text_correction": "修正了中文繁體的標點符號。",
        }
    }
}


# Define bundle size
BUNDLE_SIZE = 100

# Cache initialized label rows
label_row_map = {}

# Step 1: Initialize all label rows using a bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for data_unit in pdf_labels.keys():
        label_rows = project.list_label_rows_v2(data_title_eq=data_unit)
        if not label_rows:
            print(f"Skipping: No label row found for {data_unit}")
            continue

        label_row = label_rows[0]
        label_row.initialise_labels(bundle=bundle)
        label_row_map[data_unit] = label_row  # Cache initialized label row for later use

# Step 2: Process all frames/annotations and prepare label rows to save
label_rows_to_save = []

for data_unit, frame_coordinates in pdf_labels.items():
    label_row = label_row_map.get(data_unit)
    if not label_row:
        print(f"Skipping: No initialized label row found for {data_unit}")
        continue

    object_instances_by_label_ref = {}

    # Loop through the frames for the current data unit
    for frame_number, items in frame_coordinates.items():
        if not isinstance(items, list):  # Single or multiple objects in the frame
            items = [items]

            for item in items:
                label_ref = item["label_ref"]
                coord = item["coordinates"]
                correction_type = item["correction_type"]
                checklist_options_str = item.get("checklist_options", "")
                text_correction = item.get("text_correction", "")

                # Check if label_ref already exists for reusability
                if label_ref not in object_instances_by_label_ref:
                    box_object_instance: ObjectInstance = box_ontology_object.create_instance()
                    object_instances_by_label_ref[label_ref] = box_object_instance  # Store for reuse

                    # Set correction type (radio attribute)
                    if correction_type == "English corrections":
                        box_object_instance.set_answer(attribute=correction_radio_attribute, answer=english_correction_option)

                        # Set checklist options for English
                        checklist_answers = []
                        for option in [opt.strip() for opt in checklist_options_str.split(",")]:
                            if option == "en-ca":
                                checklist_answers.append(en_ca_option)
                            elif option == "en-gb":
                                checklist_answers.append(en_gb_option)
                            elif option == "en-us":
                                checklist_answers.append(en_us_option)

                        if checklist_answers:
                            box_object_instance.set_answer(
                                attribute=english_checklist_attribute,
                                answer=checklist_answers,
                                overwrite=True,
                            )

                        # Set text correction
                        if text_correction:
                            box_object_instance.set_answer(attribute=english_correction_text_attribute, answer=text_correction)

                    elif correction_type == "繁體中文修正":
                        box_object_instance.set_answer(attribute=correction_radio_attribute, answer=chinese_correction_option)

                        # Set checklist options for Chinese
                        checklist_answers = []
                        for option in [opt.strip() for opt in checklist_options_str.split(",")]:
                            if option == "zh-tw":
                                checklist_answers.append(zh_tw_option)
                            elif option == "zh-hk":
                                checklist_answers.append(zh_hk_option)

                        if checklist_answers:
                            box_object_instance.set_answer(
                                attribute=chinese_checklist_attribute,
                                answer=checklist_answers,
                                overwrite=True,
                            )

                        # Set text correction
                        if text_correction:
                            box_object_instance.set_answer(attribute=chinese_correction_text_attribute, answer=text_correction)

                else:
                    # Reuse existing instance across pages/frames
                    box_object_instance = object_instances_by_label_ref[label_ref]

                # Assign the object to the page/frame and track it
                box_object_instance.set_for_frames(coordinates=coord, frames=frame_number)

        # Add object instances to label_row **only if they have pages/frames assigned**
        for box_object_instance in object_instances_by_label_ref.values():
            if box_object_instance.get_annotation_frames():  # Ensures it has at least one page/frame
                label_row.add_object_instance(box_object_instance)

        # Save label row using the bundle
        label_row.save(bundle=bundle)

print("Labels with English and Mandarin corrections have been added for all data units.")
