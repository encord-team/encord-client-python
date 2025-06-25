"""
Code Block Name: Polygons PDFs
"""

# Import dependencies
from encord import EncordUserClient, Project
from encord.objects import ChecklistAttribute, Object, ObjectInstance, Option, RadioAttribute, TextAttribute
from encord.objects.coordinates import PointCoordinate, PolygonCoordinates

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"
# SSH_PATH = get_ssh_key() # replace it with ssh key
PROJECT_ID = "00000000-0000-0000-0000-000000000000"
BUNDLE_SIZE = 100

# Create user client
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Get Project
project: Project = user_client.get_project(PROJECT_ID)
assert project is not None, f"Project with ID {PROJECT_ID} not found."
ontology_structure = project.ontology_structure
assert ontology_structure is not None, "Ontology structure not found in the project."

# Get ontology object
polygon_ontology_object: Object = ontology_structure.get_child_by_title(title="PDF PG", type_=Object)
assert polygon_ontology_object is not None, "Polygon ontology object 'PDF PG' not found."

# Define radio attribute for correction types
correction_radio_attribute = ontology_structure.get_child_by_title(type_=RadioAttribute, title="Corrections PG")
assert correction_radio_attribute is not None, "Radio attribute 'Corrections PG' not found."

english_correction_option = correction_radio_attribute.get_child_by_title(type_=Option, title="English corrections")
assert english_correction_option is not None, "Option 'English corrections' not found under 'Corrections PG'."

chinese_correction_option = correction_radio_attribute.get_child_by_title(type_=Option, title="繁體中文修正")
assert chinese_correction_option is not None, "Option '繁體中文修正' not found under 'Corrections PG'."

# Define checklist attributes
english_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="English")
assert english_checklist_attribute is not None, "Checklist attribute 'English' not found."

en_ca_option = english_checklist_attribute.get_child_by_title(type_=Option, title="en-ca")
assert en_ca_option is not None, "Option 'en-ca' not found under 'English' checklist."

en_gb_option = english_checklist_attribute.get_child_by_title(type_=Option, title="en-gb")
assert en_gb_option is not None, "Option 'en-gb' not found under 'English' checklist."

en_us_option = english_checklist_attribute.get_child_by_title(type_=Option, title="en-us")
assert en_us_option is not None, "Option 'en-us' not found under 'English' checklist."

chinese_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="繁體中文")
assert chinese_checklist_attribute is not None, "Checklist attribute '繁體中文' not found."

zh_tw_option = chinese_checklist_attribute.get_child_by_title(type_=Option, title="zh-tw")
assert zh_tw_option is not None, "Option 'zh-tw' not found under '繁體中文' checklist."

zh_hk_option = chinese_checklist_attribute.get_child_by_title(type_=Option, title="zh-hk")
assert zh_hk_option is not None, "Option 'zh-hk' not found under '繁體中文' checklist."

# Define text attributes
english_correction_text_attribute = ontology_structure.get_child_by_title(type_=TextAttribute, title="Correction text")
assert english_correction_text_attribute is not None, "Text attribute 'Correction text' not found."

chinese_correction_text_attribute = ontology_structure.get_child_by_title(type_=TextAttribute, title="更正")
assert chinese_correction_text_attribute is not None, "Text attribute '更正' not found."

# Example label data (you can adjust this)
pdf_labels = {
    "the-iliad.pdf": {
        # Specify the page number in the PDF. In the example below, page number 103 is labeled
        103: {
            "label_ref": "pdf_label_001",
            "coordinates": PolygonCoordinates(
                polygons=[
                    [
                        # First rectangle
                        [
                            PointCoordinate(0.1, 0.1),
                            PointCoordinate(0.4, 0.1),
                            PointCoordinate(0.4, 0.3),
                            PointCoordinate(0.1, 0.3),
                            PointCoordinate(0.1, 0.1),  # Close the polygon
                        ]
                    ],
                    [
                        # Second rectangle
                        [
                            PointCoordinate(0.5, 0.5),
                            PointCoordinate(0.7, 0.5),
                            PointCoordinate(0.7, 0.7),
                            PointCoordinate(0.5, 0.7),
                            PointCoordinate(0.5, 0.5),  # Close the polygon
                        ]
                    ],
                ]
            ),
            "correction_type": "English corrections",
            "checklist_options": "en-ca, en-gb",
            "text_correction": "Fixed typo in English text.",
        }
    },
    "dracula.pdf": {
        # Specify the page number in the PDF. In the example below, page number 17 is labeled
        17: {
            "label_ref": "pdf_label_002",
            "coordinates": PolygonCoordinates(
                polygons=[
                    [
                        # First rectangle
                        [
                            PointCoordinate(0.2, 0.2),
                            PointCoordinate(0.5, 0.2),
                            PointCoordinate(0.5, 0.4),
                            PointCoordinate(0.2, 0.4),
                            PointCoordinate(0.2, 0.2),  # Close the polygon
                        ]
                    ],
                    [
                        # Second rectangle
                        [
                            PointCoordinate(0.6, 0.6),
                            PointCoordinate(0.8, 0.6),
                            PointCoordinate(0.8, 0.8),
                            PointCoordinate(0.6, 0.8),
                            PointCoordinate(0.6, 0.6),  # Close the polygon
                        ]
                    ],
                ]
            ),
            "correction_type": "繁體中文修正",
            "checklist_options": "zh-tw",
            "text_correction": "修正了中文繁體的標點符號。",
        }
    },
}

