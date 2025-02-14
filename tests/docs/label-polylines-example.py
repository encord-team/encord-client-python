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
from encord.objects.coordinates import PolylineCoordinates, PointCoordinate

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

# Create radio button attribute for branch type
ontology_structure = project.ontology_structure

# Find a bounding box annotation object in the project ontology
polyline_ontology_object: Object = ontology_structure.get_child_by_title(
    title="Branches", type_=Object
)

branch_type_radio_attribute = ontology_structure.get_child_by_title(
    type_=RadioAttribute, title="Type?"
)

# Create options for the radio buttons
fruiting_spur_option = branch_type_radio_attribute.get_child_by_title(type_=Option, title="Fruiting spur")
sucker_option = branch_type_radio_attribute.get_child_by_title(type_=Option, title="Sucker")
side_shoot_option = branch_type_radio_attribute.get_child_by_title(type_=Option, title="Side shoot")
other_branch_option = branch_type_radio_attribute.get_child_by_title(type_=Option, title="Other branch type")

# Create checklist attributes and options for each branch type
# Fruiting spur Qualities
fruiting_spur_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Fruiting spur Qualities?"
)
fruiting_spur_short_length = fruiting_spur_checklist_attribute.get_child_by_title(type_=Option, title="Short length")
fruiting_spur_high_bud_density = fruiting_spur_checklist_attribute.get_child_by_title(type_=Option, title="High bud density")
fruiting_spur_healthy_option = fruiting_spur_checklist_attribute.get_child_by_title(type_=Option, title="Healthy")

# Sucker Qualities
sucker_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Sucker Qualities?"
)
sucker_short_length = sucker_checklist_attribute.get_child_by_title(type_=Option, title="Short length")
sucker_high_bud_density = sucker_checklist_attribute.get_child_by_title(type_=Option, title="High bud density")
sucker_healthy_option = sucker_checklist_attribute.get_child_by_title(type_=Option, title="Healthy")

# Side shoot Qualities
side_shoot_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Side shoot Qualities?"
)
side_shoot_short_length = side_shoot_checklist_attribute.get_child_by_title(type_=Option, title="Short length")
side_shoot_high_bud_density = side_shoot_checklist_attribute.get_child_by_title(type_=Option, title="High bud density")
side_shoot_healthy_option = side_shoot_checklist_attribute.get_child_by_title(type_=Option, title="Healthy")

# Other branch Types
other_branch_option_text_attribute = ontology_structure.get_child_by_title(
    type_=TextAttribute, title="Specify branch type"
)


