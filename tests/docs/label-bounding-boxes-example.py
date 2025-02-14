# Import dependencies
from pathlib import Path
from encord import EncordUserClient, Project
from encord.objects import (
    Object,
    ObjectInstance,
    RadioAttribute,
    ChecklistAttribute,
    TextAttribute,
    Option
)
from encord.objects.coordinates import BoundingBoxCoordinates

SSH_PATH = "/Users/laverne-encord/prod-sdk-ssh-key-private-key.txt"
PROJECT_HASH = "8d73bec0-ac61-4d28-b45a-7bffdf4c6b8e"

# Create user client using ssh key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH
)

# Get project for which labels are to be added
project: Project = user_client.get_project(PROJECT_HASH)

# Create radio button attribute for cherry type
ontology_structure = project.ontology_structure

# Find a bounding box annotation object in the project ontology
box_ontology_object: Object = ontology_structure.get_child_by_title(
    title="Cherries", type_=Object
)

cherry_type_radio_attribute = ontology_structure.get_child_by_title(
    type_=RadioAttribute, title="Type?"
)

# Create options for the radio buttons
bing_option = cherry_type_radio_attribute.get_child_by_title(type_=Option, title="Bing")
king_option = cherry_type_radio_attribute.get_child_by_title(type_=Option, title="King")
rainier_option = cherry_type_radio_attribute.get_child_by_title(type_=Option, title="Rainier")
other_cherry_option = cherry_type_radio_attribute.get_child_by_title(type_=Option, title="Other cherry type")

# Create checklist attributes and options for each cherry type
# Bing Qualities
bing_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Bing Qualities?"
)
bing_plump_option = bing_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
bing_juicy_option = bing_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
bing_large_option = bing_checklist_attribute.get_child_by_title(type_=Option, title="Large")

# King Qualities
king_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="King Qualities?"
)
king_plump_option = king_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
king_juicy_option = king_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
king_large_option = king_checklist_attribute.get_child_by_title(type_=Option, title="Large")

# Rainier Qualities
rainier_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Rainier Qualities?"
)
rainier_plump_option = rainier_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
rainier_juicy_option = rainier_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
rainier_large_option = rainier_checklist_attribute.get_child_by_title(type_=Option, title="Large")

# Other Cherry Types
other_cherry_option_text_attribute = ontology_structure.get_child_by_title(
    type_=TextAttribute, title="Specify cherry type"
)


# Dictionary of labels per data unit and per frame with cherry type specified, including quality options
video_frame_labels = {
    "cherries-001.jpg": {
        0: {
            "label_ref": "cherry_001",
            "coordinates": BoundingBoxCoordinates(height=0.4, width=0.4, top_left_x=0.1, top_left_y=0.1), 
            "cherry_type": "Bing", 
            "bing_quality_options": "Plump, Juicy"
            }
    },
    "cherries-010.jpg": {
        0: [
            {
                "label_ref": "cherry_002", 
                "coordinates": BoundingBoxCoordinates(height=0.4, width=0.4, top_left_x=0.1, top_left_y=0.1), 
                "cherry_type": "King", 
                "king_quality_options": "Plump, Juicy, Large"
                },
            {
                "label_ref": "cherry_003",
                "coordinates": BoundingBoxCoordinates(height=0.2, width=0.1, top_left_x=0.5, top_left_y=0.5), 
                "cherry_type": "Rainier", 
                "rainier_quality_options": "Plump"
                },
            {
                "label_ref": "cherry_004", 
                "coordinates": BoundingBoxCoordinates(height=0.2, width=0.1, top_left_x=0.5, top_left_y=0.5), 
                "cherry_type": "Other cherry type", "Specify cherry type": "Morello"
                },
        ],
    },
    "cherries-ig": {
        0: {
            "label_ref": "cherry_005", 
            "coordinates": BoundingBoxCoordinates(height=0.4, width=0.4, top_left_x=0.1, top_left_y=0.1), 
            "cherry_type": "Bing", 
            "bing_quality_options": "Plump, Juicy"
            },
        2: [
            {
            "label_ref": "cherry_006", 
            "coordinates": BoundingBoxCoordinates(height=0.1, width=0.2, top_left_x=0.3, top_left_y=0.2), 
            "cherry_type": "King", 
            "king_quality_options": "Large"
            },
            {
            "label_ref": "cherry_007", 
            "coordinates": BoundingBoxCoordinates(height=0.1, width=0.2, top_left_x=0.4, top_left_y=0.5), 
            "cherry_type": "Rainier", 
            "rainier_quality_options": "Plump"
            },
            {
            "label_ref": "cherry_008", 
            "coordinates": BoundingBoxCoordinates(height=0.2, width=0.1, top_left_x=0.5, top_left_y=0.5), 
            "cherry_type": "Other cherry type", "Specify cherry type": "Queen Anne"
            },
        ]
    },
    "cherries-is": {
        0: {
            "label_ref": "cherry_009", 
            "coordinates": BoundingBoxCoordinates(height=0.4, width=0.4, top_left_x=0.1, top_left_y=0.1), 
            "cherry_type": "Bing", 
            "bing_quality_options": "Plump"
            },
        3: [
            {
            "label_ref": "cherry_010", 
            "coordinates": BoundingBoxCoordinates(height=0.4, width=0.4, top_left_x=0.1, top_left_y=0.1), 
            "cherry_type": "King", 
            "king_quality_options": "Plump, Juicy, Large"
            },
            {
            "label_ref": "cherry_011", 
            "coordinates": BoundingBoxCoordinates(height=0.3, width=0.3, top_left_x=0.2, top_left_y=0.2), 
            "cherry_type": "Rainier", 
            "rainier_quality_options": "Plump"
            },
            {
            "label_ref": "cherry_012", 
            "coordinates": BoundingBoxCoordinates(height=0.2, width=0.1, top_left_x=0.5, top_left_y=0.5), 
            "cherry_type": "Other cherry type", 
            "Specify cherry type": "Lambert"},
        ]
    },
    "cherries-vid-001.mp4": {
        103: [
            {
            "label_ref": "cherry_013", 
            "coordinates": BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.2, top_left_y=0.0), 
            "cherry_type": "Rainier", 
            "rainier_quality_options": "Plump"},
            {
            "label_ref": "cherry_014", 
            "coordinates": BoundingBoxCoordinates(height=0.2, width=0.2, top_left_x=0.1, top_left_y=0.1), 
            "cherry_type": "Bing", 
            "bing_quality_options": "Plump, Juicy, Large"
            },
            {
            "label_ref": "cherry_015", 
            "coordinates": BoundingBoxCoordinates(height=0.2, width=0.1, top_left_x=0.5, top_left_y=0.5), 
            "cherry_type": "Other cherry type", "Specify cherry type": "Sweetheart"
            },
        ],
        104: [
            {
            "label_ref": "cherry_016", 
            "coordinates": BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.2, top_left_y=0.2), 
            "cherry_type": "Rainier", 
            "rainier_quality_options": "Plump"},
            {
            "label_ref": "cherry_014", 
            "coordinates": BoundingBoxCoordinates(height=0.2, width=0.2, top_left_x=0.1, top_left_y=0.1), 
            "cherry_type": "Bing", 
            "bing_quality_options": "Plump, Juicy, Large"
            },
            {
            "label_ref": "cherry_017", 
            "coordinates": BoundingBoxCoordinates(height=0.2, width=0.1, top_left_x=0.5, top_left_y=0.5), 
            "cherry_type": "Other cherry type", "Specify cherry type": "Sweetheart"
            },
        ],
        105: [
            {
            "label_ref": "cherry_016", 
            "coordinates": BoundingBoxCoordinates(height=0.5, width=0.5, top_left_x=0.2, top_left_y=0.2), 
            "cherry_type": "Rainier", 
            "rainier_quality_options": "Plump"
            },
            {
            "label_ref": "cherry_014", 
            "coordinates": BoundingBoxCoordinates(height=0.2, width=0.2, top_left_x=0.1, top_left_y=0.1), 
            "cherry_type": "Bing", 
            "bing_quality_options": "Plump, Juicy, Large"
            },
            {
            "label_ref": "cherry_017", 
            "coordinates": BoundingBoxCoordinates(height=0.2, width=0.1, top_left_x=0.5, top_left_y=0.5), 
            "cherry_type": "Other cherry type", "Specify cherry type": "Sweetheart"
            },
        ],
    },
}


