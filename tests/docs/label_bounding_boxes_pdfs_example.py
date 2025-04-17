"""
Code Block Name: Bitmasks PDFs
"""

# Import dependencies
from encord import EncordUserClient, Project
from encord.objects import ChecklistAttribute, Object, ObjectInstance, Option, RadioAttribute, TextAttribute
from encord.objects.coordinates import BoundingBoxCoordinates

SSH_PATH = "/Users/laverne-encord/staging-sdk-ssh-key-private-key.txt"
# SSH_PATH = get_ssh_key() # replace it with ssh key
PROJECT_ID = "f8b81f75-d1d5-4cb8-895b-44db9957392e"
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
assert all(
    [english_correction_option, chinese_correction_option]
), "One or more correction type options missing in radio attribute."

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
    },
}

# === Step 1: Initialize all label rows using a bundle ===

label_row_map = {}

with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for data_unit in pdf_labels.keys():
        label_rows = project.list_label_rows_v2(data_title_eq=data_unit)
        assert isinstance(label_rows, list), f"[ASSERT] Expected a list of label rows for {data_unit}"
        if not label_rows:
            print(f"[SKIP] No label row found for {data_unit}")
            continue

        label_row = label_rows[0]
        try:
            label_row.initialise_labels(bundle=bundle)
            label_row_map[data_unit] = label_row
            print(f"[INIT] Initialized label row for: {data_unit}")
        except Exception as e:
            raise AssertionError(f"[ASSERT] Failed to initialize label row for {data_unit}: {e}")

# === Step 2: Process all frames/annotations and prepare label rows to save ===

for data_unit, frame_coordinates in pdf_labels.items():
    label_row = label_row_map.get(data_unit)
    assert label_row is not None, f"[ASSERT] Missing initialized label row for {data_unit}"

    object_instances_by_label_ref = {}

    for frame_number, items in frame_coordinates.items():
        if not isinstance(items, list):  # Handle single vs list
            items = [items]

        for item in items:
            label_ref = item["label_ref"]
            coord = item["coordinates"]
            correction_type = item["correction_type"]
            checklist_options_str = item.get("checklist_options", "")
            text_correction = item.get("text_correction", "")

            if label_ref not in object_instances_by_label_ref:
                box_object_instance: ObjectInstance = box_ontology_object.create_instance()
                assert box_object_instance is not None, f"[ASSERT] Failed to create ObjectInstance for {label_ref}"
                object_instances_by_label_ref[label_ref] = box_object_instance

                if correction_type == "English corrections":
                    assert english_correction_option is not None, "[ASSERT] english_correction_option not defined"
                    box_object_instance.set_answer(
                        attribute=correction_radio_attribute, answer=english_correction_option
                    )

                    checklist_answers = []
                    for option in [opt.strip() for opt in checklist_options_str.split(",")]:
                        if option == "en-ca":
                            checklist_answers.append(en_ca_option)
                        elif option == "en-gb":
                            checklist_answers.append(en_gb_option)
                        elif option == "en-us":
                            checklist_answers.append(en_us_option)
                        else:
                            raise AssertionError(f"[ASSERT] Unknown English checklist option: {option}")

                    if checklist_answers:
                        assert (
                            english_checklist_attribute is not None
                        ), "[ASSERT] english_checklist_attribute not defined"
                        box_object_instance.set_answer(
                            attribute=english_checklist_attribute,
                            answer=checklist_answers,
                            overwrite=True,
                        )

                    if text_correction:
                        assert (
                            english_correction_text_attribute is not None
                        ), "[ASSERT] english_correction_text_attribute not defined"
                        box_object_instance.set_answer(
                            attribute=english_correction_text_attribute, answer=text_correction
                        )

                elif correction_type == "繁體中文修正":
                    assert chinese_correction_option is not None, "[ASSERT] chinese_correction_option not defined"
                    box_object_instance.set_answer(
                        attribute=correction_radio_attribute, answer=chinese_correction_option
                    )

                    checklist_answers = []
                    for option in [opt.strip() for opt in checklist_options_str.split(",")]:
                        if option == "zh-tw":
                            checklist_answers.append(zh_tw_option)
                        elif option == "zh-hk":
                            checklist_answers.append(zh_hk_option)
                        else:
                            raise AssertionError(f"[ASSERT] Unknown Chinese checklist option: {option}")

                    if checklist_answers:
                        assert (
                            chinese_checklist_attribute is not None
                        ), "[ASSERT] chinese_checklist_attribute not defined"
                        box_object_instance.set_answer(
                            attribute=chinese_checklist_attribute,
                            answer=checklist_answers,
                            overwrite=True,
                        )

                    if text_correction:
                        assert (
                            chinese_correction_text_attribute is not None
                        ), "[ASSERT] chinese_correction_text_attribute not defined"
                        box_object_instance.set_answer(
                            attribute=chinese_correction_text_attribute, answer=text_correction
                        )

            else:
                # Reuse existing instance
                box_object_instance = object_instances_by_label_ref[label_ref]

            box_object_instance.set_for_frames(coordinates=coord, frames=frame_number)

    for box_object_instance in object_instances_by_label_ref.values():
        assert box_object_instance.get_annotation_frames(), "[ASSERT] Object instance has no frames assigned"
        label_row.add_object_instance(box_object_instance)

    try:
        label_row.save()
        print(f"[SAVE] Label row saved for {data_unit}")
    except Exception as e:
        raise AssertionError(f"[ASSERT] Failed to save label row for {data_unit}: {e}")

print("\n[COMPLETE] Labels with English and Mandarin corrections have been added for all data units.")