# === Step 1: Initialize all label rows in a single bundle ===

label_row_map = {}

with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for data_unit in pdf_labels.keys():
        label_rows = project.list_label_rows_v2(data_title_eq=data_unit)
        assert isinstance(label_rows, list), f"[ASSERT] Expected a list of label rows for {data_unit}"
        if not label_rows:
            print(f"[SKIP] No label row found for: {data_unit}")
            continue

        label_row = label_rows[0]
        try:
            label_row.initialise_labels(bundle=bundle)
            label_row_map[data_unit] = label_row
            print(f"[INIT] Initialized label row for: {data_unit}")
        except Exception as e:
            raise AssertionError(f"[ASSERT] Failed to initialize label row for {data_unit}: {e}")

# === Step 2: Apply annotations to each label row ===

for data_unit, frame_coordinates in pdf_labels.items():
    label_row = label_row_map.get(data_unit)
    assert label_row is not None, f"[ASSERT] Missing initialized label row for {data_unit}"

    object_instances_by_label_ref = {}

    for frame_number, items in frame_coordinates.items():
        if not isinstance(items, list):
            items = [items]

        for item in items:
            label_ref = item["label_ref"]
            coord = item["coordinates"]
            correction_type = item["correction_type"]
            checklist_options_str = item.get("checklist_options", "")
            text_correction = item.get("text_correction", "")

            # Basic checks
            assert correction_type in [
                "English corrections",
                "繁體中文修正",
            ], f"[ASSERT] Unknown correction type: {correction_type}"

            if label_ref not in object_instances_by_label_ref:
                polygon_object_instance: ObjectInstance = polygon_ontology_object.create_instance()
                assert polygon_object_instance is not None, f"[ASSERT] Failed to create ObjectInstance for {label_ref}"
                object_instances_by_label_ref[label_ref] = polygon_object_instance

                # Set radio attribute
                if correction_type == "English corrections":
                    assert english_correction_option is not None, "[ASSERT] english_correction_option not defined"
                    polygon_object_instance.set_answer(
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
                        assert english_checklist_attribute is not None, (
                            "[ASSERT] english_checklist_attribute not defined"
                        )
                        polygon_object_instance.set_answer(
                            attribute=english_checklist_attribute,
                            answer=checklist_answers,
                            overwrite=True,
                        )

                    if text_correction:
                        assert english_correction_text_attribute is not None, (
                            "[ASSERT] english_correction_text_attribute not defined"
                        )
                        polygon_object_instance.set_answer(
                            attribute=english_correction_text_attribute, answer=text_correction
                        )

                elif correction_type == "繁體中文修正":
                    assert chinese_correction_option is not None, "[ASSERT] chinese_correction_option not defined"
                    polygon_object_instance.set_answer(
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
                        assert chinese_checklist_attribute is not None, (
                            "[ASSERT] chinese_checklist_attribute not defined"
                        )
                        polygon_object_instance.set_answer(
                            attribute=chinese_checklist_attribute,
                            answer=checklist_answers,
                            overwrite=True,
                        )

                    if text_correction:
                        assert chinese_correction_text_attribute is not None, (
                            "[ASSERT] chinese_correction_text_attribute not defined"
                        )
                        polygon_object_instance.set_answer(
                            attribute=chinese_correction_text_attribute, answer=text_correction
                        )

            else:
                polygon_object_instance = object_instances_by_label_ref[label_ref]

            polygon_object_instance.set_for_frames(coordinates=coord, frames=frame_number)

    for polygon_object_instance in object_instances_by_label_ref.values():
        assert polygon_object_instance.get_annotation_frames(), "[ASSERT] Object instance has no frames assigned"
        label_row.add_object_instance(polygon_object_instance)

    try:
        label_row.save()
        print(f"[SAVE] Label row saved for {data_unit}")
    except Exception as e:
        raise AssertionError(f"[ASSERT] Failed to save label row for {data_unit}: {e}")

print("\n[COMPLETE] Labels with English and Mandarin corrections have been added for all data units.")
