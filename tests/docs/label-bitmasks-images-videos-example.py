# Import dependencies
import numpy as np

from encord import EncordUserClient, Project
from encord.objects import ChecklistAttribute, Object, ObjectInstance, Option, RadioAttribute, TextAttribute
from encord.objects.coordinates import BitmaskCoordinates

# First, we need to prepare the mask itself.
# For simplicity, we'll mask the entire frame
# Note, that the size of the mask must be identical to the size of the image/frame
numpy_coordinates = np.ones((1080, 1920))

# we also need to make sure that the image/frame is in boolean format
numpy_coordinates = numpy_coordinates.astype(bool)

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

# Create radio button attribute for apple type
ontology_structure = project.ontology_structure

# Find a bitmask annotation object in the project ontology
bitmask_ontology_object: Object = ontology_structure.get_child_by_title(title="Apples", type_=Object)

apple_type_radio_attribute = ontology_structure.get_child_by_title(type_=RadioAttribute, title="Type?")

# Create options for the radio buttons
sugar_bee_option = apple_type_radio_attribute.get_child_by_title(type_=Option, title="Sugar Bee")
granny_smith_option = apple_type_radio_attribute.get_child_by_title(type_=Option, title="Granny Smith")
honey_crisp_option = apple_type_radio_attribute.get_child_by_title(type_=Option, title="Honey Crisp")
other_apple_option = apple_type_radio_attribute.get_child_by_title(type_=Option, title="Other apple type")

# Create checklist attributes and options for each apple type
# Sugar Bee Qualities
sugar_bee_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Sugar Bee Qualities?"
)
sugar_bee_plump_option = sugar_bee_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
sugar_bee_juicy_option = sugar_bee_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
sugar_bee_large_option = sugar_bee_checklist_attribute.get_child_by_title(type_=Option, title="Large")

# Granny Smith Qualities
granny_smith_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Granny Smith Qualities?"
)
granny_smith_plump_option = granny_smith_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
granny_smith_juicy_option = granny_smith_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
granny_smith_large_option = granny_smith_checklist_attribute.get_child_by_title(type_=Option, title="Large")

# Honey Crisp Qualities
honey_crisp_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Honey Crisp Qualities?"
)
honey_crisp_plump_option = honey_crisp_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
honey_crisp_juicy_option = honey_crisp_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
honey_crisp_large_option = honey_crisp_checklist_attribute.get_child_by_title(type_=Option, title="Large")

# Other apple Types
other_apple_option_text_attribute = ontology_structure.get_child_by_title(
    type_=TextAttribute, title="Specify apple type"
)


# Dictionary of labels per data unit and per frame with apple type specified, including quality options
video_frame_labels = {
    "apples-001.jpg": {
        0: {
            "label_ref": "apple_001",
            "coordinates": BitmaskCoordinates(numpy_coordinates),
            "apple_type": "Sugar Bee",
            "sugar_bee_quality_options": "Plump, Juicy",
        }
    },
    "apples-010.jpg": {
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
    "apples-ig": {
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
    "apples-is": {
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
    "apples-vid-001.mp4": {
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
            apple_type = item["apple_type"]

            #  Check if label_ref already exists for reusability
            if label_ref not in object_instances_by_label_ref:
                bitmask_object_instance: ObjectInstance = bitmask_ontology_object.create_instance()
                object_instances_by_label_ref[label_ref] = bitmask_object_instance  #  Store for reuse
                checklist_attribute = None

                # Set apple type attribute
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
                    bitmask_object_instance.set_answer(
                        attribute=other_apple_option_text_attribute, answer=item.get("Specify apple type", "")
                    )

                # Set checklist attributes
                checklist_answers = []
                quality_options = item.get(f"{apple_type.lower()}_quality_options", "").split(", ")

                for quality in quality_options:
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
                #  Reuse existing instance across frames
                bitmask_object_instance = object_instances_by_label_ref[label_ref]

            #  Assign the object to the frame and track it
            bitmask_object_instance.set_for_frames(coordinates=coord, frames=frame_number)

    #  Add object instances to label_row **only if they have frames assigned**
    for bitmask_object_instance in object_instances_by_label_ref.values():
        if bitmask_object_instance.get_annotation_frames():  #  Ensures it has at least one frame
            label_row.add_object_instance(bitmask_object_instance)

    #  Upload all labels for this data unit (video/image) to the server
    label_row.save()

print(" Labels with apple type radio buttons, checklist attributes, and text labels added for all data units.")
