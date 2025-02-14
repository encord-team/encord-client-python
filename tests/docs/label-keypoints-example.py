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
from encord.objects.coordinates import PointCoordinate

SSH_PATH = "/Users/laverne-encord/prod-sdk-ssh-key-private-key.txt"
PROJECT_HASH = "8d73bec0-ac61-4d28-b45a-7bffdf4c6b8e"

# Create user client using ssh key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Get project for which labels are to be added
project: Project = user_client.get_project(PROJECT_HASH)

# Create radio button attribute for floral axis type
ontology_structure = project.ontology_structure

# Find a bounding box annotation object in the project ontology
keypoint_ontology_object: Object = ontology_structure.get_child_by_title(
    title="Floral axis", type_=Object
)

floral_axis_type_radio_attribute = ontology_structure.get_child_by_title(
    type_=RadioAttribute, title="Type?"
)

# Create options for the radio buttons
pedicel_option = floral_axis_type_radio_attribute.get_child_by_title(type_=Option, title="Pedicel")
peduncle_option = floral_axis_type_radio_attribute.get_child_by_title(type_=Option, title="Peduncle")
other_floral_axis_option = floral_axis_type_radio_attribute.get_child_by_title(type_=Option, title="Other floral axis type")

# Create checklist attributes and options for each floral axis type

# Pedicel Qualities
pedicel_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Pedicel Qualities?"
)
pedicel_robust_option = pedicel_checklist_attribute.get_child_by_title(type_=Option, title="Robust")
pedicel_healthy_option = pedicel_checklist_attribute.get_child_by_title(type_=Option, title="Healthy")
pedicel_growth_alignment_option = pedicel_checklist_attribute.get_child_by_title(type_=Option, title="Good Growth and Alignment")

# Peduncle Qualities
peduncle_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Peduncle Qualities?"
)
peduncle_robust_option = peduncle_checklist_attribute.get_child_by_title(type_=Option, title="Robust")
peduncle_healthy_option = peduncle_checklist_attribute.get_child_by_title(type_=Option, title="Healthy")
peduncle_growth_alignment_option = peduncle_checklist_attribute.get_child_by_title(type_=Option, title="Good Growth and Alignment")

# Other floral axis Types
other_floral_axis_option_text_attribute = ontology_structure.get_child_by_title(
    type_=TextAttribute, title="Specify floral axis type"
)

# Dictionary of labels per data unit and per frame with floral axis type specified, including quality options
video_image_frame_labels = {
    "blueberries-001.jpg": {
        0: {
            "label_ref": "floral_axis_001",
            "coordinates": PointCoordinate(.01,.02), 
            "floral_axis_type": "Pedicel", 
            "pedicel_quality_options": "Robust, Healthy"
            }
    },
    "persimmons-010.jpg": {
        0: [
            {
                "label_ref": "floral_axis_002", 
                "coordinates": PointCoordinate(.03,.03),
                "floral_axis_type": "Peduncle", 
                "peduncle_quality_options": "Robust, Healthy, Good Growth and Alignment"
                },
            {
                "label_ref": "floral_axis_003",
                "coordinates": PointCoordinate(.05,.04), 
                "floral_axis_type": "Peduncle", 
                "peduncle_quality_options": "Robust"
                },
            {
                "label_ref": "floral_axis_004", 
                "coordinates": PointCoordinate(.09,.03), 
                "floral_axis_type": "Other floral axis type", "Specify floral axis type": "Calyx"
                },
        ],
    },
    "blueberries-ig": {
        0: {
            "label_ref": "floral_axis_005", 
            "coordinates": PointCoordinate(.05,.02), 
            "floral_axis_type": "Pedicel", 
            "pedicel_quality_options": "Robust, Healthy"
            },
        2: [
            {
            "label_ref": "floral_axis_006", 
            "coordinates": PointCoordinate(.03,.03), 
            "floral_axis_type": "Pedicel", 
            "pedicel_quality_options": "Good Growth and Alignment"
            },
            {
            "label_ref": "floral_axis_007", 
            "coordinates": PointCoordinate(.04,.05), 
            "floral_axis_type": "Pedicel", 
            "pedicel_quality_options": "Robust"
            },
            {
            "label_ref": "floral_axis_008", 
            "coordinates": PointCoordinate(.11,.02), 
            "floral_axis_type": "Other floral axis type", 
            "Specify floral axis type": "Calyx"},
        ]
    },
    "persimmons-is": {
        0: {
            "label_ref": "floral_axis_009", 
            "coordinates": PointCoordinate(.01,.02), 
            "floral_axis_type": "Peduncle", 
            "peduncle_quality_options": "Robust"
            },
        3: [
            {
            "label_ref": "floral_axis_010", 
            "coordinates": PointCoordinate(.03,.03), 
            "floral_axis_type": "Peduncle", 
            "peduncle_quality_options": "Robust, Healthy, Good Growth and Alignment"
            },
            {
            "label_ref": "floral_axis_011", 
            "coordinates": PointCoordinate(.08,.05), 
            "floral_axis_type": "Peduncle", 
            "peduncle_quality_options": "Robust"
            },
            {
            "label_ref": "floral_axis_012", 
            "coordinates": PointCoordinate(.11,.02), 
            "floral_axis_type": "Other floral axis type", 
            "Specify floral axis type": "Calyx"},
        ]
    },
    "blueberries-vid-001.mp4": {
        103: [
            {
            "label_ref": "floral_axis_013", 
            "coordinates": PointCoordinate(.02,.01),
            "floral_axis_type": "Pedicel", 
            "pedicel_quality_options": "Robust"},
            {
            "label_ref": "floral_axis_014", 
            "coordinates": PointCoordinate(.06,.06), 
            "floral_axis_type": "Pedicel", 
            "pedicel_quality_options": "Robust, Healthy, Good Growth and Alignment"
            },
            {
            "label_ref": "floral_axis_015", 
            "coordinates": PointCoordinate(.10,.01), 
            "floral_axis_type": "Other floral axis type", "Specify floral axis type": "Calyx"
            },
        ],
        104: [
            {
            "label_ref": "floral_axis_016", 
            "coordinates": PointCoordinate(.04,.01), 
            "floral_axis_type": "Pedicel", 
            "pedicel_quality_options": "Robust"},
            {
            "label_ref": "floral_axis_014", 
            "coordinates": PointCoordinate(.08,.05), 
            "floral_axis_type": "Pedicel", 
            "pedicel_quality_options": "Robust, Healthy, Good Growth and Alignment"
            },
            {
            "label_ref": "floral_axis_017", 
            "coordinates": PointCoordinate(.11,.02), 
            "floral_axis_type": "Other floral axis type", "Specify floral axis type": "Calyx"
            },
        ],
        105: [
            {
            "label_ref": "floral_axis_016", 
            "coordinates": PointCoordinate(.05,.02), 
            "floral_axis_type": "Pedicel", 
            "pedicel_quality_options": "Robust"
            },
            {
            "label_ref": "floral_axis_014", 
            "coordinates": PointCoordinate(.07,.04), 
            "floral_axis_type": "Pedicel", 
            "pedicel_quality_options": "Robust, Healthy, Good Growth and Alignment"
            },
            {
            "label_ref": "floral_axis_017", 
            "coordinates": PointCoordinate(.09,.03), 
            "floral_axis_type": "Other floral axis type", "Specify floral axis type": "Calyx"
            },
        ],
    },
}


