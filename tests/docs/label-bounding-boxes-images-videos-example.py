# Import dependencies
from encord import EncordUserClient, Project
from encord.objects import ChecklistAttribute, Object, ObjectInstance, Option, RadioAttribute, TextAttribute
from encord.objects.coordinates import BoundingBoxCoordinates

SSH_PATH = "/Users/laverne-encord/prod-sdk-ssh-key-private-key.txt"
# SSH_PATH = get_ssh_key() # replace it with ssh key
PROJECT_ID = "8d73bec0-ac61-4d28-b45a-7bffdf4c6b8e"
BUNDLE_SIZE = 100

# Create user client using ssh key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Get project for which labels are to be added
project: Project = user_client.get_project(PROJECT_ID)

# Create radio button attribute for cherry type
ontology_structure = project.ontology_structure

# Find a bounding box annotation object in the project ontology
box_ontology_object: Object = ontology_structure.get_child_by_title(title="Cherries", type_=Object)
assert box_ontology_object is not None, "Bounding box object 'Cherries' not found in ontology."

cherry_type_radio_attribute = ontology_structure.get_child_by_title(type_=RadioAttribute, title="Type?")
assert cherry_type_radio_attribute is not None, "Radio attribute 'Type?' not found in ontology."

# Create options for the radio buttons
bing_option = cherry_type_radio_attribute.get_child_by_title(type_=Option, title="Bing")
king_option = cherry_type_radio_attribute.get_child_by_title(type_=Option, title="King")
rainier_option = cherry_type_radio_attribute.get_child_by_title(type_=Option, title="Rainier")
other_cherry_option = cherry_type_radio_attribute.get_child_by_title(type_=Option, title="Other cherry type")

assert all([bing_option, king_option, rainier_option, other_cherry_option]), "One or more cherry type options are missing."

# Bing Qualities
bing_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="Bing Qualities?")
assert bing_checklist_attribute is not None, "Checklist attribute 'Bing Qualities?' not found."

bing_plump_option = bing_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
bing_juicy_option = bing_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
bing_large_option = bing_checklist_attribute.get_child_by_title(type_=Option, title="Large")
assert all([bing_plump_option, bing_juicy_option, bing_large_option]), "One or more Bing quality options are missing."

# King Qualities
king_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="King Qualities?")
assert king_checklist_attribute is not None, "Checklist attribute 'King Qualities?' not found."

king_plump_option = king_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
king_juicy_option = king_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
king_large_option = king_checklist_attribute.get_child_by_title(type_=Option, title="Large")
assert all([king_plump_option, king_juicy_option, king_large_option]), "One or more King quality options are missing."

# Rainier Qualities
rainier_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Rainier Qualities?"
)
assert rainier_checklist_attribute is not None, "Checklist attribute 'Rainier Qualities?' not found."

rainier_plump_option = rainier_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
rainier_juicy_option = rainier_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
rainier_large_option = rainier_checklist_attribute.get_child_by_title(type_=Option, title="Large")
assert all([rainier_plump_option, rainier_juicy_option, rainier_large_option]), "One or more Rainier quality options are missing."

# Other Cherry Types
other_cherry_option_text_attribute = ontology_structure.get_child_by_title(
    type_=TextAttribute, title="Specify cherry type"
)
assert other_cherry_option_text_attribute is not None, "Text attribute 'Specify cherry type' not found in ontology."

