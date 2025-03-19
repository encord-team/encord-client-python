# Import dependencies
from pathlib import Path

from encord import EncordUserClient, Project
from encord.objects import ChecklistAttribute, Object, ObjectInstance, Option, RadioAttribute, TextAttribute
from encord.objects.coordinates import PointCoordinate, PolygonCoordinates

SSH_PATH = "/Users/laverne-encord/prod-sdk-ssh-key-private-key.txt"
# SSH_PATH = get_ssh_key() # replace it with ssh key
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
    "blueberries-001.jpg": {
        0: {
            "label_ref": "blueberry_001",
            "coordinates": PolygonCoordinates(polygons=
                [
                # Donut + inner polygon
                [
                # Outer ring
                [
                PointCoordinate(0.10, 0.10),
                PointCoordinate(0.22, 0.09),
                PointCoordinate(0.21, 0.22),
                PointCoordinate(0.09, 0.21),
                PointCoordinate(0.10, 0.10)
                ],
                # Inner ring
                [
                PointCoordinate(0.13, 0.13),
                PointCoordinate(0.13, 0.18),
                PointCoordinate(0.18, 0.18),
                PointCoordinate(0.18, 0.13),
                PointCoordinate(0.13, 0.13)
                ]
                ],
                # Shape inside the hole
                [
                [
                PointCoordinate(0.145, 0.145),
                PointCoordinate(0.165, 0.150),
                PointCoordinate(0.160, 0.165),
                PointCoordinate(0.145, 0.145)
                ]
                ]
                ]
            ),
            "blueberry_type": "Bluegold",
            "bluegold_quality_options": "Plump, Juicy",
        }
    },
    "blueberries-010.jpg": {
        0: [
            {
                "label_ref": "blueberry_002",
                "coordinates": PolygonCoordinates(polygons=
                [
                # First donut + inner polygon
                [
                # Outer ring
                [
                PointCoordinate(0.10, 0.10),
                PointCoordinate(0.22, 0.09),
                PointCoordinate(0.21, 0.22),
                PointCoordinate(0.09, 0.21),
                PointCoordinate(0.10, 0.10)
                ],
                # Inner ring
                [
                PointCoordinate(0.13, 0.13),
                PointCoordinate(0.13, 0.18),
                PointCoordinate(0.18, 0.18),
                PointCoordinate(0.18, 0.13),
                PointCoordinate(0.13, 0.13)
                ]
                ],
                # Shape inside the hole
                [
                [
                PointCoordinate(0.145, 0.145),
                PointCoordinate(0.165, 0.150),
                PointCoordinate(0.160, 0.165),
                PointCoordinate(0.145, 0.145)
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
                # Second donut + inner polygon
                [
                # Outer ring
                [
                PointCoordinate(0.30, 0.10),
                PointCoordinate(0.42, 0.11),
                PointCoordinate(0.41, 0.22),
                PointCoordinate(0.29, 0.21),
                PointCoordinate(0.30, 0.10)
                ],
                # Inner ring
                [
                PointCoordinate(0.33, 0.13),
                PointCoordinate(0.33, 0.18),
                PointCoordinate(0.38, 0.18),
                PointCoordinate(0.38, 0.13),
                PointCoordinate(0.33, 0.13)
                ]
                ],
                # Shape inside the hole
                [
                [
                PointCoordinate(0.345, 0.145),
                PointCoordinate(0.355, 0.155),
                PointCoordinate(0.350, 0.165),
                PointCoordinate(0.340, 0.160),
                PointCoordinate(0.345, 0.145)
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
                # Third donut + inner polygon
                [
                # Outer ring
                [
                PointCoordinate(0.10, 0.30),
                PointCoordinate(0.22, 0.29),
                PointCoordinate(0.21, 0.42),
                PointCoordinate(0.09, 0.41),
                PointCoordinate(0.10, 0.30)
                ],
                # Inner ring
                [
                PointCoordinate(0.13, 0.33),
                PointCoordinate(0.13, 0.38),
                PointCoordinate(0.18, 0.38),
                PointCoordinate(0.18, 0.33),
                PointCoordinate(0.13, 0.33)
                ]
                ],
                # Shape inside the hole
                [
                [
                PointCoordinate(0.145, 0.345),
                PointCoordinate(0.155, 0.355),
                PointCoordinate(0.150, 0.370),
                PointCoordinate(0.140, 0.360),
                PointCoordinate(0.145, 0.345)
                ]
                ]
                ]
            ),
                "blueberry_type": "Other blueberry type",
                "Specify blueberry type": "Highbush",
            },
        ],
    },
    "blueberries-ig": {
        0: {
            "label_ref": "blueberry_005",
            "coordinates": PolygonCoordinates(polygons=
                [
                # Donut + inner polygon
                [
                # Outer ring
                [
                PointCoordinate(0.10, 0.10),
                PointCoordinate(0.22, 0.09),
                PointCoordinate(0.21, 0.22),
                PointCoordinate(0.09, 0.21),
                PointCoordinate(0.10, 0.10)
                ],
                # Inner ring
                [
                PointCoordinate(0.13, 0.13),
                PointCoordinate(0.13, 0.18),
                PointCoordinate(0.18, 0.18),
                PointCoordinate(0.18, 0.13),
                PointCoordinate(0.13, 0.13)
                ]
                ],
                # Shape inside the hole
                [
                [
                PointCoordinate(0.145, 0.145),
                PointCoordinate(0.165, 0.150),
                PointCoordinate(0.160, 0.165),
                PointCoordinate(0.145, 0.145)
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
                # First donut + inner polygon
                [
                # Outer ring
                [
                PointCoordinate(0.10, 0.10),
                PointCoordinate(0.22, 0.09),
                PointCoordinate(0.21, 0.22),
                PointCoordinate(0.09, 0.21),
                PointCoordinate(0.10, 0.10)
                ],
                # Inner ring
                [
                PointCoordinate(0.13, 0.13),
                PointCoordinate(0.13, 0.18),
                PointCoordinate(0.18, 0.18),
                PointCoordinate(0.18, 0.13),
                PointCoordinate(0.13, 0.13)
                ]
                ],
                # Shape inside the hole
                [
                [
                PointCoordinate(0.145, 0.145),
                PointCoordinate(0.165, 0.150),
                PointCoordinate(0.160, 0.165),
                PointCoordinate(0.145, 0.145)
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
                # Second donut + inner polygon
                [
                # Outer ring
                [
                PointCoordinate(0.30, 0.10),
                PointCoordinate(0.42, 0.11),
                PointCoordinate(0.41, 0.22),
                PointCoordinate(0.29, 0.21),
                PointCoordinate(0.30, 0.10)
                ],
                # Inner ring
                [
                PointCoordinate(0.33, 0.13),
                PointCoordinate(0.33, 0.18),
                PointCoordinate(0.38, 0.18),
                PointCoordinate(0.38, 0.13),
                PointCoordinate(0.33, 0.13)
                ]
                ],
                # Shape inside the hole
                [
                [
                PointCoordinate(0.345, 0.145),
                PointCoordinate(0.355, 0.155),
                PointCoordinate(0.350, 0.165),
                PointCoordinate(0.340, 0.160),
                PointCoordinate(0.345, 0.145)
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
                # Third donut + inner polygon
                [
                # Outer ring
                [
                PointCoordinate(0.10, 0.30),
                PointCoordinate(0.22, 0.29),
                PointCoordinate(0.21, 0.42),
                PointCoordinate(0.09, 0.41),
                PointCoordinate(0.10, 0.30)
                ],
                # Inner ring
                [
                PointCoordinate(0.13, 0.33),
                PointCoordinate(0.13, 0.38),
                PointCoordinate(0.18, 0.38),
                PointCoordinate(0.18, 0.33),
                PointCoordinate(0.13, 0.33)
                ]
                ],
                # Shape inside the hole
                [
                [
                PointCoordinate(0.145, 0.345),
                PointCoordinate(0.155, 0.355),
                PointCoordinate(0.150, 0.370),
                PointCoordinate(0.140, 0.360),
                PointCoordinate(0.145, 0.345)
                ]
                ]
                ]
            ),
                "blueberry_type": "Other blueberry type",
                "Specify blueberry type": "Lowbush",
            },
        ],
    },
    "blueberries-is": {
        0: {
            "label_ref": "blueberry_009",
            "coordinates": PolygonCoordinates(polygons=
                [
                # Donut + inner polygon
                [
                # Outer ring
                [
                PointCoordinate(0.10, 0.10),
                PointCoordinate(0.22, 0.09),
                PointCoordinate(0.21, 0.22),
                PointCoordinate(0.09, 0.21),
                PointCoordinate(0.10, 0.10)
                ],
                # Inner ring
                [
                PointCoordinate(0.13, 0.13),
                PointCoordinate(0.13, 0.18),
                PointCoordinate(0.18, 0.18),
                PointCoordinate(0.18, 0.13),
                PointCoordinate(0.13, 0.13)
                ]
                ],
                # Shape inside the hole
                [
                [
                PointCoordinate(0.145, 0.145),
                PointCoordinate(0.165, 0.150),
                PointCoordinate(0.160, 0.165),
                PointCoordinate(0.145, 0.145)
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
                # First donut + inner polygon
                [
                # Outer ring
                [
                PointCoordinate(0.10, 0.10),
                PointCoordinate(0.22, 0.09),
                PointCoordinate(0.21, 0.22),
                PointCoordinate(0.09, 0.21),
                PointCoordinate(0.10, 0.10)
                ],
                # Inner ring
                [
                PointCoordinate(0.13, 0.13),
                PointCoordinate(0.13, 0.18),
                PointCoordinate(0.18, 0.18),
                PointCoordinate(0.18, 0.13),
                PointCoordinate(0.13, 0.13)
                ]
                ],
                # Shape inside the hole
                [
                [
                PointCoordinate(0.145, 0.145),
                PointCoordinate(0.165, 0.150),
                PointCoordinate(0.160, 0.165),
                PointCoordinate(0.145, 0.145)
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
                # Second donut + inner polygon
                [
                # Outer ring
                [
                PointCoordinate(0.30, 0.10),
                PointCoordinate(0.42, 0.11),
                PointCoordinate(0.41, 0.22),
                PointCoordinate(0.29, 0.21),
                PointCoordinate(0.30, 0.10)
                ],
                # Inner ring
                [
                PointCoordinate(0.33, 0.13),
                PointCoordinate(0.33, 0.18),
                PointCoordinate(0.38, 0.18),
                PointCoordinate(0.38, 0.13),
                PointCoordinate(0.33, 0.13)
                ]
                ],
                # Shape inside the hole
                [
                [
                PointCoordinate(0.345, 0.145),
                PointCoordinate(0.355, 0.155),
                PointCoordinate(0.350, 0.165),
                PointCoordinate(0.340, 0.160),
                PointCoordinate(0.345, 0.145)
                ]
                ]
                ]
            ),
                "blueberry_type": "Blueray",
                "blueray_quality_options": "Plump",
            },
            {
                "label_ref": "blueberry_012",
                "coordinates": PolygonCoordinates(polygons=
                [
                # Third donut + inner polygon
                [
                # Outer ring
                [
                PointCoordinate(0.10, 0.30),
                PointCoordinate(0.22, 0.29),
                PointCoordinate(0.21, 0.42),
                PointCoordinate(0.09, 0.41),
                PointCoordinate(0.10, 0.30)
                ],
                # Inner ring
                [
                PointCoordinate(0.13, 0.33),
                PointCoordinate(0.13, 0.38),
                PointCoordinate(0.18, 0.38),
                PointCoordinate(0.18, 0.33),
                PointCoordinate(0.13, 0.33)
                ]
                ],
                # Shape inside the hole
                [
                [
                PointCoordinate(0.145, 0.345),
                PointCoordinate(0.155, 0.355),
                PointCoordinate(0.150, 0.370),
                PointCoordinate(0.140, 0.360),
                PointCoordinate(0.145, 0.345)
                ]
                ]
                ]
            ),
                "blueberry_type": "Other blueberry type",
                "Specify blueberry type": "Highbush",
            },
        ],
    },
    "blueberries-vid-001.mp4": {
        103: [
            {
                "label_ref": "blueberry_013",
                "coordinates": PolygonCoordinates(polygons=
                [
                # First donut + inner polygon
                [
                # Outer ring
                [
                PointCoordinate(0.10, 0.10),
                PointCoordinate(0.22, 0.09),
                PointCoordinate(0.21, 0.22),
                PointCoordinate(0.09, 0.21),
                PointCoordinate(0.10, 0.10)
                ],
                # Inner ring
                [
                PointCoordinate(0.13, 0.13),
                PointCoordinate(0.13, 0.18),
                PointCoordinate(0.18, 0.18),
                PointCoordinate(0.18, 0.13),
                PointCoordinate(0.13, 0.13)
                ]
                ],
                # Shape inside the hole
                [
                [
                PointCoordinate(0.145, 0.145),
                PointCoordinate(0.165, 0.150),
                PointCoordinate(0.160, 0.165),
                PointCoordinate(0.145, 0.145)
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
                # Second donut + inner polygon
                [
                # Outer ring
                [
                PointCoordinate(0.30, 0.10),
                PointCoordinate(0.42, 0.11),
                PointCoordinate(0.41, 0.22),
                PointCoordinate(0.29, 0.21),
                PointCoordinate(0.30, 0.10)
                ],
                # Inner ring
                [
                PointCoordinate(0.33, 0.13),
                PointCoordinate(0.33, 0.18),
                PointCoordinate(0.38, 0.18),
                PointCoordinate(0.38, 0.13),
                PointCoordinate(0.33, 0.13)
                ]
                ],
                # Shape inside the hole
                [
                [
                PointCoordinate(0.345, 0.145),
                PointCoordinate(0.355, 0.155),
                PointCoordinate(0.350, 0.165),
                PointCoordinate(0.340, 0.160),
                PointCoordinate(0.345, 0.145)
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
                # Third donut + inner polygon
                [
                # Outer ring
                [
                PointCoordinate(0.10, 0.30),
                PointCoordinate(0.22, 0.29),
                PointCoordinate(0.21, 0.42),
                PointCoordinate(0.09, 0.41),
                PointCoordinate(0.10, 0.30)
                ],
                # Inner ring
                [
                PointCoordinate(0.13, 0.33),
                PointCoordinate(0.13, 0.38),
                PointCoordinate(0.18, 0.38),
                PointCoordinate(0.18, 0.33),
                PointCoordinate(0.13, 0.33)
                ]
                ],
                # Shape inside the hole
                [
                [
                PointCoordinate(0.145, 0.345),
                PointCoordinate(0.155, 0.355),
                PointCoordinate(0.150, 0.370),
                PointCoordinate(0.140, 0.360),
                PointCoordinate(0.145, 0.345)
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
                # Fourth donut + inner polygon
                [
                # Outer ring
                [
                PointCoordinate(0.30, 0.30),
                PointCoordinate(0.42, 0.31),
                PointCoordinate(0.41, 0.42),
                PointCoordinate(0.29, 0.41),
                PointCoordinate(0.30, 0.30)
                ],
                # Inner ring
                [
                PointCoordinate(0.33, 0.33),
                PointCoordinate(0.33, 0.38),
                PointCoordinate(0.38, 0.38),
                PointCoordinate(0.38, 0.33),
                PointCoordinate(0.33, 0.33)
                ]
                ],
                # Shape inside the hole
                [
                [
                PointCoordinate(0.345, 0.345),
                PointCoordinate(0.360, 0.350),
                PointCoordinate(0.355, 0.365),
                PointCoordinate(0.345, 0.345)
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
                # Second donut + inner polygon
                [
                # Outer ring
                [
                PointCoordinate(0.31, 0.10),
                PointCoordinate(0.45, 0.12),
                PointCoordinate(0.43, 0.25),
                PointCoordinate(0.30, 0.22),
                PointCoordinate(0.31, 0.10)
                ],
                # Inner ring
                [
                PointCoordinate(0.34, 0.14),
                PointCoordinate(0.34, 0.19),
                PointCoordinate(0.39, 0.20),
                PointCoordinate(0.40, 0.15),
                PointCoordinate(0.34, 0.14)
                ]
                ],
                # Shape inside the hole
                [
                [
                PointCoordinate(0.355, 0.155),
                PointCoordinate(0.370, 0.160),
                PointCoordinate(0.365, 0.175),
                PointCoordinate(0.350, 0.170),
                PointCoordinate(0.355, 0.155)
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
                # Fifth donut + inner polygon
                [
                # Outer ring
                [
                PointCoordinate(0.50, 0.10),
                PointCoordinate(0.62, 0.12),
                PointCoordinate(0.61, 0.22),
                PointCoordinate(0.49, 0.21),
                PointCoordinate(0.50, 0.10)
                ],
                # Inner ring
                [
                PointCoordinate(0.53, 0.13),
                PointCoordinate(0.53, 0.18),
                PointCoordinate(0.58, 0.18),
                PointCoordinate(0.58, 0.13),
                PointCoordinate(0.53, 0.13)
                ]
                ],
                # Shape inside the hole
                [
                [
                PointCoordinate(0.545, 0.145),
                PointCoordinate(0.560, 0.150),
                PointCoordinate(0.555, 0.165),
                PointCoordinate(0.540, 0.160),
                PointCoordinate(0.545, 0.145)
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
                # Fourth donut + inner polygon
                [
                # Outer ring
                [
                PointCoordinate(0.33, 0.33),
                PointCoordinate(0.47, 0.34),
                PointCoordinate(0.45, 0.46),
                PointCoordinate(0.31, 0.45),
                PointCoordinate(0.33, 0.33)
                ],
                # Inner ring
                [
                PointCoordinate(0.36, 0.36),
                PointCoordinate(0.37, 0.41),
                PointCoordinate(0.42, 0.42),
                PointCoordinate(0.43, 0.37),
                PointCoordinate(0.36, 0.36)
                ]
                ],
                # Shape inside the hole
                [
                [
                PointCoordinate(0.375, 0.375),
                PointCoordinate(0.395, 0.380),
                PointCoordinate(0.390, 0.395),
                PointCoordinate(0.370, 0.390),
                PointCoordinate(0.375, 0.375)
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
                # Second donut + inner polygon
                [
                # Outer ring
                [
                PointCoordinate(0.33, 0.12),
                PointCoordinate(0.46, 0.13),
                PointCoordinate(0.44, 0.26),
                PointCoordinate(0.31, 0.25),
                PointCoordinate(0.33, 0.12)
                ],
                # Inner ring
                [
                PointCoordinate(0.36, 0.16),
                PointCoordinate(0.37, 0.21),
                PointCoordinate(0.41, 0.22),
                PointCoordinate(0.42, 0.17),
                PointCoordinate(0.36, 0.16)
                ]
                ],
                # Shape inside the hole
                [
                [
                PointCoordinate(0.375, 0.175),
                PointCoordinate(0.390, 0.180),
                PointCoordinate(0.385, 0.195),
                PointCoordinate(0.370, 0.190),
                PointCoordinate(0.375, 0.175)
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
                # Fifth donut + inner polygon
                [
                # Outer ring
                [
                PointCoordinate(0.53, 0.13),
                PointCoordinate(0.67, 0.14),
                PointCoordinate(0.66, 0.26),
                PointCoordinate(0.52, 0.25),
                PointCoordinate(0.53, 0.13)
                ],
                # Inner ring
                [
                PointCoordinate(0.56, 0.16),
                PointCoordinate(0.57, 0.21),
                PointCoordinate(0.62, 0.22),
                PointCoordinate(0.63, 0.17),
                PointCoordinate(0.56, 0.16)
                ]
                ],
                # Shape inside the hole
                [
                [
                PointCoordinate(0.575, 0.175),
                PointCoordinate(0.595, 0.180),
                PointCoordinate(0.590, 0.195),
                PointCoordinate(0.570, 0.190),
                PointCoordinate(0.575, 0.175)
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
            blueberry_type = item["blueberry_type"]

            #  Check if label_ref already exists for reusability
            if label_ref not in object_instances_by_label_ref:
                polygon_object_instance: ObjectInstance = polygon_ontology_object.create_instance()
                object_instances_by_label_ref[label_ref] = polygon_object_instance  #  Store for reuse
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
                #  Reuse existing instance across frames
                polygon_object_instance = object_instances_by_label_ref[label_ref]

            #  Assign the object to the frame and track it
            polygon_object_instance.set_for_frames(coordinates=coord, frames=frame_number)

    #  Add object instances to label_row **only if they have frames assigned**
    for polygon_object_instance in object_instances_by_label_ref.values():
        if polygon_object_instance.get_annotation_frames():  #  Ensures it has at least one frame
            label_row.add_object_instance(polygon_object_instance)

    #  Upload all labels for this data unit (video/image) to the server
    label_row.save()

print(" Labels with blueberry type radio buttons, checklist attributes, and text labels added for all data units.")