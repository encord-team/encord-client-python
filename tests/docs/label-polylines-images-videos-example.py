# Import dependencies
from pathlib import Path

from encord import EncordUserClient, Project
from encord.objects import ChecklistAttribute, Object, ObjectInstance, Option, RadioAttribute, TextAttribute
from encord.objects.coordinates import PointCoordinate, PolylineCoordinates

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
polyline_ontology_object: Object = ontology_structure.get_child_by_title(title="Branches", type_=Object)

branch_type_radio_attribute = ontology_structure.get_child_by_title(type_=RadioAttribute, title="Type?")

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
fruiting_spur_short_length_option = fruiting_spur_checklist_attribute.get_child_by_title(
    type_=Option, title="Short length"
)
fruiting_spur_high_bud_density_option = fruiting_spur_checklist_attribute.get_child_by_title(
    type_=Option, title="High bud density"
)
fruiting_spur_healthy_option = fruiting_spur_checklist_attribute.get_child_by_title(type_=Option, title="Healthy")

# Sucker Qualities
sucker_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="Sucker Qualities?")
sucker_short_length_option = sucker_checklist_attribute.get_child_by_title(type_=Option, title="Short length")
sucker_high_bud_density_option = sucker_checklist_attribute.get_child_by_title(type_=Option, title="High bud density")
sucker_healthy_option = sucker_checklist_attribute.get_child_by_title(type_=Option, title="Healthy")

# Side shoot Qualities
side_shoot_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Side shoot Qualities?"
)
side_shoot_short_length_option = side_shoot_checklist_attribute.get_child_by_title(type_=Option, title="Short length")
side_shoot_high_bud_density_option = side_shoot_checklist_attribute.get_child_by_title(
    type_=Option, title="High bud density"
)
side_shoot_healthy_option = side_shoot_checklist_attribute.get_child_by_title(type_=Option, title="Healthy")

# Other branch Types
other_branch_option_text_attribute = ontology_structure.get_child_by_title(
    type_=TextAttribute, title="Specify branch type"
)


