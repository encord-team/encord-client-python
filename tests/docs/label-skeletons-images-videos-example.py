# Import dependencies
from pathlib import Path

from encord import EncordUserClient, Project
from encord.objects import ChecklistAttribute, Object, ObjectInstance, Option, RadioAttribute, TextAttribute
from encord.objects.coordinates import SkeletonCoordinate, SkeletonCoordinates
from encord.objects.skeleton_template import SkeletonTemplate

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

# Create radio button attribute for strawberry type
ontology_structure = project.ontology_structure

# Find a bounding box annotation object in the project ontology
skeleton_ontology_object: Object = ontology_structure.get_child_by_title(title="Strawberries", type_=Object)

skeleton_template: SkeletonTemplate = project.ontology_structure.skeleton_templates["Triangle"]

skeleton_ids = [coord.feature_hash for coord in skeleton_template.skeleton.values()]

strawberry_type_radio_attribute = ontology_structure.get_child_by_title(type_=RadioAttribute, title="Type?")

# Create options for the radio buttons
albion_option = strawberry_type_radio_attribute.get_child_by_title(type_=Option, title="Albion")
redcoat_option = strawberry_type_radio_attribute.get_child_by_title(type_=Option, title="Redcoat")
sweet_kiss_option = strawberry_type_radio_attribute.get_child_by_title(type_=Option, title="Sweet Kiss")
other_strawberry_option = strawberry_type_radio_attribute.get_child_by_title(
    type_=Option, title="Other strawberry type"
)

# Create checklist attributes and options for each strawberry type
# Albion Qualities
albion_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="Albion Qualities?")
albion_plump_option = albion_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
albion_juicy_option = albion_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
albion_large_option = albion_checklist_attribute.get_child_by_title(type_=Option, title="Large")

# Redcoat Qualities
redcoat_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Redcoat Qualities?"
)
redcoat_plump_option = redcoat_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
redcoat_juicy_option = redcoat_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
redcoat_large_option = redcoat_checklist_attribute.get_child_by_title(type_=Option, title="Large")

# Sweet Kiss Qualities
sweet_kiss_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Sweet Kiss Qualities?"
)
sweet_kiss_plump_option = sweet_kiss_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
sweet_kiss_juicy_option = sweet_kiss_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
sweet_kiss_large_option = sweet_kiss_checklist_attribute.get_child_by_title(type_=Option, title="Large")

# Other strawberry Types
other_strawberry_option_text_attribute = ontology_structure.get_child_by_title(
    type_=TextAttribute, title="Specify strawberry type"
)


# Dictionary of labels per data unit and per frame with strawberry type specified, including quality options
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

# Bundle size
BUNDLE_SIZE = 100

# Loop through each data unit (image, video, etc.)
for data_unit, frame_coordinates in video_frame_labels.items():
    object_instances_by_label_ref = {}

    # Get the label row for the current data unit
    label_row = project.list_label_rows_v2(data_title_eq=data_unit)[0]

    # Initialize label row using bundle
    with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
        # Ensure labels are initialized correctly
        label_row.initialise_labels()

        # Now we can proceed with processing each frame and assigning labels
        for frame_number, items in frame_coordinates.items():
            if not isinstance(items, list):  # Multiple objects in the frame
                items = [items]

            for item in items:
                label_ref = item["label_ref"]
                coord = item["coordinates"]
                strawberry_type = item["strawberry_type"]

                # Check if label_ref already exists for reusability
                if label_ref not in object_instances_by_label_ref:
                    skeleton_object_instance: ObjectInstance = skeleton_ontology_object.create_instance()
                    object_instances_by_label_ref[label_ref] = skeleton_object_instance  # Store for reuse
                    checklist_attribute = None

                    # Set strawberry type attribute
                    if strawberry_type == "Albion":
                        skeleton_object_instance.set_answer(
                            attribute=strawberry_type_radio_attribute, answer=albion_option
                        )
                        checklist_attribute = albion_checklist_attribute
                    elif strawberry_type == "Redcoat":
                        skeleton_object_instance.set_answer(
                            attribute=strawberry_type_radio_attribute, answer=redcoat_option
                        )
                        checklist_attribute = redcoat_checklist_attribute
                    elif strawberry_type == "Sweet Kiss":
                        skeleton_object_instance.set_answer(
                            attribute=strawberry_type_radio_attribute, answer=sweet_kiss_option
                        )
                        checklist_attribute = sweet_kiss_checklist_attribute
                    elif strawberry_type == "Other strawberry type":
                        skeleton_object_instance.set_answer(
                            attribute=strawberry_type_radio_attribute, answer=other_strawberry_option
                        )
                        skeleton_object_instance.set_answer(
                            attribute=other_strawberry_option_text_attribute,
                            answer=item.get("Specify strawberry type", ""),
                        )

                    # Set checklist attributes
                    checklist_answers = []
                    quality_options = item.get(f"{strawberry_type.lower()}_quality_options", "").split(", ")

                    for quality in quality_options:
                        if quality == "Plump":
                            checklist_answers.append(
                                albion_plump_option
                                if strawberry_type == "Albion"
                                else redcoat_plump_option
                                if strawberry_type == "Redcoat"
                                else sweet_kiss_plump_option
                            )
                        elif quality == "Juicy":
                            checklist_answers.append(
                                albion_juicy_option
                                if strawberry_type == "Albion"
                                else redcoat_juicy_option
                                if strawberry_type == "Redcoat"
                                else sweet_kiss_juicy_option
                            )
                        elif quality == "Large":
                            checklist_answers.append(
                                albion_large_option
                                if strawberry_type == "Albion"
                                else redcoat_large_option
                                if strawberry_type == "Redcoat"
                                else sweet_kiss_large_option
                            )

                    if checklist_attribute and checklist_answers:
                        skeleton_object_instance.set_answer(
                            attribute=checklist_attribute, answer=checklist_answers, overwrite=True
                        )

                else:
                    # Reuse existing instance across frames
                    skeleton_object_instance = object_instances_by_label_ref[label_ref]

                # Assign the object to the frame and track it
                skeleton_object_instance.set_for_frames(coordinates=coord, frames=frame_number)

        # Add object instances to label_row **only if they have frames assigned**
        for skeleton_object_instance in object_instances_by_label_ref.values():
            if skeleton_object_instance.get_annotation_frames():  # Ensures it has at least one frame
                label_row.add_object_instance(skeleton_object_instance)

        # Save label row using the bundle
        label_row.save(bundle=bundle)

print("Labels with strawberry type radio buttons, checklist attributes, and text labels added for all data units.")
