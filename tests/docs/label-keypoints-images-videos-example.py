# Import dependencies
from pathlib import Path

from encord import EncordUserClient, Project
from encord.objects import ChecklistAttribute, Object, ObjectInstance, Option, RadioAttribute, TextAttribute
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
keypoint_ontology_object: Object = ontology_structure.get_child_by_title(title="Floral axis", type_=Object)

floral_axis_type_radio_attribute = ontology_structure.get_child_by_title(type_=RadioAttribute, title="Type?")

# Create options for the radio buttons
pedicel_option = floral_axis_type_radio_attribute.get_child_by_title(type_=Option, title="Pedicel")
peduncle_option = floral_axis_type_radio_attribute.get_child_by_title(type_=Option, title="Peduncle")
other_floral_axis_option = floral_axis_type_radio_attribute.get_child_by_title(
    type_=Option, title="Other floral axis type"
)

# Create checklist attributes and options for each floral axis type

# Pedicel Qualities
pedicel_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Pedicel Qualities?"
)
pedicel_robust_option = pedicel_checklist_attribute.get_child_by_title(type_=Option, title="Robust")
pedicel_healthy_option = pedicel_checklist_attribute.get_child_by_title(type_=Option, title="Healthy")
pedicel_growth_alignment_option = pedicel_checklist_attribute.get_child_by_title(
    type_=Option, title="Good Growth and Alignment"
)

# Peduncle Qualities
peduncle_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Peduncle Qualities?"
)
peduncle_robust_option = peduncle_checklist_attribute.get_child_by_title(type_=Option, title="Robust")
peduncle_healthy_option = peduncle_checklist_attribute.get_child_by_title(type_=Option, title="Healthy")
peduncle_growth_alignment_option = peduncle_checklist_attribute.get_child_by_title(
    type_=Option, title="Good Growth and Alignment"
)

# Other floral axis Types
other_floral_axis_option_text_attribute = ontology_structure.get_child_by_title(
    type_=TextAttribute, title="Specify floral axis type"
)

# Dictionary of labels per data unit and per frame with floral axis type specified, including quality options
video_image_frame_labels = {
    "blueberries-001.jpg": {
        0: {
            "label_ref": "floral_axis_001",
            "coordinates": PointCoordinate(x=0.01, y=0.02),
            "floral_axis_type": "Pedicel",
            "pedicel_quality_options": "Robust, Healthy",
        }
    },
    "persimmons-010.jpg": {
        0: [
            {
                "label_ref": "floral_axis_002",
                "coordinates": PointCoordinate(x=0.03, y=0.03),
                "floral_axis_type": "Peduncle",
                "peduncle_quality_options": "Robust, Healthy, Good Growth and Alignment",
            },
            {
                "label_ref": "floral_axis_003",
                "coordinates": PointCoordinate(x=0.05, y=0.04),
                "floral_axis_type": "Peduncle",
                "peduncle_quality_options": "Robust",
            },
            {
                "label_ref": "floral_axis_004",
                "coordinates": PointCoordinate(x=0.09, y=0.03),
                "floral_axis_type": "Other floral axis type",
                "Specify floral axis type": "Calyx",
            },
        ],
    },
    "blueberries-ig": {
        0: {
            "label_ref": "floral_axis_005",
            "coordinates": PointCoordinate(x=0.05, y=0.02),
            "floral_axis_type": "Pedicel",
            "pedicel_quality_options": "Robust, Healthy",
        },
        2: [
            {
                "label_ref": "floral_axis_006",
                "coordinates": PointCoordinate(x=0.03, y=0.03),
                "floral_axis_type": "Pedicel",
                "pedicel_quality_options": "Good Growth and Alignment",
            },
            {
                "label_ref": "floral_axis_007",
                "coordinates": PointCoordinate(x=0.04, y=0.05),
                "floral_axis_type": "Pedicel",
                "pedicel_quality_options": "Robust",
            },
            {
                "label_ref": "floral_axis_008",
                "coordinates": PointCoordinate(x=0.11, y=0.02),
                "floral_axis_type": "Other floral axis type",
                "Specify floral axis type": "Calyx",
            },
        ],
    },
    "persimmons-is": {
        0: {
            "label_ref": "floral_axis_009",
            "coordinates": PointCoordinate(x=0.01, y=0.02),
            "floral_axis_type": "Peduncle",
            "peduncle_quality_options": "Robust",
        },
        3: [
            {
                "label_ref": "floral_axis_010",
                "coordinates": PointCoordinate(x=0.03, y=0.03),
                "floral_axis_type": "Peduncle",
                "peduncle_quality_options": "Robust, Healthy, Good Growth and Alignment",
            },
            {
                "label_ref": "floral_axis_011",
                "coordinates": PointCoordinate(x=0.08, y=0.05),
                "floral_axis_type": "Peduncle",
                "peduncle_quality_options": "Robust",
            },
            {
                "label_ref": "floral_axis_012",
                "coordinates": PointCoordinate(x=0.11, y=0.02),
                "floral_axis_type": "Other floral axis type",
                "Specify floral axis type": "Calyx",
            },
        ],
    },
    "blueberries-vid-001.mp4": {
        103: [
            {
                "label_ref": "floral_axis_013",
                "coordinates": PointCoordinate(x=0.02, y=0.01),
                "floral_axis_type": "Pedicel",
                "pedicel_quality_options": "Robust",
            },
            {
                "label_ref": "floral_axis_014",
                "coordinates": PointCoordinate(x=0.06, y=0.06),
                "floral_axis_type": "Pedicel",
                "pedicel_quality_options": "Robust, Healthy, Good Growth and Alignment",
            },
            {
                "label_ref": "floral_axis_015",
                "coordinates": PointCoordinate(x=0.10, y=0.01),
                "floral_axis_type": "Other floral axis type",
                "Specify floral axis type": "Calyx",
            },
        ],
        104: [
            {
                "label_ref": "floral_axis_016",
                "coordinates": PointCoordinate(x=0.04, y=0.01),
                "floral_axis_type": "Pedicel",
                "pedicel_quality_options": "Robust",
            },
            {
                "label_ref": "floral_axis_014",
                "coordinates": PointCoordinate(x=0.08, y=0.05),
                "floral_axis_type": "Pedicel",
                "pedicel_quality_options": "Robust, Healthy, Good Growth and Alignment",
            },
            {
                "label_ref": "floral_axis_017",
                "coordinates": PointCoordinate(x=0.11, y=0.02),
                "floral_axis_type": "Other floral axis type",
                "Specify floral axis type": "Calyx",
            },
        ],
        105: [
            {
                "label_ref": "floral_axis_016",
                "coordinates": PointCoordinate(x=0.05, y=0.02),
                "floral_axis_type": "Pedicel",
                "pedicel_quality_options": "Robust",
            },
            {
                "label_ref": "floral_axis_014",
                "coordinates": PointCoordinate(x=0.07, y=0.04),
                "floral_axis_type": "Pedicel",
                "pedicel_quality_options": "Robust, Healthy, Good Growth and Alignment",
            },
            {
                "label_ref": "floral_axis_017",
                "coordinates": PointCoordinate(x=0.09, y=0.03),
                "floral_axis_type": "Other floral axis type",
                "Specify floral axis type": "Calyx",
            },
        ],
    },
}


