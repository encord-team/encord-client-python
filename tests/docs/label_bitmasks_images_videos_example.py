"""
Code Block Name: Bitmasks Images/Videos
"""

# Import dependencies

import numpy as np

from encord import EncordUserClient, Project
from encord.objects import ChecklistAttribute, Object, ObjectInstance, Option, RadioAttribute, TextAttribute
from encord.objects.coordinates import BitmaskCoordinates

# Prepare boolean mask with shape matching frame size
numpy_coordinates = np.ones((1080, 1920)).astype(bool)
assert numpy_coordinates.shape == (1080, 1920), "Mask dimensions must match 1080x1920"

# Paths and identifiers
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"
PROJECT_ID = "00000000-0000-0000-0000-000000000000"
BUNDLE_SIZE = 100

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Load project
project: Project = user_client.get_project(PROJECT_ID)
assert project is not None, f"Project {PROJECT_ID} could not be loaded"

# Ontology lookup with assertions
ontology_structure = project.ontology_structure
assert ontology_structure, "Ontology structure not found"

bitmask_ontology_object = ontology_structure.get_child_by_title(title="Apples", type_=Object)
assert bitmask_ontology_object is not None, "Ontology object 'Apples' not found"

apple_type_radio_attribute = ontology_structure.get_child_by_title(type_=RadioAttribute, title="Type?")
assert apple_type_radio_attribute is not None, "Radio attribute 'Type?' not found"

sugar_bee_option = apple_type_radio_attribute.get_child_by_title(type_=Option, title="Sugar Bee")
granny_smith_option = apple_type_radio_attribute.get_child_by_title(type_=Option, title="Granny Smith")
honey_crisp_option = apple_type_radio_attribute.get_child_by_title(type_=Option, title="Honey Crisp")
other_apple_option = apple_type_radio_attribute.get_child_by_title(type_=Option, title="Other apple type")
assert all([sugar_bee_option, granny_smith_option, honey_crisp_option, other_apple_option]), "Missing radio options"


# Helper for checklist + options
def assert_checklist_and_options(title, *option_titles):
    checklist = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title=title)
    assert checklist, f"Checklist '{title}' not found"
    options = [checklist.get_child_by_title(type_=Option, title=o) for o in option_titles]
    assert all(options), f"Missing options in checklist '{title}'"
    return (checklist, *options)


sugar_bee_checklist_attribute, sugar_bee_plump_option, sugar_bee_juicy_option, sugar_bee_large_option = (
    assert_checklist_and_options("Sugar Bee Qualities?", "Plump", "Juicy", "Large")
)

granny_smith_checklist_attribute, granny_smith_plump_option, granny_smith_juicy_option, granny_smith_large_option = (
    assert_checklist_and_options("Granny Smith Qualities?", "Plump", "Juicy", "Large")
)

honey_crisp_checklist_attribute, honey_crisp_plump_option, honey_crisp_juicy_option, honey_crisp_large_option = (
    assert_checklist_and_options("Honey Crisp Qualities?", "Plump", "Juicy", "Large")
)

other_apple_option_text_attribute = ontology_structure.get_child_by_title(
    type_=TextAttribute, title="Specify apple type"
)
assert other_apple_option_text_attribute is not None, "TextAttribute 'Specify apple type' not found"