# Dictionary of labels per data unit and per frame with branch type specified, including quality options
video_image_frame_labels = {
    "cherries-001.jpg": {
        0: {
            "label_ref": "branch_001",
            "coordinates": PolylineCoordinates(
                [
                    PointCoordinate(0.013, 0.023),
                    PointCoordinate(0.033, 0.033),
                    PointCoordinate(0.053, 0.023),
                    PointCoordinate(0.043, 0.013),
                ]
            ),
            "branch_type": "Fruiting spur",
            "fruiting_spur_quality_options": "Short length, High bud density",
        }
    },
    "cherries-010.jpg": {
        0: [
            {
                "label_ref": "branch_002",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate(0.03, 0.023),
                        PointCoordinate(0.033, 0.033),
                        PointCoordinate(0.053, 0.033),
                        PointCoordinate(0.043, 0.013),
                    ]
                ),
                "branch_type": "Sucker",
                "sucker_quality_options": "Short length, High bud density, Healthy",
            },
            {
                "label_ref": "branch_003",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate(0.043, 0.053),
                        PointCoordinate(0.063, 0.063),
                        PointCoordinate(0.083, 0.053),
                        PointCoordinate(0.073, 0.043),
                    ]
                ),
                "branch_type": "Side shoot",
                "side_shoot_quality_options": "Short length",
            },
            {
                "label_ref": "branch_004",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate(0.073, 0.023),
                        PointCoordinate(0.093, 0.033),
                        PointCoordinate(0.113, 0.023),
                        PointCoordinate(0.103, 0.013),
                    ]
                ),
                "branch_type": "Other branch type",
                "Specify branch type": "Cane",
            },
        ],
    },
    "cherries-ig": {
        0: {
            "label_ref": "branch_005",
            "coordinates": PolylineCoordinates(
                [
                    PointCoordinate(0.013, 0.023),
                    PointCoordinate(0.033, 0.033),
                    PointCoordinate(0.053, 0.023),
                    PointCoordinate(0.043, 0.013),
                ]
            ),
            "branch_type": "Fruiting spur",
            "fruiting_spur_quality_options": "Short length, High bud density",
        },
        2: [
            {
                "label_ref": "branch_006",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate(0.013, 0.023),
                        PointCoordinate(0.033, 0.033),
                        PointCoordinate(0.053, 0.023),
                        PointCoordinate(0.043, 0.013),
                    ]
                ),
                "branch_type": "Sucker",
                "sucker_quality_options": "Healthy",
            },
            {
                "label_ref": "branch_007",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate(0.043, 0.053),
                        PointCoordinate(0.063, 0.063),
                        PointCoordinate(0.083, 0.053),
                        PointCoordinate(0.073, 0.043),
                    ]
                ),
                "branch_type": "Side shoot",
                "side_shoot_quality_options": "Short length",
            },
            {
                "label_ref": "branch_008",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate(0.073, 0.023),
                        PointCoordinate(0.093, 0.033),
                        PointCoordinate(0.113, 0.023),
                        PointCoordinate(0.103, 0.013),
                    ]
                ),
                "branch_type": "Other branch type",
                "Specify branch type": "Cane",
            },
        ],
    },
    "cherries-is": {
        0: {
            "label_ref": "branch_009",
            "coordinates": PolylineCoordinates(
                [
                    PointCoordinate(0.013, 0.023),
                    PointCoordinate(0.033, 0.033),
                    PointCoordinate(0.053, 0.023),
                    PointCoordinate(0.043, 0.013),
                ]
            ),
            "branch_type": "Fruiting spur",
            "fruiting_spur_quality_options": "Short length",
        },
        3: [
            {
                "label_ref": "branch_010",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate(0.013, 0.023),
                        PointCoordinate(0.033, 0.033),
                        PointCoordinate(0.053, 0.023),
                        PointCoordinate(0.043, 0.013),
                    ]
                ),
                "branch_type": "Sucker",
                "sucker_quality_options": "Short length, High bud density, Healthy",
            },
            {
                "label_ref": "branch_011",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate(0.043, 0.053),
                        PointCoordinate(0.063, 0.063),
                        PointCoordinate(0.083, 0.053),
                        PointCoordinate(0.073, 0.043),
                    ]
                ),
                "branch_type": "Side shoot",
                "side_shoot_quality_options": "Short length",
            },
            {
                "label_ref": "branch_012",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate(0.073, 0.023),
                        PointCoordinate(0.093, 0.033),
                        PointCoordinate(0.113, 0.023),
                        PointCoordinate(0.103, 0.013),
                    ]
                ),
                "branch_type": "Other branch type",
                "Specify branch type": "Cane",
            },
        ],
    },
    "cherries-vid-001.mp4": {
        103: [
            {
                "label_ref": "branch_013",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate(0.013, 0.023),
                        PointCoordinate(0.033, 0.033),
                        PointCoordinate(0.053, 0.023),
                        PointCoordinate(0.043, 0.013),
                    ]
                ),
                "branch_type": "Side shoot",
                "side_shoot_quality_options": "Short length",
            },
            {
                "label_ref": "branch_014",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate(0.043, 0.053),
                        PointCoordinate(0.063, 0.063),
                        PointCoordinate(0.083, 0.053),
                        PointCoordinate(0.073, 0.043),
                    ]
                ),
                "branch_type": "Fruiting spur",
                "fruiting_spur_quality_options": "Short length, High bud density, Healthy",
            },
            {
                "label_ref": "branch_015",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate(0.073, 0.023),
                        PointCoordinate(0.093, 0.033),
                        PointCoordinate(0.113, 0.023),
                        PointCoordinate(0.103, 0.013),
                    ]
                ),
                "branch_type": "Other branch type",
                "Specify branch type": "Cane",
            },
        ],
        104: [
            {
                "label_ref": "branch_016",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate(0.013, 0.023),
                        PointCoordinate(0.033, 0.033),
                        PointCoordinate(0.053, 0.023),
                        PointCoordinate(0.043, 0.013),
                    ]
                ),
                "branch_type": "Side shoot",
                "side_shoot_quality_options": "Short length",
            },
            {
                "label_ref": "branch_014",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate(0.0413, 0.0523),
                        PointCoordinate(0.0613, 0.0623),
                        PointCoordinate(0.0813, 0.0523),
                        PointCoordinate(0.0713, 0.0423),
                    ]
                ),
                "branch_type": "Fruiting spur",
                "fruiting_spur_quality_options": "Short length, High bud density, Healthy",
            },
            {
                "label_ref": "branch_017",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate(0.073, 0.023),
                        PointCoordinate(0.093, 0.033),
                        PointCoordinate(0.113, 0.023),
                        PointCoordinate(0.103, 0.013),
                    ]
                ),
                "branch_type": "Other branch type",
                "Specify branch type": "Cane",
            },
        ],
        105: [
            {
                "label_ref": "branch_016",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate(0.0113, 0.0223),
                        PointCoordinate(0.0313, 0.0323),
                        PointCoordinate(0.0513, 0.0223),
                        PointCoordinate(0.0413, 0.0123),
                    ]
                ),
                "branch_type": "Side shoot",
                "side_shoot_quality_options": "Short length",
            },
            {
                "label_ref": "branch_014",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate(0.0433, 0.0553),
                        PointCoordinate(0.0633, 0.0653),
                        PointCoordinate(0.0833, 0.0553),
                        PointCoordinate(0.0733, 0.0453),
                    ]
                ),
                "branch_type": "Fruiting spur",
                "fruiting_spur_quality_options": "Short length, High bud density, Healthy",
            },
            {
                "label_ref": "branch_017",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate(0.0713, 0.0223),
                        PointCoordinate(0.0913, 0.0323),
                        PointCoordinate(0.1113, 0.0223),
                        PointCoordinate(0.1013, 0.0123),
                    ]
                ),
                "branch_type": "Other branch type",
                "Specify branch type": "Cane",
            },
        ],
    },
}

