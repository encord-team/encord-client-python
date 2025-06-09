"""
Code Block Name: Polylines Images/Videos
"""

# Import dependencies
from pathlib import Path

from encord import EncordUserClient, Project
from encord.objects import ChecklistAttribute, Object, ObjectInstance, Option, RadioAttribute, TextAttribute
from encord.objects.coordinates import PointCoordinate, PolylineCoordinates

# User imput
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"
# SSH_PATH = get_ssh_key() # replace it with ssh key
PROJECT_ID = "00000000-0000-0000-0000-000000000000"
BUNDLE_SIZE = 100

# Create user client using ssh key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Get project for which labels are to be added
project: Project = user_client.get_project(PROJECT_ID)
assert project is not None, "Project not found — check PROJECT_ID"

# Get ontology structure
ontology_structure = project.ontology_structure
assert ontology_structure is not None, "Ontology structure is missing in the project"

# Get polyline object for branches
polyline_ontology_object: Object = ontology_structure.get_child_by_title(title="Branches", type_=Object)
assert polyline_ontology_object is not None, "Polyline object 'Branches' not found in ontology"

# Get radio attribute for branch type
branch_type_radio_attribute = ontology_structure.get_child_by_title(type_=RadioAttribute, title="Type?")
assert branch_type_radio_attribute is not None, "Radio attribute 'Type?' not found in ontology"

# Get radio options
fruiting_spur_option = branch_type_radio_attribute.get_child_by_title(type_=Option, title="Fruiting spur")
assert fruiting_spur_option is not None, "Option 'Fruiting spur' not found under radio attribute 'Type?'"

sucker_option = branch_type_radio_attribute.get_child_by_title(type_=Option, title="Sucker")
assert sucker_option is not None, "Option 'Sucker' not found under radio attribute 'Type?'"

side_shoot_option = branch_type_radio_attribute.get_child_by_title(type_=Option, title="Side shoot")
assert side_shoot_option is not None, "Option 'Side shoot' not found under radio attribute 'Type?'"

other_branch_option = branch_type_radio_attribute.get_child_by_title(type_=Option, title="Other branch type")
assert other_branch_option is not None, "Option 'Other branch type' not found under radio attribute 'Type?'"

# Fruiting spur Qualities
fruiting_spur_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Fruiting spur Qualities?"
)
assert fruiting_spur_checklist_attribute is not None, "Checklist attribute 'Fruiting spur Qualities?' not found"

fruiting_spur_short_length_option = fruiting_spur_checklist_attribute.get_child_by_title(
    type_=Option, title="Short length"
)
assert fruiting_spur_short_length_option is not None, "Option 'Short length' not found under 'Fruiting spur Qualities?'"

fruiting_spur_high_bud_density_option = fruiting_spur_checklist_attribute.get_child_by_title(
    type_=Option, title="High bud density"
)
assert (
    fruiting_spur_high_bud_density_option is not None
), "Option 'High bud density' not found under 'Fruiting spur Qualities?'"

fruiting_spur_healthy_option = fruiting_spur_checklist_attribute.get_child_by_title(type_=Option, title="Healthy")
assert fruiting_spur_healthy_option is not None, "Option 'Healthy' not found under 'Fruiting spur Qualities?'"

# Sucker Qualities
sucker_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="Sucker Qualities?")
assert sucker_checklist_attribute is not None, "Checklist attribute 'Sucker Qualities?' not found"

sucker_short_length_option = sucker_checklist_attribute.get_child_by_title(type_=Option, title="Short length")
assert sucker_short_length_option is not None, "Option 'Short length' not found under 'Sucker Qualities?'"

sucker_high_bud_density_option = sucker_checklist_attribute.get_child_by_title(type_=Option, title="High bud density")
assert sucker_high_bud_density_option is not None, "Option 'High bud density' not found under 'Sucker Qualities?'"

sucker_healthy_option = sucker_checklist_attribute.get_child_by_title(type_=Option, title="Healthy")
assert sucker_healthy_option is not None, "Option 'Healthy' not found under 'Sucker Qualities?'"

# Side shoot Qualities
side_shoot_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Side shoot Qualities?"
)
assert side_shoot_checklist_attribute is not None, "Checklist attribute 'Side shoot Qualities?' not found"

side_shoot_short_length_option = side_shoot_checklist_attribute.get_child_by_title(type_=Option, title="Short length")
assert side_shoot_short_length_option is not None, "Option 'Short length' not found under 'Side shoot Qualities?'"