video_frame_labels = {
    "cherries-001.jpg": {
        0: {
            "label_ref": "apple_001",
            "coordinates": BitmaskCoordinates(numpy_coordinates),
            "apple_type": "Sugar Bee",
            "sugar_bee_quality_options": "Plump, Juicy",
        }
    },
    "cherries-010.jpg": {
        0: [
            {
                "label_ref": "apple_002",
                "coordinates": BitmaskCoordinates(numpy_coordinates),
                "apple_type": "Granny Smith",
                "granny_smith_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "apple_003",
                "coordinates": BitmaskCoordinates(numpy_coordinates),
                "apple_type": "Honey Crisp",
                "honey_crisp_quality_options": "Plump",
            },
            {
                "label_ref": "apple_004",
                "coordinates": BitmaskCoordinates(numpy_coordinates),
                "apple_type": "Other apple type",
                "Specify apple type": "Fuji",
            },
        ],
    },
    "cherries-ig": {
        0: {
            "label_ref": "apple_005",
            "coordinates": BitmaskCoordinates(numpy_coordinates),
            "apple_type": "Sugar Bee",
            "sugar_bee_quality_options": "Plump, Juicy",
        },
        2: [
            {
                "label_ref": "apple_006",
                "coordinates": BitmaskCoordinates(numpy_coordinates),
                "apple_type": "Granny Smith",
                "granny_smith_quality_options": "Large",
            },
            {
                "label_ref": "apple_007",
                "coordinates": BitmaskCoordinates(numpy_coordinates),
                "apple_type": "Honey Crisp",
                "honey_crisp_quality_options": "Plump",
            },
            {
                "label_ref": "apple_008",
                "coordinates": BitmaskCoordinates(numpy_coordinates),
                "apple_type": "Other apple type",
                "Specify apple type": "Jazz",
            },
        ],
    },
    "cherries-is": {
        0: {
            "label_ref": "apple_009",
            "coordinates": BitmaskCoordinates(numpy_coordinates),
            "apple_type": "Sugar Bee",
            "sugar_bee_quality_options": "Plump",
        },
        3: [
            {
                "label_ref": "apple_010",
                "coordinates": BitmaskCoordinates(numpy_coordinates),
                "apple_type": "Granny Smith",
                "granny_smith_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "apple_011",
                "coordinates": BitmaskCoordinates(numpy_coordinates),
                "apple_type": "Honey Crisp",
                "honey_crisp_quality_options": "Plump",
            },
            {
                "label_ref": "apple_012",
                "coordinates": BitmaskCoordinates(numpy_coordinates),
                "apple_type": "Other apple type",
                "Specify apple type": "Red Delicious",
            },
        ],
    },
    "cherries-vid-001.mp4": {
        103: [
            {
                "label_ref": "apple_013",
                "coordinates": BitmaskCoordinates(numpy_coordinates),
                "apple_type": "Honey Crisp",
                "honey_crisp_quality_options": "Plump",
            },
            {
                "label_ref": "apple_014",
                "coordinates": BitmaskCoordinates(numpy_coordinates),
                "apple_type": "Sugar Bee",
                "sugar_bee_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "apple_015",
                "coordinates": BitmaskCoordinates(numpy_coordinates),
                "apple_type": "Other apple type",
                "Specify apple type": "Jazz",
            },
        ],
        104: [
            {
                "label_ref": "apple_016",
                "coordinates": BitmaskCoordinates(numpy_coordinates),
                "apple_type": "Honey Crisp",
                "honey_crisp_quality_options": "Plump",
            },
            {
                "label_ref": "apple_014",
                "coordinates": BitmaskCoordinates(numpy_coordinates),
                "apple_type": "Sugar Bee",
                "sugar_bee_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "apple_017",
                "coordinates": BitmaskCoordinates(numpy_coordinates),
                "apple_type": "Other apple type",
                "Specify apple type": "Fuji",
            },
        ],
        105: [
            {
                "label_ref": "apple_016",
                "coordinates": BitmaskCoordinates(numpy_coordinates),
                "apple_type": "Honey Crisp",
                "honey_crisp_quality_options": "Plump",
            },
            {
                "label_ref": "apple_014",
                "coordinates": BitmaskCoordinates(numpy_coordinates),
                "apple_type": "Sugar Bee",
                "sugar_bee_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "apple_017",
                "coordinates": BitmaskCoordinates(numpy_coordinates),
                "apple_type": "Other apple type",
                "Specify apple type": "Red Delicious",
            },
        ],
    },
}

# Cache initialized label rows
label_row_map = {}

# Step 1: Initialize all label rows
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for data_unit in video_frame_labels.keys():
        label_rows = project.list_label_rows_v2(data_title_eq=data_unit)
        assert isinstance(label_rows, list), f"Expected list of label rows for {data_unit}"
        if not label_rows:
            print(f"Skipping: No label row found for {data_unit}")
            continue
        label_row = label_rows[0]
        label_row.initialise_labels(bundle=bundle)
        label_row_map[data_unit] = label_row