# Bundle size
BUNDLE_SIZE = 100

# Cache initialized label rows
label_row_map = {}

# Step 1: Initialize all label rows using a bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for data_unit in video_image_frame_labels.keys():
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

for data_unit, frame_coordinates in video_image_frame_labels.items():
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
            floral_axis_type = item["floral_axis_type"]

            assert floral_axis_type in {"Pedicel", "Peduncle", "Other floral axis type"}, \
                f"Unexpected floral axis type '{floral_axis_type}' in data unit '{data_unit}'"

            # Check if label_ref already exists for reusability
            if label_ref not in object_instances_by_label_ref:
                keypoint_object_instance: ObjectInstance = keypoint_ontology_object.create_instance()
                assert keypoint_object_instance is not None, "Failed to create ObjectInstance"

                object_instances_by_label_ref[label_ref] = keypoint_object_instance
                checklist_attribute = None

                # Set floral axis type attribute
                if floral_axis_type == "Pedicel":
                    assert pedicel_option is not None, "Missing 'pedicel_option'"
                    keypoint_object_instance.set_answer(
                        attribute=floral_axis_type_radio_attribute, answer=pedicel_option
                    )
                    checklist_attribute = pedicel_checklist_attribute
                elif floral_axis_type == "Peduncle":
                    assert peduncle_option is not None, "Missing 'peduncle_option'"
                    keypoint_object_instance.set_answer(
                        attribute=floral_axis_type_radio_attribute, answer=peduncle_option
                    )
                    checklist_attribute = peduncle_checklist_attribute
                elif floral_axis_type == "Other floral axis type":
                    assert other_floral_axis_option is not None, "Missing 'other_floral_axis_option'"
                    keypoint_object_instance.set_answer(
                        attribute=floral_axis_type_radio_attribute, answer=other_floral_axis_option
                    )
                    text_answer = item.get("Specify floral axis type", "")
                    assert isinstance(text_answer, str), "'Specify floral axis type' must be a string"
                    keypoint_object_instance.set_answer(
                        attribute=other_floral_axis_option_text_attribute,
                        answer=text_answer,
                    )

                # Set checklist attributes
                checklist_answers = []
                quality_key = f"{floral_axis_type.lower()}_quality_options"
                quality_options = item.get(quality_key, "").split(", ")

                for quality in quality_options:
                    if quality == "Robust":
                        checklist_answers.append(
                            pedicel_robust_option if floral_axis_type == "Pedicel" else peduncle_robust_option
                        )
                    elif quality == "Healthy":
                        checklist_answers.append(
                            pedicel_healthy_option if floral_axis_type == "Pedicel" else peduncle_healthy_option
                        )
                    elif quality == "Good Growth and Alignment":
                        checklist_answers.append(
                            pedicel_growth_alignment_option
                            if floral_axis_type == "Pedicel"
                            else peduncle_growth_alignment_option
                        )

                if checklist_attribute and checklist_answers:
                    keypoint_object_instance.set_answer(
                        attribute=checklist_attribute, answer=checklist_answers, overwrite=True
                    )
            else:
                # Reuse existing instance across frames
                keypoint_object_instance = object_instances_by_label_ref[label_ref]

            # Assign the object to the frame and track it
            keypoint_object_instance.set_for_frames(coordinates=coord, frames=frame_number)

    # Add object instances to label_row **only if they have frames assigned**
    for keypoint_object_instance in object_instances_by_label_ref.values():
        assert isinstance(keypoint_object_instance, ObjectInstance), "Expected ObjectInstance type"
        if keypoint_object_instance.get_annotation_frames():
            label_row.add_object_instance(keypoint_object_instance)

    label_rows_to_save.append(label_row)

# Step 3: Save all label rows using a bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for label_row in label_rows_to_save:
        assert label_row is not None, "Trying to save a None label row"
        label_row.save(bundle=bundle)
        print(f"Saved label row for {label_row.data_title}")

print("Labels with floral axis type radio buttons, checklist attributes, and text labels added for all data units.")
