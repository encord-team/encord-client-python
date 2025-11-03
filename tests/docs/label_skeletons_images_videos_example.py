"""
Code Block Name: Primatives Images/Videos
"""

# Import dependencies

from encord import EncordUserClient, Project
from encord.objects import ChecklistAttribute, Object, ObjectInstance, Option, RadioAttribute, TextAttribute
from encord.objects.coordinates import SkeletonCoordinate, SkeletonCoordinates
from encord.objects.skeleton_template import SkeletonTemplate

# User input
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
assert ontology_structure is not None, "Ontology structure is missing from the project"

# Get the skeleton annotation object
skeleton_ontology_object: Object = ontology_structure.get_child_by_title(title="Strawberries", type_=Object)
assert skeleton_ontology_object is not None, "Object 'Strawberries' not found in ontology"

# Get skeleton template
assert "Triangle" in project.ontology_structure.skeleton_templates, "Skeleton template 'Triangle' not found"
skeleton_template: SkeletonTemplate = project.ontology_structure.skeleton_templates["Triangle"]
assert skeleton_template is not None, "Skeleton template 'Triangle' is None"

# Get skeleton point IDs
skeleton_ids = [coord.feature_hash for coord in skeleton_template.skeleton.values()]
assert skeleton_ids, "Skeleton template 'Triangle' has no keypoints"

# Get radio attribute for strawberry type
strawberry_type_radio_attribute = ontology_structure.get_child_by_title(type_=RadioAttribute, title="Type?")
assert strawberry_type_radio_attribute is not None, "Radio attribute 'Type?' not found"

# Get radio options
albion_option = strawberry_type_radio_attribute.get_child_by_title(type_=Option, title="Albion")
assert albion_option is not None, "Option 'Albion' not found under 'Type?'"

redcoat_option = strawberry_type_radio_attribute.get_child_by_title(type_=Option, title="Redcoat")
assert redcoat_option is not None, "Option 'Redcoat' not found under 'Type?'"

sweet_kiss_option = strawberry_type_radio_attribute.get_child_by_title(type_=Option, title="Sweet Kiss")
assert sweet_kiss_option is not None, "Option 'Sweet Kiss' not found under 'Type?'"

other_strawberry_option = strawberry_type_radio_attribute.get_child_by_title(
    type_=Option, title="Other strawberry type"
)
assert other_strawberry_option is not None, "Option 'Other strawberry type' not found under 'Type?'"

# Albion Qualities
albion_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="Albion Qualities?")
assert albion_checklist_attribute is not None, "Checklist attribute 'Albion Qualities?' not found"

albion_plump_option = albion_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
assert albion_plump_option is not None, "Option 'Plump' not found under 'Albion Qualities?'"

albion_juicy_option = albion_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
assert albion_juicy_option is not None, "Option 'Juicy' not found under 'Albion Qualities?'"

albion_large_option = albion_checklist_attribute.get_child_by_title(type_=Option, title="Large")
assert albion_large_option is not None, "Option 'Large' not found under 'Albion Qualities?'"

# Redcoat Qualities
redcoat_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Redcoat Qualities?"
)
assert redcoat_checklist_attribute is not None, "Checklist attribute 'Redcoat Qualities?' not found"

redcoat_plump_option = redcoat_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
assert redcoat_plump_option is not None, "Option 'Plump' not found under 'Redcoat Qualities?'"

redcoat_juicy_option = redcoat_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
assert redcoat_juicy_option is not None, "Option 'Juicy' not found under 'Redcoat Qualities?'"

redcoat_large_option = redcoat_checklist_attribute.get_child_by_title(type_=Option, title="Large")
assert redcoat_large_option is not None, "Option 'Large' not found under 'Redcoat Qualities?'"

# Sweet Kiss Qualities
sweet_kiss_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Sweet Kiss Qualities?"
)
assert sweet_kiss_checklist_attribute is not None, "Checklist attribute 'Sweet Kiss Qualities?' not found"

sweet_kiss_plump_option = sweet_kiss_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
assert sweet_kiss_plump_option is not None, "Option 'Plump' not found under 'Sweet Kiss Qualities?'"