label_rows_to_save = []

for data_unit, frame_coordinates in video_frame_labels.items():
    label_row = label_row_map.get(data_unit)
    if not label_row:
        print(f"⚠️ Skipping: No initialized label row found for {data_unit}")
        continue

    object_instances_by_label_ref = {}

    for frame_number, items in frame_coordinates.items():
        if not isinstance(items, list):
            items = [items]

        for item in items:
            label_ref = item["label_ref"]
            coord = item["coordinates"]
            apple_type = item["apple_type"]
            assert isinstance(coord, BitmaskCoordinates), f"Invalid coordinates for {label_ref}"

            # Reuse instance if already created
            if label_ref not in object_instances_by_label_ref:
                bitmask_object_instance: ObjectInstance = bitmask_ontology_object.create_instance()
                object_instances_by_label_ref[label_ref] = bitmask_object_instance
                checklist_attribute = None

                # Set radio attribute (apple type)
                if apple_type == "Sugar Bee":
                    bitmask_object_instance.set_answer(attribute=apple_type_radio_attribute, answer=sugar_bee_option)
                    checklist_attribute = sugar_bee_checklist_attribute
                elif apple_type == "Granny Smith":
                    bitmask_object_instance.set_answer(attribute=apple_type_radio_attribute, answer=granny_smith_option)
                    checklist_attribute = granny_smith_checklist_attribute
                elif apple_type == "Honey Crisp":
                    bitmask_object_instance.set_answer(attribute=apple_type_radio_attribute, answer=honey_crisp_option)
                    checklist_attribute = honey_crisp_checklist_attribute
                elif apple_type == "Other apple type":
                    bitmask_object_instance.set_answer(attribute=apple_type_radio_attribute, answer=other_apple_option)
                    text_value = item.get("Specify apple type", "").strip()
                    assert text_value, f"Missing text answer for 'Other apple type' in {label_ref}"
                    bitmask_object_instance.set_answer(attribute=other_apple_option_text_attribute, answer=text_value)

                # Set checklist answers
                checklist_answers = []
                quality_key = f"{apple_type.lower()}_quality_options"
                quality_list = item.get(quality_key, "")
                qualities = [q.strip() for q in quality_list.split(",") if q.strip()]

                for quality in qualities:
                    if quality == "Plump":
                        checklist_answers.append(
                            sugar_bee_plump_option
                            if apple_type == "Sugar Bee"
                            else granny_smith_plump_option
                            if apple_type == "Granny Smith"
                            else honey_crisp_plump_option
                        )
                    elif quality == "Juicy":
                        checklist_answers.append(
                            sugar_bee_juicy_option
                            if apple_type == "Sugar Bee"
                            else granny_smith_juicy_option
                            if apple_type == "Granny Smith"
                            else honey_crisp_juicy_option
                        )
                    elif quality == "Large":
                        checklist_answers.append(
                            sugar_bee_large_option
                            if apple_type == "Sugar Bee"
                            else granny_smith_large_option
                            if apple_type == "Granny Smith"
                            else honey_crisp_large_option
                        )

                if checklist_attribute and checklist_answers:
                    bitmask_object_instance.set_answer(
                        attribute=checklist_attribute, answer=checklist_answers, overwrite=True
                    )

            else:
                bitmask_object_instance = object_instances_by_label_ref[label_ref]

            # Assign coordinates for this frame
            bitmask_object_instance.set_for_frames(coordinates=coord, frames=frame_number)

    # Add valid instances to label row
    for bitmask_object_instance in object_instances_by_label_ref.values():
        assert bitmask_object_instance.get_annotation_frames(), f"No frames set for instance {bitmask_object_instance}"
        label_row.add_object_instance(bitmask_object_instance)

    label_rows_to_save.append(label_row)

with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for label_row in label_rows_to_save:
        label_row.save(bundle=bundle)
        print(f"Saved label row for: {label_row.data_title}")

print("\n🎉 Done! Labels with radio buttons, checklist attributes, and text answers have been added.")
