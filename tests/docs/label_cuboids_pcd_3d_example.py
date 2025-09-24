"""
Code Block Name: Cuboids
"""

# Import dependencies
from encord import EncordUserClient, Project
from encord.objects import ChecklistAttribute, Object, ObjectInstance, Option, RadioAttribute, TextAttribute
from encord.objects.coordinates import CuboidCoordinates

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt" # Replace with the file path to your SSH private key
PROJECT_ID = "00000000-0000-0000-0000-000000000000" # Replace with the unique ID for the Project
BUNDLE_SIZE = 100

# Create user client using ssh key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Get project for which labels are to be added
project: Project = user_client.get_project(PROJECT_ID)

# Create radio button attribute for Person type
ontology_structure = project.ontology_structure

# Find a cuboid annotation object in the project ontology
cuboid_ontology_object: Object = ontology_structure.get_child_by_title(title="Person", type_=Object)
assert cuboid_ontology_object is not None, "Cuboid object 'Person' not found in ontology."

person_type_radio_attribute = ontology_structure.get_child_by_title(type_=RadioAttribute, title="Type?")
assert person_type_radio_attribute is not None, "Radio attribute 'Type?' not found in ontology."

# Create options for the radio buttons
adult_option = person_type_radio_attribute.get_child_by_title(type_=Option, title="Adult")
adolescent_option = person_type_radio_attribute.get_child_by_title(type_=Option, title="Adolescent")
child_option = person_type_radio_attribute.get_child_by_title(type_=Option, title="Child")
other_person_option = person_type_radio_attribute.get_child_by_title(type_=Option, title="Other Person type")

assert all([adult_option, adolescent_option, child_option, other_person_option]), (
    "One or more Person type options are missing."
)

# Adult Qualities
adult_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="Adult Qualities?")
assert adult_checklist_attribute is not None, "Checklist attribute 'Adult Qualities?' not found."

adult_moving_option = adult_checklist_attribute.get_child_by_title(type_=Option, title="Moving")
adult_well_lit_option = adult_checklist_attribute.get_child_by_title(type_=Option, title="Well lit")
adult_fully_visible_option = adult_checklist_attribute.get_child_by_title(type_=Option, title="Fully visible")
assert all([adult_moving_option, adult_well_lit_option, adult_fully_visible_option]), "One or more Adult quality options are missing."

# Adolescent Qualities
adolescent_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="Adolescent Qualities?")
assert adolescent_checklist_attribute is not None, "Checklist attribute 'Adolescent Qualities?' not found."

adolescent_moving_option = adolescent_checklist_attribute.get_child_by_title(type_=Option, title="Moving")
adolescent_well_lit_option = adolescent_checklist_attribute.get_child_by_title(type_=Option, title="Well lit")
adolescent_fully_visible_option = adolescent_checklist_attribute.get_child_by_title(type_=Option, title="Fully visible")
assert all([adolescent_moving_option, adolescent_well_lit_option, adolescent_fully_visible_option]), "One or more Adolescent quality options are missing."

# Child Qualities
child_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Child Qualities?"
)
assert child_checklist_attribute is not None, "Checklist attribute 'Child Qualities?' not found."

child_moving_option = child_checklist_attribute.get_child_by_title(type_=Option, title="Moving")
child_well_lit_option = child_checklist_attribute.get_child_by_title(type_=Option, title="Well lit")
child_fully_visible_option = child_checklist_attribute.get_child_by_title(type_=Option, title="Fully visible")
assert all([child_moving_option, child_well_lit_option, child_fully_visible_option]), (
    "One or more Child quality options are missing."
)

# Other Person Types
other_person_option_text_attribute = ontology_structure.get_child_by_title(
    type_=TextAttribute, title="Specify Person type"
)
assert other_person_option_text_attribute is not None, "Text attribute 'Specify Person type' not found in ontology."