# Dictionary of labels per data unit and per frame with cherry type specified, including quality options
video_frame_labels = {
    "cherries-001.jpg": {
        0: {
            "label_ref": "cherry_001",
            "coordinates": BoundingBoxCoordinates(height=0.4, width=0.4, top_left_x=0.1, top_left_y=0.1),
            "cherry_type": "Bing",
            "bing_quality_options": "Plump, Juicy",
        }
    },
    "cherries-010.jpg": {
        0: [
            {
                "label_ref": "cherry_002",
                "coordinates": BoundingBoxCoordinates(height=0.4, width=0.4, top_left_x=0.1, top_left_y=0.1),
                "cherry_type": "King",
                "king_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "cherry_003",
                "coordinates": BoundingBoxCoordinates(height=0.2, width=0.1, top_left_x=0.5, top_left_y=0.5),
                "cherry_type": "Rainier",
                "rainier_quality_options": "Plump",
            },
            {
                "label_ref": "cherry_004",
                "coordinates": BoundingBoxCoordinates(height=0.2, width=0.1, top_left_x=0.5, top_left_y=0.5),
                "cherry_type": "Other cherry type",
                "Specify cherry type": "Morello",
            },
        ],
    },
    "cherries-ig": {
        0: {
            "label_ref": "cherry_005",
            "coordinates": BoundingBoxCoordinates(height=0.4, width=0.4, top_left_x=0.1, top_left_y=0.1),
            "cherry_type": "Bing",
            "bing_quality_options": "Plump, Juicy",
        },
        2: [
            {
                "label_ref": "cherry_006",
                "coordinates": BoundingBoxCoordinates(height=0.1, width=0.2, top_left_x=0.3, top_left_y=0.2),
                "cherry_type": "King",
                "king_quality_options": "Large",
            },
            {
                "label_ref": "cherry_007",
                "coordinates": BoundingBoxCoordinates(height=0.1, width=0.2, top_left_x=0.4, top_left_y=0.5),
                "cherry_type": "Rainier",
                "rainier_quality_options": "Plump",
            },
            {
                "label_ref": "cherry_008",
                "coordinates": BoundingBoxCoordinates(height=0.2, width=0.1, top_left_x=0.5, top_left_y=0.5),
                "cherry_type": "Other cherry type",
                "Specify cherry type": "Queen Anne",
            },
        ],
    },
    "cherries-is": {
        0: {
            "label_ref": "cherry_009",
            "coordinates": BoundingBoxCoordinates(height=0.4, width=0.4, top_left_x=0.1, top_left_y=0.1),
            "cherry_type": "Bing",
            "bing_quality_options": "Plump",
        },
        3: [
            {
                "label_ref": "cherry_010",
                "coordinates": BoundingBoxCoordinates(height=0.4, width=0.4, top_left_x=0.1, top_left_y=0.1),
                "cherry_type": "King",
                "king_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "cherry_011",
                "coordinates": BoundingBoxCoordinates(height=0.3, width=0.3, top_left_x=0.2, top_left_y=0.2),
                "cherry_type": "Rainier",
                "rainier_quality_options": "Plump",
            },
            {
                "label_ref": "cherry_012",
                "coordinates": BoundingBoxCoordinates(height=0.2, width=0.1, top_left_x=0.5, top_left_y=0.5),
                "cherry_type": "Other cherry type",
                "Specify cherry type": "Lambert",
            },
        ],
    },
    "cherries-vid-001.mp4": {
        103: [
            {
                "label_ref": "cherry_013",
                "coordinates": BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.2, top_left_y=0.0),
                "cherry_type": "Rainier",
                "rainier_quality_options": "Plump",
            },
            {
                "label_ref": "cherry_014",
                "coordinates": BoundingBoxCoordinates(height=0.2, width=0.2, top_left_x=0.1, top_left_y=0.1),
                "cherry_type": "Bing",
                "bing_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "cherry_015",
                "coordinates": BoundingBoxCoordinates(height=0.2, width=0.1, top_left_x=0.5, top_left_y=0.5),
                "cherry_type": "Other cherry type",
                "Specify cherry type": "Sweetheart",
            },
        ],
        104: [
            {
                "label_ref": "cherry_016",
                "coordinates": BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.2, top_left_y=0.2),
                "cherry_type": "Rainier",
                "rainier_quality_options": "Plump",
            },
            {
                "label_ref": "cherry_014",
                "coordinates": BoundingBoxCoordinates(height=0.2, width=0.2, top_left_x=0.1, top_left_y=0.1),
                "cherry_type": "Bing",
                "bing_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "cherry_017",
                "coordinates": BoundingBoxCoordinates(height=0.2, width=0.1, top_left_x=0.5, top_left_y=0.5),
                "cherry_type": "Other cherry type",
                "Specify cherry type": "Sweetheart",
            },
        ],
        105: [
            {
                "label_ref": "cherry_016",
                "coordinates": BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.2, top_left_y=0.2),
                "cherry_type": "Rainier",
                "rainier_quality_options": "Plump",
            },
            {
                "label_ref": "cherry_014",
                "coordinates": BoundingBoxCoordinates(height=0.2, width=0.2, top_left_x=0.1, top_left_y=0.1),
                "cherry_type": "Bing",
                "bing_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "cherry_017",
                "coordinates": BoundingBoxCoordinates(height=0.2, width=0.1, top_left_x=0.5, top_left_y=0.5),
                "cherry_type": "Other cherry type",
                "Specify cherry type": "Sweetheart",
            },
        ],
    },
}