# Bundle size
BUNDLE_SIZE = 100

# Cache label rows after initialization
label_row_map = {}

# Step 1: Initialize all label rows using a bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for data_unit in video_image_frame_labels.keys():
        label_rows = project.list_label_rows_v2(data_title_eq=data_unit)
        if not label_rows:
            print(f"Skipping: No label row found for {data_unit}")
            continue

        label_row = label_rows[0]
        label_row.initialise_labels(bundle=bundle)
        label_row_map[data_unit] = label_row  # Cache the initialized label row

# Step 2: Process all frame coordinates and prepare label rows for saving
label_rows_to_save = []

for data_unit, frame_coordinates in video_image_frame_labels.items():
    label_row = label_row_map.get(data_unit)
    if not label_row:
        print(f"Skipping: No initialized label row found for {data_unit}")
        continue

    object_instances_by_label_ref = {}

    for frame_number, items in frame_coordinates.items():
        if not isinstance(items, list):
            items = [items]

        for item in items:
            label_ref = item["label_ref"]
            coord = item["coordinates"]
            branch_type = item["branch_type"]

            if label_ref not in object_instances_by_label_ref:
                polyline_object_instance: ObjectInstance = polyline_ontology_object.create_instance()
                checklist_attribute = None
                quality_options = []

                # Assign radio and checklist attributes based on branch type
                if branch_type == "Fruiting spur":
                    polyline_object_instance.set_answer(
                        attribute=branch_type_radio_attribute, answer=fruiting_spur_option
                    )
                    checklist_attribute = fruiting_spur_checklist_attribute
                    quality_options = item.get("fruiting_spur_quality_options", "").split(", ")
                elif branch_type == "Sucker":
                    polyline_object_instance.set_answer(attribute=branch_type_radio_attribute, answer=sucker_option)
                    checklist_attribute = sucker_checklist_attribute
                    quality_options = item.get("sucker_quality_options", "").split(", ")
                elif branch_type == "Side shoot":
                    polyline_object_instance.set_answer(attribute=branch_type_radio_attribute, answer=side_shoot_option)
                    checklist_attribute = side_shoot_checklist_attribute
                    quality_options = item.get("side_shoot_quality_options", "").split(", ")
                elif branch_type == "Other branch type":
                    polyline_object_instance.set_answer(
                        attribute=branch_type_radio_attribute, answer=other_branch_option
                    )
                    polyline_object_instance.set_answer(
                        attribute=other_branch_option_text_attribute, answer=item.get("Specify branch type", "")
                    )
                    quality_options = []

                # Process checklist options
                checklist_answers = []
                for quality in quality_options:
                    option = None
                    if quality == "Short length":
                        option = (
                            fruiting_spur_short_length_option
                            if branch_type == "Fruiting spur"
                            else sucker_short_length_option
                            if branch_type == "Sucker"
                            else side_shoot_short_length_option
                            if branch_type == "Side shoot"
                            else None
                        )
                    elif quality == "High bud density":
                        option = (
                            fruiting_spur_high_bud_density_option
                            if branch_type == "Fruiting spur"
                            else sucker_high_bud_density_option
                            if branch_type == "Sucker"
                            else side_shoot_high_bud_density_option
                            if branch_type == "Side shoot"
                            else None
                        )
                    elif quality == "Healthy":
                        option = (
                            fruiting_spur_healthy_option
                            if branch_type == "Fruiting spur"
                            else sucker_healthy_option
                            if branch_type == "Sucker"
                            else side_shoot_healthy_option
                            if branch_type == "Side shoot"
                            else None
                        )

                    if option:
                        checklist_answers.append(option)

                if checklist_attribute and checklist_answers:
                    polyline_object_instance.set_answer(
                        attribute=checklist_attribute, answer=checklist_answers, overwrite=True
                    )

                object_instances_by_label_ref[label_ref] = polyline_object_instance

            else:
                polyline_object_instance = object_instances_by_label_ref[label_ref]

            # Assign coordinates for this frame
            polyline_object_instance.set_for_frames(coordinates=coord, frames=frame_number)

    # Add object instances to the label row if they have frames assigned
    for polyline_object_instance in object_instances_by_label_ref.values():
        if polyline_object_instance.get_annotation_frames():
            label_row.add_object_instance(polyline_object_instance)

    label_rows_to_save.append(label_row)

# Step 3: Save all label rows using a bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for label_row in label_rows_to_save:
        label_row.save(bundle=bundle)
        print(f"Saved label row for {label_row.data_title}")

print("Labels with branch type radio buttons, checklist attributes, and text labels added for all data units.")