# Dictionary of labels per data unit and per frame with Person type specified, including quality options
pcd_labels = {
    "scene-1094": {
        0: {
            "label_ref": "person_001",
            "coordinates": CuboidCoordinates(position=(9, 9, 9), orientation=(0.11, 0.77, 0.33), size=(0.2, 0.2, 0.2)),
            "person_type": "Adult",
            "adult_quality_options": "Moving, Well lit",
        }
    },
    "scene-0916": {
        0: [
            {
                "label_ref": "person_002",
                "coordinates": CuboidCoordinates(position=(0.4, 0.4, 0.4), orientation=(0.0, 0.0, 0.4), size=(0.1, 0.1, 0.1)),
                "person_type": "Adolescent",
                "adolescent_quality_options": "Moving, Well lit, Fully visible",
            },
            {
                "label_ref": "person_003",
                "coordinates": CuboidCoordinates(position=(0.2, 0.2, 0.0), orientation=(0.0, 0.0, 0.1), size=(0.5, 0.5, 0.5)),
                "person_type": "Child",
                "child_quality_options": "Moving",
            },
            {
                "label_ref": "person_004",
                "coordinates": CuboidCoordinates(position=(0.2, 0.2, 0.0), orientation=(0.0, 0.0, 0.1), size=(0.7, 0.7, 0.7)),
                "person_type": "Other Person type",
                "Specify Person type": "Morello",
            },
        ],
    },
    "scene-0796": {
        0: {
            "label_ref": "person_005",
            "coordinates": CuboidCoordinates(position=(0.4, 0.4, 0.0), orientation=(0.0, 0.0, 0.4), size=(0.12, 0.12, 0.12)),
            "person_type": "Adult",
            "adult_quality_options": "Moving, Well lit",
        },
        2: [
            {
                "label_ref": "person_006",
                "coordinates": CuboidCoordinates(position=(0.1, 0.1, 0.0), orientation=(0.0, 0.0, 0.2), size=(0.5, 0.5, 0.5)),
                "person_type": "Adolescent",
                "adolescent_quality_options": "Fully visible",
            },
            {
                "label_ref": "person_007",
                "coordinates": CuboidCoordinates(position=(0.1, 0.1, 0.0), orientation=(0.0, 0.0, 0.2), size=(0.0132, 0.0132, 0.0132)),
                "person_type": "Child",
                "child_quality_options": "Moving",
            },
            {
                "label_ref": "person_008",
                "coordinates": CuboidCoordinates(position=(0.2, 0.2, 0.0), orientation=(0.0, 0.0, 0.1), size=(0.8, 0.8, 0.8)),
                "person_type": "Other Person type",
                "Specify Person type": "Person with a baby stroller",
            },
        ],
    },
    "scene-1100": {
        0: {
            "label_ref": "person_009",
            "coordinates": CuboidCoordinates(position=(0.4, 0.4, 0.0), orientation=(0.0, 0.0, 0.4), size=(0.012, 0.012, 0.012)),
            "person_type": "Adult",
            "adult_quality_options": "Moving",
        },
        3: [
            {
                "label_ref": "person_010",
                "coordinates": CuboidCoordinates(position=(0.4, 0.4, 0.0), orientation=(0.0, 0.0, 0.4), size=(0.5, 0.5, 0.5)),
                "person_type": "Adolescent",
                "adolescent_quality_options": "Moving, Well lit, Fully visible",
            },
            {
                "label_ref": "person_011",
                "coordinates": CuboidCoordinates(position=(0.3, 0.3, 0.0), orientation=(0.0, 0.0, 0.3), size=(0.13, 0.13, 0.13)),
                "person_type": "Child",
                "child_quality_options": "Moving",
            },
            {
                "label_ref": "person_012",
                "coordinates": CuboidCoordinates(position=(0.2, 0.2, 0.0), orientation=(0.0, 0.0, 0.1), size=(0.9, 0.9, 0.9)),
                "person_type": "Other Person type",
                "Specify Person type": "Lambert",
            },
        ],
    },
    "scene-0655": {
        23: [
            {
                "label_ref": "person_013",
                "coordinates": CuboidCoordinates(position=(0.5, 0.5, 0.0), orientation=(0.0, 0.0, 0.5), size=(0.11, 0.11, 0.11)),
                "person_type": "Child",
                "child_quality_options": "Moving",
            },
            {
                "label_ref": "person_014",
                "coordinates": CuboidCoordinates(position=(0.2, 0.2, 0.0), orientation=(0.0, 0.0, 0.2), size=(0.6, 0.6, 0.6)),
                "person_type": "Adult",
                "adult_quality_options": "Moving, Well lit, Fully visible",
            },
            {
                "label_ref": "person_015",
                "coordinates": CuboidCoordinates(position=(0.2, 0.2, 0.0), orientation=(0.0, 0.0, 0.1), size=(0.8, 0.8, 0.8)),
                "person_type": "Other Person type",
                "Specify Person type": "Sweetheart",
            },
        ],
        24: [
            {
                "label_ref": "person_016",
                "coordinates": CuboidCoordinates(position=(0.5, 0.5, 0.0), orientation=(0.0, 0.0, 0.5), size=(0.3, 0.3, 0.3)),
                "person_type": "Child",
                "child_quality_options": "Moving",
            },
            {
                "label_ref": "person_014",
                "coordinates": CuboidCoordinates(position=(0.2, 0.2, 0.0), orientation=(0.0, 0.0, 0.2), size=(0.6, 0.6, 0.6)),
                "person_type": "Adult",
                "adult_quality_options": "Moving, Well lit, Fully visible",
            },
            {
                "label_ref": "person_017",
                "coordinates": CuboidCoordinates(position=(0.2, 0.2, 0.0), orientation=(0.0, 0.0, 0.1), size=(0.8, 0.8, 0.8)),
                "person_type": "Other Person type",
                "Specify Person type": "Sweetheart",
            },
        ],
        25: [
            {
                "label_ref": "person_016",
                "coordinates": CuboidCoordinates(position=(0.5, 0.5, 0.0), orientation=(0.0, 0.0, 0.5), size=(0.1, 0.1, 0.1)),
                "person_type": "Child",
                "child_quality_options": "Moving",
            },
            {
                "label_ref": "person_014",
                "coordinates": CuboidCoordinates(position=(0.2, 0.2, 0.0), orientation=(0.0, 0.0, 0.2), size=(0.6, 0.6, 0.6)),
                "person_type": "Adult",
                "adult_quality_options": "Moving, Well lit, Fully visible",
            },
            {
                "label_ref": "person_017",
                "coordinates": CuboidCoordinates(position=(0.2, 0.2, 0.0), orientation=(0.0, 0.0, 0.1), size=(0.8, 0.8, 0.8)),
                "person_type": "Other Person type",
                "Specify Person type": "Sweetheart",
            },
        ],
    },
}