# Loop through each data unit (image, video, etc.)
for data_unit, frame_coordinates in video_image_frame_labels.items():
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
            floral_axis_type = item["floral_axis_type"]

            #  Check if label_ref already exists for reusability
            if label_ref not in object_instances_by_label_ref:
                keypoint_object_instance: ObjectInstance = keypoint_ontology_object.create_instance()
                object_instances_by_label_ref[label_ref] = keypoint_object_instance  #  Store for reuse
                checklist_attribute = None

                # Set floral axis type attribute
                if floral_axis_type == "Pedicel":
                    keypoint_object_instance.set_answer(attribute=floral_axis_type_radio_attribute, answer=pedicel_option)
                    checklist_attribute = pedicel_checklist_attribute
                elif floral_axis_type == "Peduncle":
                    keypoint_object_instance.set_answer(attribute=floral_axis_type_radio_attribute, answer=peduncle_option)
                    checklist_attribute = peduncle_checklist_attribute
                elif floral_axis_type == "Other floral axis type":
                    keypoint_object_instance.set_answer(attribute=floral_axis_type_radio_attribute, answer=other_floral_axis_option)
                    keypoint_object_instance.set_answer(attribute=other_floral_axis_option_text_attribute, answer=item.get("Specify floral axis type", ""))

                # Set checklist attributes
                checklist_answers = []
                quality_options = item.get(f"{floral_axis_type.lower()}_quality_options", "").split(", ")

                for quality in quality_options:
                    if quality == "Robust":
                        checklist_answers.append(pedicel_robust_option if floral_axis_type == "Pedicel" else peduncle_robust_option)
                    elif quality == "Healthy":
                        checklist_answers.append(pedicel_healthy_option if floral_axis_type == "Pedicel" else peduncle_healthy_option)
                    elif quality == "Good Growth and Alignment":
                        checklist_answers.append(pedicel_growth_alignment_option if floral_axis_type == "Pedicel" else peduncle_growth_alignment_option)

                if checklist_attribute and checklist_answers:
                    keypoint_object_instance.set_answer(attribute=checklist_attribute, answer=checklist_answers, overwrite=True)

            else:
                #  Reuse existing instance across frames
                keypoint_object_instance = object_instances_by_label_ref[label_ref]

            #  Assign the object to the frame and track it
            keypoint_object_instance.set_for_frames(coordinates=coord, frames=frame_number)

    #  Add object instances to label_row **only if they have frames assigned**
    for keypoint_object_instance in object_instances_by_label_ref.values():
        if keypoint_object_instance.get_annotation_frames():  #  Ensures it has at least one frame
            label_row.add_object_instance(keypoint_object_instance)

    #  Upload all labels for this data unit (video/image) to the server
    label_row.save()

print(" Labels with floral axis type radio buttons, checklist attributes, and text labels added for all data units.")