# Cache initialized label rows
label_row_map = {}

# Step 1: Initialize all label rows using a bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for data_unit in video_frame_labels.keys():
        label_rows = project.list_label_rows_v2(data_title_eq=data_unit)
        if not label_rows:
            print(f"Skipping: No label row found for {data_unit}")
            continue

        label_row = label_rows[0]
        label_row.initialise_labels(bundle=bundle)
        label_row_map[data_unit] = label_row  # Cache initialized label row for later use

# Step 2: Process all frames/annotations and prepare label rows to save
label_rows_to_save = []

for data_unit, frame_coordinates in video_frame_labels.items():
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
            cherry_type = item["cherry_type"]

            # Check if label_ref already exists for reusability
            if label_ref not in object_instances_by_label_ref:
                box_object_instance: ObjectInstance = box_ontology_object.create_instance()
                object_instances_by_label_ref[label_ref] = box_object_instance  # Store for reuse
                checklist_attribute = None

                # Set cherry type attribute
                if cherry_type == "Bing":
                    box_object_instance.set_answer(attribute=cherry_type_radio_attribute, answer=bing_option)
                    checklist_attribute = bing_checklist_attribute
                elif cherry_type == "King":
                    box_object_instance.set_answer(attribute=cherry_type_radio_attribute, answer=king_option)
                    checklist_attribute = king_checklist_attribute
                elif cherry_type == "Rainier":
                    box_object_instance.set_answer(attribute=cherry_type_radio_attribute, answer=rainier_option)
                    checklist_attribute = rainier_checklist_attribute
                elif cherry_type == "Other cherry type":
                    box_object_instance.set_answer(attribute=cherry_type_radio_attribute, answer=other_cherry_option)
                    box_object_instance.set_answer(
                        attribute=other_cherry_option_text_attribute,
                        answer=item.get("Specify cherry type", "")
                    )

                # Set checklist attributes
                checklist_answers = []
                quality_options = item.get(f"{cherry_type.lower()}_quality_options", "").split(", ")

                for quality in quality_options:
                    if quality == "Plump":
                        checklist_answers.append(
                            bing_plump_option
                            if cherry_type == "Bing"
                            else king_plump_option
                            if cherry_type == "King"
                            else rainier_plump_option
                        )
                    elif quality == "Juicy":
                        checklist_answers.append(
                            bing_juicy_option
                            if cherry_type == "Bing"
                            else king_juicy_option
                            if cherry_type == "King"
                            else rainier_juicy_option
                        )
                    elif quality == "Large":
                        checklist_answers.append(
                            bing_large_option
                            if cherry_type == "Bing"
                            else king_large_option
                            if cherry_type == "King"
                            else rainier_large_option
                        )

                if checklist_attribute and checklist_answers:
                    box_object_instance.set_answer(
                        attribute=checklist_attribute, answer=checklist_answers, overwrite=True
                    )

            else:
                # Reuse existing instance across frames
                box_object_instance = object_instances_by_label_ref[label_ref]

            # Assign the object to the frame and track it
            box_object_instance.set_for_frames(coordinates=coord, frames=frame_number)

    # Add object instances to label_row **only if they have frames assigned**
    for box_object_instance in object_instances_by_label_ref.values():
        if box_object_instance.get_annotation_frames():  # Ensures it has at least one frame
            label_row.add_object_instance(box_object_instance)

    label_rows_to_save.append(label_row)

# Step 3: Save all label rows using a bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for label_row in label_rows_to_save:
        label_row.save(bundle=bundle)
        print(f"Saved label row for {label_row.data_title}")

print("Labels with cherry type radio buttons, checklist attributes, and text labels added for all data units.")