sweet_kiss_juicy_option = sweet_kiss_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
assert sweet_kiss_juicy_option is not None, "Option 'Juicy' not found under 'Sweet Kiss Qualities?'"

sweet_kiss_large_option = sweet_kiss_checklist_attribute.get_child_by_title(type_=Option, title="Large")
assert sweet_kiss_large_option is not None, "Option 'Large' not found under 'Sweet Kiss Qualities?'"

# Other strawberry type (text input)
other_strawberry_option_text_attribute = ontology_structure.get_child_by_title(
    type_=TextAttribute, title="Specify strawberry type"
)
assert other_strawberry_option_text_attribute is not None, "Text attribute 'Specify strawberry type' not found"

# Dictionary of labels per data unit and per frame with strawberry type specified, including quality options
video_frame_labels = {
    "cherries-001.jpg": {
        0: {
            "label_ref": "strawberry_001",
            "coordinates": SkeletonCoordinates(
                values=[
                    SkeletonCoordinate(
                        x=0.25, y=0.25, name="point_0", color="#000000", value="point_0", feature_hash=skeleton_ids[0]
                    ),
                    SkeletonCoordinate(
                        x=0.35, y=0.25, name="point_1", color="#000000", value="point_1", feature_hash=skeleton_ids[1]
                    ),
                    SkeletonCoordinate(
                        x=0.25, y=0.35, name="point_2", color="#000000", value="point_2", feature_hash=skeleton_ids[2]
                    ),
                ],
                name="Triangle",
            ),
            "strawberry_type": "Albion",
            "albion_quality_options": "Plump, Juicy",
        }
    },
    "cherries-010.jpg": {
        0: [
            {
                "label_ref": "strawberry_002",
                "coordinates": SkeletonCoordinates(
                    values=[
                        SkeletonCoordinate(
                            x=0.25,
                            y=0.25,
                            name="point_0",
                            color="#000000",
                            value="point_0",
                            feature_hash=skeleton_ids[0],
                        ),
                        SkeletonCoordinate(
                            x=0.35,
                            y=0.25,
                            name="point_1",
                            color="#000000",
                            value="point_1",
                            feature_hash=skeleton_ids[1],
                        ),
                        SkeletonCoordinate(
                            x=0.25,
                            y=0.35,
                            name="point_2",
                            color="#000000",
                            value="point_2",
                            feature_hash=skeleton_ids[2],
                        ),
                    ],
                    name="Triangle",
                ),
                "strawberry_type": "Redcoat",
                "redcoat_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "strawberry_003",
                "coordinates": SkeletonCoordinates(
                    values=[
                        SkeletonCoordinate(
                            x=0.45,
                            y=0.45,
                            name="point_0",
                            color="#000000",
                            value="point_0",
                            feature_hash=skeleton_ids[0],
                        ),
                        SkeletonCoordinate(
                            x=0.55,
                            y=0.45,
                            name="point_1",
                            color="#000000",
                            value="point_1",
                            feature_hash=skeleton_ids[1],
                        ),
                        SkeletonCoordinate(
                            x=0.45,
                            y=0.55,
                            name="point_2",
                            color="#000000",
                            value="point_2",
                            feature_hash=skeleton_ids[2],
                        ),
                    ],
                    name="Triangle",
                ),
                "strawberry_type": "Sweet Kiss",
                "sweet_kiss_quality_options": "Plump",
            },
            {
                "label_ref": "strawberry_004",
                "coordinates": SkeletonCoordinates(
                    values=[
                        SkeletonCoordinate(
                            x=0.65,
                            y=0.65,
                            name="point_0",
                            color="#000000",
                            value="point_0",
                            feature_hash=skeleton_ids[0],
                        ),
                        SkeletonCoordinate(
                            x=0.75,
                            y=0.65,
                            name="point_1",
                            color="#000000",
                            value="point_1",
                            feature_hash=skeleton_ids[1],
                        ),
                        SkeletonCoordinate(
                            x=0.65,
                            y=0.75,
                            name="point_2",
                            color="#000000",
                            value="point_2",
                            feature_hash=skeleton_ids[2],
                        ),
                    ],
                    name="Triangle",
                ),
                "strawberry_type": "Other strawberry type",
                "Specify strawberry type": "Pineberry",
            },
        ],
    },
    "cherries-ig": {
        0: {
            "label_ref": "strawberry_005",
            "coordinates": SkeletonCoordinates(
                values=[
                    SkeletonCoordinate(
                        x=0.25, y=0.25, name="point_0", color="#000000", value="point_0", feature_hash=skeleton_ids[0]
                    ),
                    SkeletonCoordinate(
                        x=0.35, y=0.25, name="point_1", color="#000000", value="point_1", feature_hash=skeleton_ids[1]
                    ),
                    SkeletonCoordinate(
                        x=0.25, y=0.35, name="point_2", color="#000000", value="point_2", feature_hash=skeleton_ids[2]
                    ),
                ],
                name="Triangle",
            ),
            "strawberry_type": "Albion",
            "albion_quality_options": "Plump, Juicy",
        },
        2: [
            {
                "label_ref": "strawberry_006",
                "coordinates": SkeletonCoordinates(
                    values=[
                        SkeletonCoordinate(
                            x=0.25,
                            y=0.25,
                            name="point_0",
                            color="#000000",
                            value="point_0",
                            feature_hash=skeleton_ids[0],
                        ),
                        SkeletonCoordinate(
                            x=0.35,
                            y=0.25,
                            name="point_1",
                            color="#000000",
                            value="point_1",
                            feature_hash=skeleton_ids[1],
                        ),
                        SkeletonCoordinate(
                            x=0.25,
                            y=0.35,
                            name="point_2",
                            color="#000000",
                            value="point_2",
                            feature_hash=skeleton_ids[2],
                        ),
                    ],
                    name="Triangle",
                ),
                "strawberry_type": "Redcoat",
                "redcoat_quality_options": "Large",
            },
            {
                "label_ref": "strawberry_007",
                "coordinates": SkeletonCoordinates(
                    values=[
                        SkeletonCoordinate(
                            x=0.45,
                            y=0.45,
                            name="point_0",
                            color="#000000",
                            value="point_0",
                            feature_hash=skeleton_ids[0],
                        ),
                        SkeletonCoordinate(
                            x=0.55,
                            y=0.45,
                            name="point_1",
                            color="#000000",
                            value="point_1",
                            feature_hash=skeleton_ids[1],
                        ),
                        SkeletonCoordinate(
                            x=0.45,
                            y=0.55,
                            name="point_2",
                            color="#000000",
                            value="point_2",
                            feature_hash=skeleton_ids[2],
                        ),
                    ],
                    name="Triangle",
                ),
                "strawberry_type": "Sweet Kiss",
                "sweet_kiss_quality_options": "Plump",
            },
            {
                "label_ref": "strawberry_008",
                "coordinates": SkeletonCoordinates(
                    values=[
                        SkeletonCoordinate(
                            x=0.65,
                            y=0.65,
                            name="point_0",
                            color="#000000",
                            value="point_0",
                            feature_hash=skeleton_ids[0],
                        ),
                        SkeletonCoordinate(
                            x=0.75,
                            y=0.65,
                            name="point_1",
                            color="#000000",
                            value="point_1",
                            feature_hash=skeleton_ids[1],
                        ),
                        SkeletonCoordinate(
                            x=0.65,
                            y=0.75,
                            name="point_2",
                            color="#000000",
                            value="point_2",
                            feature_hash=skeleton_ids[2],
                        ),
                    ],
                    name="Triangle",
                ),
                "strawberry_type": "Other strawberry type",
                "Specify strawberry type": "Pineberry",
            },
        ],
    },
    "cherries-is": {
        0: {
            "label_ref": "strawberry_009",
            "coordinates": SkeletonCoordinates(
                values=[
                    SkeletonCoordinate(
                        x=0.25, y=0.25, name="point_0", color="#000000", value="point_0", feature_hash=skeleton_ids[0]
                    ),
                    SkeletonCoordinate(
                        x=0.35, y=0.25, name="point_1", color="#000000", value="point_1", feature_hash=skeleton_ids[1]
                    ),
                    SkeletonCoordinate(
                        x=0.25, y=0.35, name="point_2", color="#000000", value="point_2", feature_hash=skeleton_ids[2]
                    ),
                ],
                name="Triangle",
            ),
            "strawberry_type": "Albion",
            "albion_quality_options": "Plump",
        },
        3: [
            {
                "label_ref": "strawberry_010",
                "coordinates": SkeletonCoordinates(
                    values=[
                        SkeletonCoordinate(
                            x=0.25,
                            y=0.25,
                            name="point_0",
                            color="#000000",
                            value="point_0",
                            feature_hash=skeleton_ids[0],
                        ),
                        SkeletonCoordinate(
                            x=0.35,
                            y=0.25,
                            name="point_1",
                            color="#000000",
                            value="point_1",
                            feature_hash=skeleton_ids[1],
                        ),
                        SkeletonCoordinate(
                            x=0.25,
                            y=0.35,
                            name="point_2",
                            color="#000000",
                            value="point_2",
                            feature_hash=skeleton_ids[2],
                        ),
                    ],
                    name="Triangle",
                ),
                "strawberry_type": "Redcoat",
                "redcoat_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "strawberry_011",
                "coordinates": SkeletonCoordinates(
                    values=[
                        SkeletonCoordinate(
                            x=0.45,
                            y=0.45,
                            name="point_0",
                            color="#000000",
                            value="point_0",
                            feature_hash=skeleton_ids[0],
                        ),
                        SkeletonCoordinate(
                            x=0.55,
                            y=0.45,
                            name="point_1",
                            color="#000000",
                            value="point_1",
                            feature_hash=skeleton_ids[1],
                        ),
                        SkeletonCoordinate(
                            x=0.45,
                            y=0.55,
                            name="point_2",
                            color="#000000",
                            value="point_2",
                            feature_hash=skeleton_ids[2],
                        ),
                    ],
                    name="Triangle",
                ),
                "strawberry_type": "Sweet Kiss",
                "sweet_kiss_quality_options": "Plump",
            },
            {
                "label_ref": "strawberry_012",
                "coordinates": SkeletonCoordinates(
                    values=[
                        SkeletonCoordinate(
                            x=0.65,
                            y=0.65,
                            name="point_0",
                            color="#000000",
                            value="point_0",
                            feature_hash=skeleton_ids[0],
                        ),
                        SkeletonCoordinate(
                            x=0.75,
                            y=0.65,
                            name="point_1",
                            color="#000000",
                            value="point_1",
                            feature_hash=skeleton_ids[1],
                        ),
                        SkeletonCoordinate(
                            x=0.65,
                            y=0.75,
                            name="point_2",
                            color="#000000",
                            value="point_2",
                            feature_hash=skeleton_ids[2],
                        ),
                    ],
                    name="Triangle",
                ),
                "strawberry_type": "Other strawberry type",
                "Specify strawberry type": "Pineberry",
            },
        ],
    },
    "cherries-vid-001.mp4": {
        103: [
            {
                "label_ref": "strawberry_013",
                "coordinates": SkeletonCoordinates(
                    values=[
                        SkeletonCoordinate(
                            x=0.25,
                            y=0.25,
                            name="point_0",
                            color="#000000",
                            value="point_0",
                            feature_hash=skeleton_ids[0],
                        ),
                        SkeletonCoordinate(
                            x=0.35,
                            y=0.25,
                            name="point_1",
                            color="#000000",
                            value="point_1",
                            feature_hash=skeleton_ids[1],
                        ),
                        SkeletonCoordinate(
                            x=0.25,
                            y=0.35,
                            name="point_2",
                            color="#000000",
                            value="point_2",
                            feature_hash=skeleton_ids[2],
                        ),
                    ],
                    name="Triangle",
                ),
                "strawberry_type": "Sweet Kiss",
                "sweet_kiss_quality_options": "Plump",
            },
            {
                "label_ref": "strawberry_014",
                "coordinates": SkeletonCoordinates(
                    values=[
                        SkeletonCoordinate(
                            x=0.45,
                            y=0.45,
                            name="point_0",
                            color="#000000",
                            value="point_0",
                            feature_hash=skeleton_ids[0],
                        ),
                        SkeletonCoordinate(
                            x=0.55,
                            y=0.45,
                            name="point_1",
                            color="#000000",
                            value="point_1",
                            feature_hash=skeleton_ids[1],
                        ),
                        SkeletonCoordinate(
                            x=0.45,
                            y=0.55,
                            name="point_2",
                            color="#000000",
                            value="point_2",
                            feature_hash=skeleton_ids[2],
                        ),
                    ],
                    name="Triangle",
                ),
                "strawberry_type": "Albion",
                "albion_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "strawberry_015",
                "coordinates": SkeletonCoordinates(
                    values=[
                        SkeletonCoordinate(
                            x=0.65,
                            y=0.65,
                            name="point_0",
                            color="#000000",
                            value="point_0",
                            feature_hash=skeleton_ids[0],
                        ),
                        SkeletonCoordinate(
                            x=0.75,
                            y=0.65,
                            name="point_1",
                            color="#000000",
                            value="point_1",
                            feature_hash=skeleton_ids[1],
                        ),
                        SkeletonCoordinate(
                            x=0.65,
                            y=0.75,
                            name="point_2",
                            color="#000000",
                            value="point_2",
                            feature_hash=skeleton_ids[2],
                        ),
                    ],
                    name="Triangle",
                ),
                "strawberry_type": "Other strawberry type",
                "Specify strawberry type": "Pineberry",
            },
        ],
        104: [
            {
                "label_ref": "strawberry_016",
                "coordinates": SkeletonCoordinates(
                    values=[
                        SkeletonCoordinate(
                            x=0.15,
                            y=0.15,
                            name="point_0",
                            color="#000000",
                            value="point_0",
                            feature_hash=skeleton_ids[0],
                        ),
                        SkeletonCoordinate(
                            x=0.25,
                            y=0.25,
                            name="point_1",
                            color="#000000",
                            value="point_1",
                            feature_hash=skeleton_ids[1],
                        ),
                        SkeletonCoordinate(
                            x=0.15,
                            y=0.15,
                            name="point_2",
                            color="#000000",
                            value="point_2",
                            feature_hash=skeleton_ids[2],
                        ),
                    ],
                    name="Triangle",
                ),
                "strawberry_type": "Sweet Kiss",
                "sweet_kiss_quality_options": "Plump",
            },
            {
                "label_ref": "strawberry_014",
                "coordinates": SkeletonCoordinates(
                    values=[
                        SkeletonCoordinate(
                            x=0.35,
                            y=0.35,
                            name="point_0",
                            color="#000000",
                            value="point_0",
                            feature_hash=skeleton_ids[0],
                        ),
                        SkeletonCoordinate(
                            x=0.45,
                            y=0.35,
                            name="point_1",
                            color="#000000",
                            value="point_1",
                            feature_hash=skeleton_ids[1],
                        ),
                        SkeletonCoordinate(
                            x=0.35,
                            y=0.45,
                            name="point_2",
                            color="#000000",
                            value="point_2",
                            feature_hash=skeleton_ids[2],
                        ),
                    ],
                    name="Triangle",
                ),
                "strawberry_type": "Albion",
                "albion_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "strawberry_017",
                "coordinates": SkeletonCoordinates(
                    values=[
                        SkeletonCoordinate(
                            x=0.55,
                            y=0.55,
                            name="point_0",
                            color="#000000",
                            value="point_0",
                            feature_hash=skeleton_ids[0],
                        ),
                        SkeletonCoordinate(
                            x=0.65,
                            y=0.55,
                            name="point_1",
                            color="#000000",
                            value="point_1",
                            feature_hash=skeleton_ids[1],
                        ),
                        SkeletonCoordinate(
                            x=0.55,
                            y=0.65,
                            name="point_2",
                            color="#000000",
                            value="point_2",
                            feature_hash=skeleton_ids[2],
                        ),
                    ],
                    name="Triangle",
                ),
                "strawberry_type": "Other strawberry type",
                "Specify strawberry type": "Pineberry",
            },
        ],
        105: [
            {
                "label_ref": "strawberry_016",
                "coordinates": SkeletonCoordinates(
                    values=[
                        SkeletonCoordinate(
                            x=0.25,
                            y=0.25,
                            name="point_0",
                            color="#000000",
                            value="point_0",
                            feature_hash=skeleton_ids[0],
                        ),
                        SkeletonCoordinate(
                            x=0.35,
                            y=0.25,
                            name="point_1",
                            color="#000000",
                            value="point_1",
                            feature_hash=skeleton_ids[1],
                        ),
                        SkeletonCoordinate(
                            x=0.25,
                            y=0.35,
                            name="point_2",
                            color="#000000",
                            value="point_2",
                            feature_hash=skeleton_ids[2],
                        ),
                    ],
                    name="Triangle",
                ),
                "strawberry_type": "Sweet Kiss",
                "sweet_kiss_quality_options": "Plump",
            },
            {
                "label_ref": "strawberry_014",
                "coordinates": SkeletonCoordinates(
                    values=[
                        SkeletonCoordinate(
                            x=0.45,
                            y=0.45,
                            name="point_0",
                            color="#000000",
                            value="point_0",
                            feature_hash=skeleton_ids[0],
                        ),
                        SkeletonCoordinate(
                            x=0.55,
                            y=0.45,
                            name="point_1",
                            color="#000000",
                            value="point_1",
                            feature_hash=skeleton_ids[1],
                        ),
                        SkeletonCoordinate(
                            x=0.45,
                            y=0.55,
                            name="point_2",
                            color="#000000",
                            value="point_2",
                            feature_hash=skeleton_ids[2],
                        ),
                    ],
                    name="Triangle",
                ),
                "strawberry_type": "Albion",
                "albion_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "strawberry_017",
                "coordinates": SkeletonCoordinates(
                    values=[
                        SkeletonCoordinate(
                            x=0.75,
                            y=0.75,
                            name="point_0",
                            color="#000000",
                            value="point_0",
                            feature_hash=skeleton_ids[0],
                        ),
                        SkeletonCoordinate(
                            x=0.65,
                            y=0.75,
                            name="point_1",
                            color="#000000",
                            value="point_1",
                            feature_hash=skeleton_ids[1],
                        ),
                        SkeletonCoordinate(
                            x=0.75,
                            y=0.65,
                            name="point_2",
                            color="#000000",
                            value="point_2",
                            feature_hash=skeleton_ids[2],
                        ),
                    ],
                    name="Triangle",
                ),
                "strawberry_type": "Other strawberry type",
                "Specify strawberry type": "Pineberry",
            },
        ],
    },
}


