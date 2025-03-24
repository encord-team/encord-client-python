# Import dependencies
from pathlib import Path

from encord import EncordUserClient, Project
from encord.objects import ChecklistAttribute, Object, ObjectInstance, Option, RadioAttribute, TextAttribute
from encord.objects.coordinates import PointCoordinate, PolygonCoordinates

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

# Create radio button attribute for blueberry type
ontology_structure = project.ontology_structure

# Find a bounding box annotation object in the project ontology
polygon_ontology_object: Object = ontology_structure.get_child_by_title(title="Blueberries", type_=Object)

blueberry_type_radio_attribute = ontology_structure.get_child_by_title(type_=RadioAttribute, title="Type?")

# Create options for the radio buttons
bluegold_option = blueberry_type_radio_attribute.get_child_by_title(type_=Option, title="Bluegold")
duke_option = blueberry_type_radio_attribute.get_child_by_title(type_=Option, title="Duke")
blueray_option = blueberry_type_radio_attribute.get_child_by_title(type_=Option, title="Blueray")
other_blueberry_option = blueberry_type_radio_attribute.get_child_by_title(type_=Option, title="Other blueberry type")

# Create checklist attributes and options for each blueberry type
# Bluegold Qualities
bluegold_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="Bluegold Qualities?")
bluegold_plump_option = bluegold_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
bluegold_juicy_option = bluegold_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
bluegold_large_option = bluegold_checklist_attribute.get_child_by_title(type_=Option, title="Large")

# Duke Qualities
duke_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="Duke Qualities?")
duke_plump_option = duke_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
duke_juicy_option = duke_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
duke_large_option = duke_checklist_attribute.get_child_by_title(type_=Option, title="Large")

# Blueray Qualities
blueray_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="Blueray Qualities?")
blueray_plump_option = blueray_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
blueray_juicy_option = blueray_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
blueray_large_option = blueray_checklist_attribute.get_child_by_title(type_=Option, title="Large")

# Other blueberry Types
other_blueberry_option_text_attribute = ontology_structure.get_child_by_title(
    type_=TextAttribute, title="Specify blueberry type"
)