# Loop through each data unit (image, video, etc.)
for data_unit, frame_coordinates in video_frame_labels.items():
    object_instances_by_label_ref = {}

    # Get the label row for the current data unit
    label_row = project.list_label_rows_v2(data_title_eq=data_unit)[0]
    label_row.initialise_labels()

    # Loop through the frames for the current data unit
    for frame_number, items in frame_coordinates.items():
        if not isinstance(items, list):  #  Multiple objects in the frame
            items = [items]

        for item in items:
            label_ref = item["label_ref"]
            coord = item["coordinates"]
            cherry_type = item["cherry_type"]

            #  Check if label_ref already exists for reusability
            if label_ref not in object_instances_by_label_ref:
                box_object_instance: ObjectInstance = box_ontology_object.create_instance()
                object_instances_by_label_ref[label_ref] = box_object_instance  #  Store for reuse
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
                    box_object_instance.set_answer(attribute=other_cherry_option_text_attribute, answer=item.get("Specify cherry type", ""))

                # Set checklist attributes
                checklist_answers = []
                quality_options = item.get(f"{cherry_type.lower()}_quality_options", "").split(", ")

                for quality in quality_options:
                    if quality == "Plump":
                        checklist_answers.append(bing_plump_option if cherry_type == "Bing" else king_plump_option if cherry_type == "King" else rainier_plump_option)
                    elif quality == "Juicy":
                        checklist_answers.append(bing_juicy_option if cherry_type == "Bing" else king_juicy_option if cherry_type == "King" else rainier_juicy_option)
                    elif quality == "Large":
                        checklist_answers.append(bing_large_option if cherry_type == "Bing" else king_large_option if cherry_type == "King" else rainier_large_option)

                if checklist_attribute and checklist_answers:
                    box_object_instance.set_answer(attribute=checklist_attribute, answer=checklist_answers, overwrite=True)

            else:
                #  Reuse existing instance across frames
                box_object_instance = object_instances_by_label_ref[label_ref]

            #  Assign the object to the frame and track it
            box_object_instance.set_for_frames(coordinates=coord, frames=frame_number)

    #  Add object instances to label_row **only if they have frames assigned**
    for box_object_instance in object_instances_by_label_ref.values():
        if box_object_instance.get_annotation_frames():  #  Ensures it has at least one frame
            label_row.add_object_instance(box_object_instance)

    #  Upload all labels for this data unit (video/image) to the server
    label_row.save()

print(" Labels with cherry type radio buttons, checklist attributes, and text labels added for all data units.")