# Cache initialized label rows
label_row_map = {}

# Step 1: Initialize all label rows using a bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for data_unit in pcd_labels.keys():
        label_rows = project.list_label_rows_v2(data_title_eq=data_unit)
        assert isinstance(label_rows, list), f"Expected list of label rows for '{data_unit}', got {type(label_rows)}"

        if not label_rows:
            print(f"Skipping: No label row found for {data_unit}")
            continue

        label_row = label_rows[0]
        label_row.initialise_labels(bundle=bundle)
        assert label_row.ontology_structure is not None, f"Ontology not initialized for label row: {data_unit}"

        label_row_map[data_unit] = label_row  # Cache initialized label row for later use

# Step 2: Process all frames/annotations and prepare label rows to save
label_rows_to_save = []

for data_unit, frame_coordinates in pcd_labels.items():
    label_row = label_row_map.get(data_unit)
    if not label_row:
        print(f"Skipping: No initialized label row found for {data_unit}")
        continue

    object_instances_by_label_ref = {}

    # Loop through the frames for the current data unit
    for frame_number, items in frame_coordinates.items():
        assert isinstance(frame_number, int), f"Frame number must be int, got {type(frame_number)}"
        if not isinstance(items, list):
            items = [items]

        for item in items:
            label_ref = item["label_ref"]
            coord = item["coordinates"]
            person_type = item["person_type"]

            assert person_type in {
                "Adult",
                "Adolescent",
                "Child",
                "Other Person type",
            }, f"Unexpected Person type '{person_type}' in data unit '{data_unit}'"

            # Check if label_ref already exists for reusability
            if label_ref not in object_instances_by_label_ref:
                cuboid_object_instance: ObjectInstance = cuboid_ontology_object.create_instance()
                assert cuboid_object_instance is not None, "Failed to create ObjectInstance"

                object_instances_by_label_ref[label_ref] = cuboid_object_instance
                checklist_attribute = None

                # Set Person type attribute
                if person_type == "Adult":
                    assert adult_option is not None, "Missing 'adult_option'"
                    cuboid_object_instance.set_answer(attribute=person_type_radio_attribute, answer=adult_option)
                    checklist_attribute = adult_checklist_attribute
                elif person_type == "Adolescent":
                    assert adolescent_option is not None, "Missing 'adolescent_option'"
                    cuboid_object_instance.set_answer(attribute=person_type_radio_attribute, answer=adolescent_option)
                    checklist_attribute = adolescent_checklist_attribute
                elif person_type == "Child":
                    assert child_option is not None, "Missing 'child_option'"
                    cuboid_object_instance.set_answer(attribute=person_type_radio_attribute, answer=child_option)
                    checklist_attribute = child_checklist_attribute
                elif person_type == "Other Person type":
                    assert other_person_option is not None, "Missing 'other_person_option'"
                    cuboid_object_instance.set_answer(attribute=person_type_radio_attribute, answer=other_person_option)
                    text_answer = item.get("Specify Person type", "")
                    assert isinstance(text_answer, str), "'Specify Person type' must be a string"
                    cuboid_object_instance.set_answer(attribute=other_person_option_text_attribute, answer=text_answer)

                # Set checklist attributes
                checklist_answers = []
                quality_key = f"{person_type.lower()}_quality_options"
                quality_options = item.get(quality_key, "").split(", ")

                for quality in quality_options:
                    if quality == "Moving":
                        checklist_answers.append(
                            adult_moving_option
                            if person_type == "Adult"
                            else adolescent_moving_option
                            if person_type == "Adolescent"
                            else child_moving_option
                        )
                    elif quality == "Well lit":
                        checklist_answers.append(
                            adult_well_lit_option
                            if person_type == "Adult"
                            else adolescent_well_lit_option
                            if person_type == "Adolescent"
                            else child_well_lit_option
                        )
                    elif quality == "Fully visible":
                        checklist_answers.append(
                            adult_fully_visible_option
                            if person_type == "Adult"
                            else adolescent_fully_visible_option
                            if person_type == "Adolescent"
                            else child_fully_visible_option
                        )

                if checklist_attribute and checklist_answers:
                    cuboid_object_instance.set_answer(
                        attribute=checklist_attribute, answer=checklist_answers, overwrite=True
                    )

            else:
                # Reuse existing instance across frames
                cuboid_object_instance = object_instances_by_label_ref[label_ref]

            # Assign the object to the frame and track it
            cuboid_object_instance.set_for_frames(coordinates=coord, frames=frame_number)

    # Add object instances to label_row **only if they have frames assigned**
    for cuboid_object_instance in object_instances_by_label_ref.values():
        assert isinstance(cuboid_object_instance, ObjectInstance), "Expected ObjectInstance type"
        if cuboid_object_instance.get_annotation_frames():  # Ensures it has at least one frame
            label_row.add_object_instance(cuboid_object_instance)

    label_rows_to_save.append(label_row)

# Step 3: Save all label rows using a bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for label_row in label_rows_to_save:
        assert label_row is not None, "Trying to save a None label row"
        label_row.save(bundle=bundle)
        print(f"Saved label row for {label_row.data_title}")

print("Labels with Person type radio buttons, checklist attributes, and text labels added for all data units.")