# Loop through each data unit (image, video, etc.)
for data_unit, frame_coordinates in video_frame_labels.items():
    object_instances_by_label_ref = {}

    # Get the label row for the current data unit
    label_rows = project.list_label_rows_v2(data_title_eq=data_unit)
    assert isinstance(label_rows, list), f"Expected list of label rows for '{data_unit}', got {type(label_rows)}"
    assert label_rows, f"No label row found for data unit: {data_unit}"

    label_row = label_rows[0]
    assert label_row is not None, f"Label row is None for {data_unit}"

    # Initialize label row using bundle
    with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
        label_row.initialise_labels()
        assert label_row.ontology_structure is not None, f"Ontology not initialized for label row: {data_unit}"

        for frame_number, items in frame_coordinates.items():
            assert isinstance(frame_number, int), f"Frame number must be int, got {type(frame_number)}"
            if not isinstance(items, list):
                items = [items]

            for item in items:
                label_ref = item["label_ref"]
                coord = item["coordinates"]
                strawberry_type = item["strawberry_type"]

                assert strawberry_type in {
                    "Albion",
                    "Redcoat",
                    "Sweet Kiss",
                    "Other strawberry type",
                }, f"Unexpected strawberry type '{strawberry_type}' in data unit '{data_unit}'"

                if label_ref not in object_instances_by_label_ref:
                    skeleton_object_instance: ObjectInstance = skeleton_ontology_object.create_instance()
                    assert skeleton_object_instance is not None, f"Failed to create ObjectInstance for {label_ref}"

                    object_instances_by_label_ref[label_ref] = skeleton_object_instance
                    checklist_attribute = None

                    # Set strawberry type radio attribute
                    if strawberry_type == "Albion":
                        assert albion_option is not None, "Missing 'albion_option'"
                        skeleton_object_instance.set_answer(
                            attribute=strawberry_type_radio_attribute, answer=albion_option
                        )
                        checklist_attribute = albion_checklist_attribute
                    elif strawberry_type == "Redcoat":
                        assert redcoat_option is not None, "Missing 'redcoat_option'"
                        skeleton_object_instance.set_answer(
                            attribute=strawberry_type_radio_attribute, answer=redcoat_option
                        )
                        checklist_attribute = redcoat_checklist_attribute
                    elif strawberry_type == "Sweet Kiss":
                        assert sweet_kiss_option is not None, "Missing 'sweet_kiss_option'"
                        skeleton_object_instance.set_answer(
                            attribute=strawberry_type_radio_attribute, answer=sweet_kiss_option
                        )
                        checklist_attribute = sweet_kiss_checklist_attribute
                    elif strawberry_type == "Other strawberry type":
                        assert other_strawberry_option is not None, "Missing 'other_strawberry_option'"
                        skeleton_object_instance.set_answer(
                            attribute=strawberry_type_radio_attribute, answer=other_strawberry_option
                        )
                        text_answer = item.get("Specify strawberry type", "")
                        assert isinstance(text_answer, str), "'Specify strawberry type' must be a string"
                        skeleton_object_instance.set_answer(
                            attribute=other_strawberry_option_text_attribute,
                            answer=text_answer,
                        )

                    # Set checklist attributes
                    checklist_answers = []
                    quality_key = f"{strawberry_type.lower().replace(' ', '_')}_quality_options"
                    quality_options = item.get(quality_key, "").split(", ")

                    for quality in quality_options:
                        option = None
                        if quality == "Plump":
                            option = (
                                albion_plump_option
                                if strawberry_type == "Albion"
                                else redcoat_plump_option
                                if strawberry_type == "Redcoat"
                                else sweet_kiss_plump_option
                                if strawberry_type == "Sweet Kiss"
                                else None
                            )
                        elif quality == "Juicy":
                            option = (
                                albion_juicy_option
                                if strawberry_type == "Albion"
                                else redcoat_juicy_option
                                if strawberry_type == "Redcoat"
                                else sweet_kiss_juicy_option
                                if strawberry_type == "Sweet Kiss"
                                else None
                            )
                        elif quality == "Large":
                            option = (
                                albion_large_option
                                if strawberry_type == "Albion"
                                else redcoat_large_option
                                if strawberry_type == "Redcoat"
                                else sweet_kiss_large_option
                                if strawberry_type == "Sweet Kiss"
                                else None
                            )

                        if option:
                            checklist_answers.append(option)
                        else:
                            assert strawberry_type == "Other strawberry type", (
                                f"Invalid quality '{quality}' for strawberry type '{strawberry_type}'"
                            )

                    if checklist_attribute and checklist_answers:
                        skeleton_object_instance.set_answer(
                            attribute=checklist_attribute, answer=checklist_answers, overwrite=True
                        )

                else:
                    skeleton_object_instance = object_instances_by_label_ref[label_ref]

                # Assign the object to the frame and track it
                skeleton_object_instance.set_for_frames(coordinates=coord, frames=frame_number)

        # Add object instances to label_row **only if they have frames assigned**
        for skeleton_object_instance in object_instances_by_label_ref.values():
            assert isinstance(skeleton_object_instance, ObjectInstance), "Expected ObjectInstance type"
            if skeleton_object_instance.get_annotation_frames():
                label_row.add_object_instance(skeleton_object_instance)

        # Save label row using the bundle
        assert label_row is not None, "Trying to save a None label row"
        label_row.save(bundle=bundle)

print("Labels with strawberry type radio buttons, checklist attributes, and text labels added for all data units.")