side_shoot_high_bud_density_option = side_shoot_checklist_attribute.get_child_by_title(
    type_=Option, title="High bud density"
)
assert (
    side_shoot_high_bud_density_option is not None
), "Option 'High bud density' not found under 'Side shoot Qualities?'"

side_shoot_healthy_option = side_shoot_checklist_attribute.get_child_by_title(type_=Option, title="Healthy")
assert side_shoot_healthy_option is not None, "Option 'Healthy' not found under 'Side shoot Qualities?'"

# Other branch type text attribute
other_branch_option_text_attribute = ontology_structure.get_child_by_title(
    type_=TextAttribute, title="Specify branch type"
)
assert other_branch_option_text_attribute is not None, "Text attribute 'Specify branch type' not found"


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

# Cache label rows after initialization
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

        label_row_map[data_unit] = label_row  # Cache the initialized label row

# Step 2: Process all frame coordinates and prepare label rows for saving
label_rows_to_save = []

for data_unit, frame_coordinates in video_image_frame_labels.items():
    label_row = label_row_map.get(data_unit)
    assert label_row is not None, f"Label row not initialized for {data_unit}"

    object_instances_by_label_ref = {}

    for frame_number, items in frame_coordinates.items():
        assert isinstance(frame_number, int), f"Frame number must be int, got {type(frame_number)}"
        if not isinstance(items, list):
            items = [items]

        for item in items:
            label_ref = item["label_ref"]
            coord = item["coordinates"]
            branch_type = item["branch_type"]

            assert branch_type in {
                "Fruiting spur",
                "Sucker",
                "Side shoot",
                "Other branch type",
            }, f"Unexpected branch type '{branch_type}' in {data_unit}"

            if label_ref not in object_instances_by_label_ref:
                polyline_object_instance: ObjectInstance = polyline_ontology_object.create_instance()
                assert polyline_object_instance is not None, "Failed to create ObjectInstance"
                checklist_attribute = None
                quality_options = []

                # Assign radio and checklist attributes based on branch type
                if branch_type == "Fruiting spur":
                    assert fruiting_spur_option is not None, "Missing 'fruiting_spur_option'"
                    polyline_object_instance.set_answer(
                        attribute=branch_type_radio_attribute, answer=fruiting_spur_option
                    )
                    checklist_attribute = fruiting_spur_checklist_attribute
                    quality_options = item.get("fruiting_spur_quality_options", "").split(", ")
                elif branch_type == "Sucker":
                    assert sucker_option is not None, "Missing 'sucker_option'"
                    polyline_object_instance.set_answer(attribute=branch_type_radio_attribute, answer=sucker_option)
                    checklist_attribute = sucker_checklist_attribute
                    quality_options = item.get("sucker_quality_options", "").split(", ")
                elif branch_type == "Side shoot":
                    assert side_shoot_option is not None, "Missing 'side_shoot_option'"
                    polyline_object_instance.set_answer(attribute=branch_type_radio_attribute, answer=side_shoot_option)
                    checklist_attribute = side_shoot_checklist_attribute
                    quality_options = item.get("side_shoot_quality_options", "").split(", ")
                elif branch_type == "Other branch type":
                    assert other_branch_option is not None, "Missing 'other_branch_option'"
                    polyline_object_instance.set_answer(
                        attribute=branch_type_radio_attribute, answer=other_branch_option
                    )
                    text_answer = item.get("Specify branch type", "")
                    assert isinstance(text_answer, str), "'Specify branch type' must be a string"
                    polyline_object_instance.set_answer(
                        attribute=other_branch_option_text_attribute, answer=text_answer
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
                    else:
                        assert (
                            branch_type == "Other branch type"
                        ), f"Invalid quality '{quality}' for branch type '{branch_type}'"

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
        assert isinstance(polyline_object_instance, ObjectInstance), "Expected ObjectInstance type"
        if polyline_object_instance.get_annotation_frames():
            label_row.add_object_instance(polyline_object_instance)

    label_rows_to_save.append(label_row)

# Step 3: Save all label rows using a bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for label_row in label_rows_to_save:
        assert label_row is not None, "Trying to save a None label row"
        label_row.save(bundle=bundle)
        print(f"Saved label row for {label_row.data_title}")

print("Labels with branch type radio buttons, checklist attributes, and text labels added for all data units.")