# Dictionary of labels per data unit and per frame with blueberry type specified, including quality options
video_frame_labels = {
    "cherries-001.jpg": {
        0: {
            "label_ref": "blueberry_001",
            "coordinates": PolygonCoordinates(polygons=
                [
                [
                [
                    PointCoordinate(0.01, 0.02),
                    PointCoordinate(0.03, 0.03),
                    PointCoordinate(0.05, 0.02),
                    PointCoordinate(0.04, 0.01),
                    PointCoordinate(0.02, 0.01),
                ]
            ]
            ]
            ),
            "blueberry_type": "Bluegold",
            "bluegold_quality_options": "Plump, Juicy",
        }
    },
    "cherries-010.jpg": {
        0: [
            {
                "label_ref": "blueberry_002",
                "coordinates": PolygonCoordinates(polygons=[[
                    [
                        PointCoordinate(0.01, 0.02),
                        PointCoordinate(0.03, 0.03),
                        PointCoordinate(0.05, 0.02),
                        PointCoordinate(0.04, 0.01),
                        PointCoordinate(0.02, 0.01),
                    ]
                ]
                ]
                ),
                "blueberry_type": "Duke",
                "duke_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "blueberry_003",
                "coordinates": PolygonCoordinates(polygons=
                    [
                    [
                    [
                        PointCoordinate(0.04, 0.05),
                        PointCoordinate(0.06, 0.06),
                        PointCoordinate(0.08, 0.05),
                        PointCoordinate(0.07, 0.04),
                        PointCoordinate(0.05, 0.04),
                    ]
                    ]
                    ]
                ),
                "blueberry_type": "Blueray",
                "blueray_quality_options": "Plump",
            },
            {
                "label_ref": "blueberry_004",
                "coordinates": PolygonCoordinates(polygons=
                    [
                    [
                    [
                        PointCoordinate(0.07, 0.02),
                        PointCoordinate(0.09, 0.03),
                        PointCoordinate(0.11, 0.02),
                        PointCoordinate(0.10, 0.01),
                        PointCoordinate(0.08, 0.01),
                    ]
                    ]
                    ]
                ),
                "blueberry_type": "Other blueberry type",
                "Specify blueberry type": "Highbush",
            },
        ],
    },
    "cherries-ig": {
        0: {
            "label_ref": "blueberry_005",
            "coordinates": PolygonCoordinates(polygons=
                [
                [
                [
                    PointCoordinate(0.01, 0.02),
                    PointCoordinate(0.03, 0.03),
                    PointCoordinate(0.05, 0.02),
                    PointCoordinate(0.04, 0.01),
                    PointCoordinate(0.02, 0.01),
                ]
                ]
                ]
            ),
            "blueberry_type": "Bluegold",
            "bluegold_quality_options": "Plump, Juicy",
        },
        2: [
            {
                "label_ref": "blueberry_006",
                "coordinates": PolygonCoordinates(polygons=
                    [
                    [
                    [
                        PointCoordinate(0.01, 0.02),
                        PointCoordinate(0.03, 0.03),
                        PointCoordinate(0.05, 0.02),
                        PointCoordinate(0.04, 0.01),
                        PointCoordinate(0.02, 0.01),
                    ]
                    ]
                    ]
                ),
                "blueberry_type": "Duke",
                "duke_quality_options": "Large",
            },
            {
                "label_ref": "blueberry_007",
                "coordinates": PolygonCoordinates(polygons=
                    [
                    [
                    [
                        PointCoordinate(0.04, 0.05),
                        PointCoordinate(0.06, 0.06),
                        PointCoordinate(0.08, 0.05),
                        PointCoordinate(0.07, 0.04),
                        PointCoordinate(0.05, 0.04),
                    ]
                    ]
                    ]
                ),
                "blueberry_type": "Blueray",
                "blueray_quality_options": "Plump",
            },
            {
                "label_ref": "blueberry_008",
                "coordinates": PolygonCoordinates(polygons=
                    [
                    [
                    [
                        PointCoordinate(0.07, 0.02),
                        PointCoordinate(0.09, 0.03),
                        PointCoordinate(0.11, 0.02),
                        PointCoordinate(0.10, 0.01),
                        PointCoordinate(0.08, 0.01),
                    ]
                    ]
                    ]
                ),
                "blueberry_type": "Other blueberry type",
                "Specify blueberry type": "Lowbush",
            },
        ],
    },
    "cherries-is": {
        0: {
            "label_ref": "blueberry_009",
            "coordinates": PolygonCoordinates(polygons=
                    [
                    [
                [
                    PointCoordinate(0.01, 0.02),
                    PointCoordinate(0.03, 0.03),
                    PointCoordinate(0.05, 0.02),
                    PointCoordinate(0.04, 0.01),
                    PointCoordinate(0.02, 0.01),
                ]
                    ]
                    ]
            ),
            "blueberry_type": "Bluegold",
            "bluegold_quality_options": "Plump",
        },
        3: [
            {
                "label_ref": "blueberry_010",
                "coordinates": PolygonCoordinates(polygons=
                    [
                    [
                    [
                        PointCoordinate(0.01, 0.02),
                        PointCoordinate(0.03, 0.03),
                        PointCoordinate(0.05, 0.02),
                        PointCoordinate(0.04, 0.01),
                        PointCoordinate(0.02, 0.01),
                    ]
                    ]
                    ]
                ),
                "blueberry_type": "Duke",
                "duke_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "blueberry_011",
                "coordinates": PolygonCoordinates(polygons=
                    [
                    [
                    [
                        PointCoordinate(0.04, 0.05),
                        PointCoordinate(0.06, 0.06),
                        PointCoordinate(0.08, 0.05),
                        PointCoordinate(0.07, 0.04),
                        PointCoordinate(0.05, 0.04),
                    ]
                    ]
                    ]
                ),
                "blueberry_type": "Blueray",
                "blueray_quality_options": "Plump",
            },
            {
                "label_ref": "blueberry_012",
                "coordinates": PolygonCoordinates(
                    polygons=
                    [
                    [
                    [
                        PointCoordinate(0.07, 0.02),
                        PointCoordinate(0.09, 0.03),
                        PointCoordinate(0.11, 0.02),
                        PointCoordinate(0.10, 0.01),
                        PointCoordinate(0.08, 0.01),
                    ]
                    ]
                    ]
                ),
                "blueberry_type": "Other blueberry type",
                "Specify blueberry type": "Highbush",
            },
        ],
    },
    "cherries-vid-001.mp4": {
        103: [
            {
                "label_ref": "blueberry_013",
                "coordinates": PolygonCoordinates(polygons=
                    [
                    [
                    
                    [
                        PointCoordinate(0.01, 0.02),
                        PointCoordinate(0.03, 0.03),
                        PointCoordinate(0.05, 0.02),
                        PointCoordinate(0.04, 0.01),
                        PointCoordinate(0.02, 0.01),
                    ]
                    ]
                    ]
                ),
                "blueberry_type": "Blueray",
                "blueray_quality_options": "Plump",
            },
            {
                "label_ref": "blueberry_014",
                "coordinates": PolygonCoordinates(polygons=
                    [
                    [
                    [
                        PointCoordinate(0.04, 0.05),
                        PointCoordinate(0.06, 0.06),
                        PointCoordinate(0.08, 0.05),
                        PointCoordinate(0.07, 0.04),
                        PointCoordinate(0.05, 0.04),
                    ]
                    ]
                    ]
                ),
                "blueberry_type": "Bluegold",
                "bluegold_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "blueberry_015",
                "coordinates": PolygonCoordinates(polygons=
                    [
                    [
                    [
                        PointCoordinate(0.07, 0.02),
                        PointCoordinate(0.09, 0.03),
                        PointCoordinate(0.11, 0.02),
                        PointCoordinate(0.10, 0.01),
                        PointCoordinate(0.08, 0.01),
                    ]
                    ]
                    ]
                ),
                "blueberry_type": "Other blueberry type",
                "Specify blueberry type": "Lowbush",
            },
        ],
        104: [
            {
                "label_ref": "blueberry_016",
                "coordinates": PolygonCoordinates(polygons=
                    [
                    [
                    [
                        PointCoordinate(0.01, 0.02),
                        PointCoordinate(0.03, 0.03),
                        PointCoordinate(0.05, 0.02),
                        PointCoordinate(0.04, 0.01),
                        PointCoordinate(0.02, 0.01),
                    ]
                    ]
                    ]
                ),
                "blueberry_type": "Blueray",
                "blueray_quality_options": "Plump",
            },
            {
                "label_ref": "blueberry_014",
                "coordinates": PolygonCoordinates(polygons=
                    [
                    [
                    [
                        PointCoordinate(0.041, 0.052),
                        PointCoordinate(0.061, 0.062),
                        PointCoordinate(0.081, 0.052),
                        PointCoordinate(0.071, 0.042),
                        PointCoordinate(0.051, 0.042),
                    ]
                    ]
                    ]
                ),
                "blueberry_type": "Bluegold",
                "bluegold_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "blueberry_017",
                "coordinates": PolygonCoordinates(polygons=
                    [
                    [
                    [
                        PointCoordinate(0.07, 0.02),
                        PointCoordinate(0.09, 0.03),
                        PointCoordinate(0.11, 0.02),
                        PointCoordinate(0.10, 0.01),
                        PointCoordinate(0.08, 0.01),
                    ]
                    ]
                    ]
                ),
                "blueberry_type": "Other blueberry type",
                "Specify blueberry type": "Highbush",
            },
        ],
        105: [
            {
                "label_ref": "blueberry_016",
                "coordinates": PolygonCoordinates(polygons=
                    [
                    [
                    [
                        PointCoordinate(0.011, 0.022),
                        PointCoordinate(0.031, 0.032),
                        PointCoordinate(0.051, 0.022),
                        PointCoordinate(0.041, 0.012),
                        PointCoordinate(0.021, 0.012),
                    ]
                    ]
                    ]
                ),
                "blueberry_type": "Blueray",
                "blueray_quality_options": "Plump",
            },
            {
                "label_ref": "blueberry_014",
                "coordinates": PolygonCoordinates(polygons=
                    [
                    [
                    [
                        PointCoordinate(0.043, 0.055),
                        PointCoordinate(0.063, 0.065),
                        PointCoordinate(0.083, 0.055),
                        PointCoordinate(0.073, 0.045),
                        PointCoordinate(0.053, 0.045),
                    ]
                    ]
                    ]
                ),
                "blueberry_type": "Bluegold",
                "bluegold_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "blueberry_017",
                "coordinates": PolygonCoordinates(polygons=
                    [
                    [
                    [
                        PointCoordinate(0.071, 0.022),
                        PointCoordinate(0.091, 0.032),
                        PointCoordinate(0.111, 0.022),
                        PointCoordinate(0.101, 0.012),
                        PointCoordinate(0.081, 0.012),
                    ]
                    ]
                    ]
                ),
                "blueberry_type": "Other blueberry type",
                "Specify blueberry type": "Highbush",
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
        label_row.initialise_labels()  # Ensure this is called before adding object instances

        for frame_number, items in frame_coordinates.items():
            if not isinstance(items, list):  # Multiple objects in the frame
                items = [items]

            for item in items:
                label_ref = item["label_ref"]
                coord = item["coordinates"]
                blueberry_type = item["blueberry_type"]

                # Check if label_ref already exists for reusability
                if label_ref not in object_instances_by_label_ref:
                    polygon_object_instance: ObjectInstance = polygon_ontology_object.create_instance()
                    object_instances_by_label_ref[label_ref] = polygon_object_instance  # Store for reuse
                    checklist_attribute = None

                    # Set blueberry type attribute
                    if blueberry_type == "Bluegold":
                        polygon_object_instance.set_answer(attribute=blueberry_type_radio_attribute, answer=bluegold_option)
                        checklist_attribute = bluegold_checklist_attribute
                    elif blueberry_type == "Duke":
                        polygon_object_instance.set_answer(attribute=blueberry_type_radio_attribute, answer=duke_option)
                        checklist_attribute = duke_checklist_attribute
                    elif blueberry_type == "Blueray":
                        polygon_object_instance.set_answer(attribute=blueberry_type_radio_attribute, answer=blueray_option)
                        checklist_attribute = blueray_checklist_attribute
                    elif blueberry_type == "Other blueberry type":
                        polygon_object_instance.set_answer(
                            attribute=blueberry_type_radio_attribute, answer=other_blueberry_option
                        )
                        polygon_object_instance.set_answer(
                            attribute=other_blueberry_option_text_attribute, answer=item.get("Specify blueberry type", "")
                        )

                    # Set checklist attributes
                    checklist_answers = []
                    quality_options = item.get(f"{blueberry_type.lower()}_quality_options", "").split(", ")

                    for quality in quality_options:
                        if quality == "Plump":
                            checklist_answers.append(
                                bluegold_plump_option
                                if blueberry_type == "Bluegold"
                                else duke_plump_option
                                if blueberry_type == "Duke"
                                else blueray_plump_option
                            )
                        elif quality == "Juicy":
                            checklist_answers.append(
                                bluegold_juicy_option
                                if blueberry_type == "Bluegold"
                                else duke_juicy_option
                                if blueberry_type == "Duke"
                                else blueray_juicy_option
                            )
                        elif quality == "Large":
                            checklist_answers.append(
                                bluegold_large_option
                                if blueberry_type == "Bluegold"
                                else duke_large_option
                                if blueberry_type == "Duke"
                                else blueray_large_option
                            )

                    if checklist_attribute and checklist_answers:
                        polygon_object_instance.set_answer(
                            attribute=checklist_attribute, answer=checklist_answers, overwrite=True
                        )

                else:
                    # Reuse existing instance across frames
                    polygon_object_instance = object_instances_by_label_ref[label_ref]

                # Assign the object to the frame and track it
                polygon_object_instance.set_for_frames(coordinates=coord, frames=frame_number)

        # Add object instances to label_row **only if they have frames assigned**
        for polygon_object_instance in object_instances_by_label_ref.values():
            if polygon_object_instance.get_annotation_frames():  # Ensures it has at least one frame
                label_row.add_object_instance(polygon_object_instance)

        # Save label row using the bundle
        label_row.save(bundle=bundle)

print("Labels with blueberry type radio buttons, checklist attributes, and text labels added for all data units.")