# Dictionary of labels per data unit and per frame with branch type specified, including quality options
video_image_frame_labels = {
    "blueberries-001.jpg": {
        0: {
            "label_ref": "blueberry_001",
            "coordinates": PolylineCoordinates([
                PointCoordinate(.013,.023), 
                PointCoordinate(.033,.033), 
                PointCoordinate(.053,.023), 
                PointCoordinate(.043,.013)]), 
            "branch_type": "Fruiting spur", 
            "fruiting_spur_quality_options": "Short length, High bud density"
            }
    },
    "blueberries-010.jpg": {
        0: [
            {
                "label_ref": "blueberry_002", 
                "coordinates": PolylineCoordinates([
                    PointCoordinate(.03,.023), 
                    PointCoordinate(.033,.033), 
                    PointCoordinate(.053,.033), 
                    PointCoordinate(.043,.013)]), 
                "branch_type": "Sucker", 
                "sucker_quality_options": "Short length, High bud density, Healthy"
                },
            {
                "label_ref": "blueberry_003",
                "coordinates": PolylineCoordinates([
                    PointCoordinate(.043,.053), 
                    PointCoordinate(.063,.063), 
                    PointCoordinate(.083,.053), 
                    PointCoordinate(.073,.043)]), 
                "branch_type": "Side shoot", 
                "side_shoot_quality_options": "Short length"
                },
            {
                "label_ref": "blueberry_004", 
                "coordinates": PolylineCoordinates([
                    PointCoordinate(.073,.023), 
                    PointCoordinate(.093,.033), 
                    PointCoordinate(.113,.023), 
                    PointCoordinate(.103,.013)]), 
                "branch_type": "Other branch type", "Specify branch type": "Cane"
                },
        ],
    },
    "blueberries-ig": {
        0: {
            "label_ref": "blueberry_005", 
            "coordinates": PolylineCoordinates([
                    PointCoordinate(.013,.023), 
                    PointCoordinate(.033,.033), 
                    PointCoordinate(.053,.023), 
                    PointCoordinate(.043,.013)]), 
            "branch_type": "Fruiting spur", 
            "fruiting_spur_quality_options": "Short length, High bud density"
            },
        2: [
            {
            "label_ref": "blueberry_006", 
            "coordinates": PolylineCoordinates([
                PointCoordinate(.013,.023), 
                PointCoordinate(.033,.033), 
                PointCoordinate(.053,.023), 
                PointCoordinate(.043,.013)]),
            "branch_type": "Sucker", 
            "sucker_quality_options": "Healthy"
            },
            {
            "label_ref": "blueberry_007", 
            "coordinates": PolylineCoordinates([
                PointCoordinate(.043,.053), 
                PointCoordinate(.063,.063), 
                PointCoordinate(.083,.053), 
                PointCoordinate(.073,.043)]), 
            "branch_type": "Side shoot", 
            "side_shoot_quality_options": "Short length"
            },
            {
            "label_ref": "blueberry_008", 
            "coordinates": PolylineCoordinates([
                PointCoordinate(.073,.023), 
                PointCoordinate(.093,.033), 
                PointCoordinate(.113,.023), 
                PointCoordinate(.103,.013)]),
            "branch_type": "Other branch type", "Specify branch type": "Cane"
            },
        ]
    },
    "blueberries-is": {
        0: {
            "label_ref": "blueberry_009", 
            "coordinates": PolylineCoordinates([
                PointCoordinate(.013,.023), 
                PointCoordinate(.033,.033), 
                PointCoordinate(.053,.023), 
                PointCoordinate(.043,.013)]),
            "branch_type": "Fruiting spur", 
            "fruiting_spur_quality_options": "Short length"
            },
        3: [
            {
            "label_ref": "blueberry_010", 
            "coordinates": PolylineCoordinates([
                PointCoordinate(.013,.023), 
                PointCoordinate(.033,.033), 
                PointCoordinate(.053,.023), 
                PointCoordinate(.043,.013)]), 
            "branch_type": "Sucker", 
            "sucker_quality_options": "Short length, High bud density, Healthy"
            },
            {
            "label_ref": "blueberry_011", 
            "coordinates": PolylineCoordinates([
                PointCoordinate(.043,.053), 
                PointCoordinate(.063,.063), 
                PointCoordinate(.083,.053), 
                PointCoordinate(.073,.043)]), 
            "branch_type": "Side shoot", 
            "side_shoot_quality_options": "Short length"
            },
            {
            "label_ref": "blueberry_012", 
            "coordinates": PolylineCoordinates([
                PointCoordinate(.073,.023), 
                PointCoordinate(.093,.033), 
                PointCoordinate(.113,.023), 
                PointCoordinate(.103,.013)]), 
            "branch_type": "Other branch type", 
            "Specify branch type": "Cane"},
        ]
    },
    "blueberries-vid-001.mp4": {
        103: [
            {
            "label_ref": "blueberry_013", 
            "coordinates": PolylineCoordinates([
                PointCoordinate(.013,.023), 
                PointCoordinate(.033,.033), 
                PointCoordinate(.053,.023), 
                PointCoordinate(.043,.013)]),
            "branch_type": "Side shoot", 
            "side_shoot_quality_options": "Short length"},
            {
            "label_ref": "blueberry_014", 
            "coordinates": PolylineCoordinates([
                PointCoordinate(.043,.053), 
                PointCoordinate(.063,.063), 
                PointCoordinate(.083,.053), 
                PointCoordinate(.073,.043)]),
            "branch_type": "Fruiting spur", 
            "fruiting_spur_quality_options": "Short length, High bud density, Healthy"
            },
            {
            "label_ref": "blueberry_015", 
            "coordinates": PolylineCoordinates([
                PointCoordinate(.073,.023), 
                PointCoordinate(.093,.033), 
                PointCoordinate(.113,.023), 
                PointCoordinate(.103,.013)]),
            "branch_type": "Other branch type", "Specify branch type": "Cane"
            },
        ],
        104: [
            {
            "label_ref": "blueberry_016", 
            "coordinates": PolylineCoordinates([
                PointCoordinate(.013,.023), 
                PointCoordinate(.033,.033), 
                PointCoordinate(.053,.023), 
                PointCoordinate(.043,.013)]), 
            "branch_type": "Side shoot", 
            "side_shoot_quality_options": "Short length"},
            {
            "label_ref": "blueberry_014", 
            "coordinates": PolylineCoordinates([
                PointCoordinate(.0413,.0523), 
                PointCoordinate(.0613,.0623), 
                PointCoordinate(.0813,.0523), 
                PointCoordinate(.0713,.0423)]),
            "branch_type": "Fruiting spur", 
            "fruiting_spur_quality_options": "Short length, High bud density, Healthy"
            },
            {
            "label_ref": "blueberry_017", 
            "coordinates": PolylineCoordinates([
                PointCoordinate(.073,.023), 
                PointCoordinate(.093,.033), 
                PointCoordinate(.113,.023), 
                PointCoordinate(.103,.013)]),
            "branch_type": "Other branch type", "Specify branch type": "Cane"
            },
        ],
        105: [
            {
            "label_ref": "blueberry_016", 
            "coordinates": PolylineCoordinates([
                PointCoordinate(.0113,.0223), 
                PointCoordinate(.0313,.0323), 
                PointCoordinate(.0513,.0223), 
                PointCoordinate(.0413,.0123)]), 
            "branch_type": "Side shoot", 
            "side_shoot_quality_options": "Short length"
            },
            {
            "label_ref": "blueberry_014", 
            "coordinates": PolylineCoordinates([
                PointCoordinate(.0433,.0553), 
                PointCoordinate(.0633,.0653), 
                PointCoordinate(.0833,.0553), 
                PointCoordinate(.0733,.0453)]),
            "branch_type": "Fruiting spur", 
            "fruiting_spur_quality_options": "Short length, High bud density, Healthy"
            },
            {
            "label_ref": "blueberry_017", 
            "coordinates": PolylineCoordinates([
                PointCoordinate(.0713,.0223), 
                PointCoordinate(.0913,.0323), 
                PointCoordinate(.1113,.0223), 
                PointCoordinate(.1013,.0123)]),
            "branch_type": "Other branch type", "Specify branch type": "Cane"
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
            branch_type = item["branch_type"]

            #  Check if label_ref already exists for reusability
            if label_ref not in object_instances_by_label_ref:
                polyline_object_instance: ObjectInstance = polyline_ontology_object.create_instance()
                object_instances_by_label_ref[label_ref] = polyline_object_instance  #  Store for reuse
                checklist_attribute = None

                # Set branch type attribute
                if branch_type == "Fruiting spur":
                    polyline_object_instance.set_answer(attribute=branch_type_radio_attribute, answer=fruiting_spur_option)
                    checklist_attribute = fruiting_spur_checklist_attribute
                elif branch_type == "Sucker":
                    polyline_object_instance.set_answer(attribute=branch_type_radio_attribute, answer=sucker_option)
                    checklist_attribute = sucker_checklist_attribute
                elif branch_type == "Side shoot":
                    polyline_object_instance.set_answer(attribute=branch_type_radio_attribute, answer=side_shoot_option)
                    checklist_attribute = side_shoot_checklist_attribute
                elif branch_type == "Other branch type":
                    polyline_object_instance.set_answer(attribute=branch_type_radio_attribute, answer=other_branch_option)
                    polyline_object_instance.set_answer(attribute=other_branch_option_text_attribute, answer=item.get("Specify branch type", ""))

                # Set checklist attributes
                checklist_answers = []
                quality_options = item.get(f"{branch_type.lower()}_quality_options", "").split(", ")

                for quality in quality_options:
                    if quality == "Short length":
                        checklist_answers.append(fruiting_spur_short_length if branch_type == "Fruiting spur" else sucker_short_length if branch_type == "Sucker" else side_shoot_short_length)
                    elif quality == "High bud density":
                        checklist_answers.append(fruiting_spur_high_bud_density if branch_type == "Fruiting spur" else sucker_high_bud_density if branch_type == "Sucker" else side_shoot_high_bud_density)
                    elif quality == "Healthy":
                        checklist_answers.append(fruiting_spur_healthy_option if branch_type == "Fruiting spur" else sucker_healthy_option if branch_type == "Sucker" else side_shoot_healthy_option)

                if checklist_attribute and checklist_answers:
                    polyline_object_instance.set_answer(attribute=checklist_attribute, answer=checklist_answers, overwrite=True)

            else:
                #  Reuse existing instance across frames
                polyline_object_instance = object_instances_by_label_ref[label_ref]

            #  Assign the object to the frame and track it
            polyline_object_instance.set_for_frames(coordinates=coord, frames=frame_number)

    #  Add object instances to label_row **only if they have frames assigned**
    for polyline_object_instance in object_instances_by_label_ref.values():
        if polyline_object_instance.get_annotation_frames():  #  Ensures it has at least one frame
            label_row.add_object_instance(polyline_object_instance)

    #  Upload all labels for this data unit (video/image) to the server
    label_row.save()

print(" Labels with branch type radio buttons, checklist attributes, and text labels added for all data units.")
