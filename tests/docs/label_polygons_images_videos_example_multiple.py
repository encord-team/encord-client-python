"""
Code Block Name: Multiple - Advanced
"""

# Import dependencies

from encord import EncordUserClient, Project
from encord.objects import ChecklistAttribute, Object, ObjectInstance, Option, RadioAttribute, TextAttribute
from encord.objects.coordinates import PointCoordinate, PolygonCoordinates

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

# Find polygon object for blueberries
polygon_ontology_object: Object = ontology_structure.get_child_by_title(title="Blueberries", type_=Object)
assert polygon_ontology_object is not None, "Object 'Blueberries' not found in ontology"

# Get radio attribute for blueberry type
blueberry_type_radio_attribute = ontology_structure.get_child_by_title(type_=RadioAttribute, title="Type?")
assert blueberry_type_radio_attribute is not None, "Radio attribute 'Type?' not found"

# Get radio options
bluegold_option = blueberry_type_radio_attribute.get_child_by_title(type_=Option, title="Bluegold")
assert bluegold_option is not None, "Option 'Bluegold' not found under radio attribute 'Type?'"

duke_option = blueberry_type_radio_attribute.get_child_by_title(type_=Option, title="Duke")
assert duke_option is not None, "Option 'Duke' not found under radio attribute 'Type?'"

blueray_option = blueberry_type_radio_attribute.get_child_by_title(type_=Option, title="Blueray")
assert blueray_option is not None, "Option 'Blueray' not found under radio attribute 'Type?'"

other_blueberry_option = blueberry_type_radio_attribute.get_child_by_title(type_=Option, title="Other blueberry type")
assert other_blueberry_option is not None, "Option 'Other blueberry type' not found under radio attribute 'Type?'"

# Bluegold Qualities
bluegold_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Bluegold Qualities?"
)
assert bluegold_checklist_attribute is not None, "Checklist attribute 'Bluegold Qualities?' not found"

bluegold_plump_option = bluegold_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
assert bluegold_plump_option is not None, "Option 'Plump' not found under 'Bluegold Qualities?'"

bluegold_juicy_option = bluegold_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
assert bluegold_juicy_option is not None, "Option 'Juicy' not found under 'Bluegold Qualities?'"

bluegold_large_option = bluegold_checklist_attribute.get_child_by_title(type_=Option, title="Large")
assert bluegold_large_option is not None, "Option 'Large' not found under 'Bluegold Qualities?'"

# Duke Qualities
duke_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="Duke Qualities?")
assert duke_checklist_attribute is not None, "Checklist attribute 'Duke Qualities?' not found"

duke_plump_option = duke_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
assert duke_plump_option is not None, "Option 'Plump' not found under 'Duke Qualities?'"

duke_juicy_option = duke_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
assert duke_juicy_option is not None, "Option 'Juicy' not found under 'Duke Qualities?'"

duke_large_option = duke_checklist_attribute.get_child_by_title(type_=Option, title="Large")
assert duke_large_option is not None, "Option 'Large' not found under 'Duke Qualities?'"

# Blueray Qualities
blueray_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Blueray Qualities?"
)
assert blueray_checklist_attribute is not None, "Checklist attribute 'Blueray Qualities?' not found"

blueray_plump_option = blueray_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
assert blueray_plump_option is not None, "Option 'Plump' not found under 'Blueray Qualities?'"

blueray_juicy_option = blueray_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
assert blueray_juicy_option is not None, "Option 'Juicy' not found under 'Blueray Qualities?'"

blueray_large_option = blueray_checklist_attribute.get_child_by_title(type_=Option, title="Large")
assert blueray_large_option is not None, "Option 'Large' not found under 'Blueray Qualities?'"

# Other blueberry type — text input
other_blueberry_option_text_attribute = ontology_structure.get_child_by_title(
    type_=TextAttribute, title="Specify blueberry type"
)
assert other_blueberry_option_text_attribute is not None, "Text attribute 'Specify blueberry type' not found"

# Dictionary of labels per data unit and per frame with blueberry type specified, including quality options
video_frame_labels = {
    "cherries-001.jpg": {
        0: {
            "label_ref": "blueberry_001",
            "coordinates": PolygonCoordinates(
                polygons=[
                    [
                        # Polygon
                        # First part (triangle)
                        [
                            PointCoordinate(0.1, 0.1),
                            PointCoordinate(0.3, 0.1),
                            PointCoordinate(0.2, 0.3),
                            PointCoordinate(0.1, 0.1),
                            # Close the polygon
                        ]
                    ],
                    [
                        # Second part (pentagon)
                        [
                            PointCoordinate(0.6, 0.2),
                            PointCoordinate(0.7, 0.25),
                            PointCoordinate(0.75, 0.35),
                            PointCoordinate(0.65, 0.45),
                            PointCoordinate(0.55, 0.35),
                            PointCoordinate(0.6, 0.2),
                            # Close the polygon
                        ]
                    ],
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
                "coordinates": PolygonCoordinates(
                    polygons=[
                        # Polygon 1
                        [
                            # First part
                            [
                                PointCoordinate(0.1, 0.1),
                                PointCoordinate(0.3, 0.1),
                                PointCoordinate(0.2, 0.3),
                                PointCoordinate(0.1, 0.1),
                                # Close the polygon
                            ]
                        ],
                        # Second part
                        [
                            [
                                PointCoordinate(0.5, 0.5),
                                PointCoordinate(0.7, 0.5),
                                PointCoordinate(0.6, 0.7),
                                PointCoordinate(0.5, 0.5),
                                # Close the polygon
                            ]
                        ],
                    ]
                ),
                "blueberry_type": "Duke",
                "duke_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "blueberry_003",
                "coordinates": PolygonCoordinates(
                    polygons=[
                        # Polygon 2
                        [
                            # First part
                            [
                                PointCoordinate(0.15, 0.6),
                                PointCoordinate(0.35, 0.6),
                                PointCoordinate(0.35, 0.8),
                                PointCoordinate(0.15, 0.8),
                                PointCoordinate(0.15, 0.6),
                                # Close the polygon
                            ]
                        ],
                        # Second part
                        [
                            [
                                PointCoordinate(0.55, 0.15),
                                PointCoordinate(0.75, 0.15),
                                PointCoordinate(0.75, 0.35),
                                PointCoordinate(0.55, 0.35),
                                PointCoordinate(0.55, 0.15),
                                # Close the polygon
                            ]
                        ],
                    ]
                ),
                "blueberry_type": "Blueray",
                "blueray_quality_options": "Plump",
            },
            {
                "label_ref": "blueberry_004",
                "coordinates": PolygonCoordinates(
                    polygons=[
                        # Third polygon
                        [
                            # First part
                            [
                                PointCoordinate(0.25, 0.25),
                                PointCoordinate(0.4, 0.3),
                                PointCoordinate(0.35, 0.45),
                                PointCoordinate(0.2, 0.4),
                                PointCoordinate(0.25, 0.25),
                                # Close the polygon
                            ]
                        ],
                        # Second part
                        [
                            [
                                PointCoordinate(0.65, 0.6),
                                PointCoordinate(0.8, 0.65),
                                PointCoordinate(0.75, 0.8),
                                PointCoordinate(0.6, 0.75),
                                PointCoordinate(0.65, 0.6),
                                # Close the polygon
                            ]
                        ],
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
            "coordinates": PolygonCoordinates(
                polygons=[
                    [
                        # Polygon
                        # First part (triangle)
                        [
                            PointCoordinate(0.1, 0.1),
                            PointCoordinate(0.3, 0.1),
                            PointCoordinate(0.2, 0.3),
                            PointCoordinate(0.1, 0.1),
                            # Close the ring
                        ]
                    ],
                    [
                        # Second part (pentagon)
                        [
                            PointCoordinate(0.6, 0.2),
                            PointCoordinate(0.7, 0.25),
                            PointCoordinate(0.75, 0.35),
                            PointCoordinate(0.65, 0.45),
                            PointCoordinate(0.55, 0.35),
                            PointCoordinate(0.6, 0.2),
                            # Close the ring
                        ]
                    ],
                ]
            ),
            "blueberry_type": "Bluegold",
            "bluegold_quality_options": "Plump, Juicy",
        },
        2: [
            {
                "label_ref": "blueberry_006",
                "coordinates": PolygonCoordinates(
                    polygons=[
                        # First polygon
                        [
                            # First part
                            [
                                PointCoordinate(0.05, 0.15),
                                PointCoordinate(0.20, 0.10),
                                PointCoordinate(0.25, 0.25),
                                PointCoordinate(0.10, 0.30),
                                PointCoordinate(0.05, 0.15),
                                # Close the polygon
                            ]
                        ],
                        # Second part
                        [
                            [
                                PointCoordinate(0.50, 0.20),
                                PointCoordinate(0.65, 0.25),
                                PointCoordinate(0.60, 0.40),
                                PointCoordinate(0.45, 0.35),
                                PointCoordinate(0.50, 0.20),
                                # Close the polygon
                            ]
                        ],
                    ]
                ),
                "blueberry_type": "Duke",
                "duke_quality_options": "Large",
            },
            {
                "label_ref": "blueberry_007",
                "coordinates": PolygonCoordinates(
                    polygons=[
                        # Second polygon
                        [
                            # First part
                            [
                                PointCoordinate(0.30, 0.60),
                                PointCoordinate(0.50, 0.60),
                                PointCoordinate(0.50, 0.75),
                                PointCoordinate(0.30, 0.75),
                                PointCoordinate(0.30, 0.60),
                                # Close the polygon
                            ]
                        ],
                        # Second part
                        [
                            [
                                PointCoordinate(0.65, 0.55),
                                PointCoordinate(0.85, 0.55),
                                PointCoordinate(0.85, 0.70),
                                PointCoordinate(0.65, 0.70),
                                PointCoordinate(0.65, 0.55),
                                # Close the polygon
                            ]
                        ],
                    ]
                ),
                "blueberry_type": "Blueray",
                "blueray_quality_options": "Plump",
            },
            {
                "label_ref": "blueberry_008",
                "coordinates": PolygonCoordinates(
                    polygons=[
                        # Third polygon
                        [
                            # First part
                            [
                                PointCoordinate(0.10, 0.80),
                                PointCoordinate(0.25, 0.85),
                                PointCoordinate(0.20, 0.95),
                                PointCoordinate(0.05, 0.90),
                                PointCoordinate(0.10, 0.80),
                                # Close the polygon
                            ]
                        ],
                        # Second part
                        [
                            [
                                PointCoordinate(0.55, 0.75),
                                PointCoordinate(0.70, 0.80),
                                PointCoordinate(0.65, 0.95),
                                PointCoordinate(0.50, 0.90),
                                PointCoordinate(0.55, 0.75),
                                # Close the polygon
                            ]
                        ],
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
            "coordinates": PolygonCoordinates(
                polygons=[
                    [
                        # Polygon
                        # First part (triangle)
                        [
                            PointCoordinate(0.1, 0.1),
                            PointCoordinate(0.3, 0.1),
                            PointCoordinate(0.2, 0.3),
                            PointCoordinate(0.1, 0.1),
                            # Close the ring
                        ]
                    ],
                    [
                        # Second part (pentagon)
                        [
                            PointCoordinate(0.6, 0.2),
                            PointCoordinate(0.7, 0.25),
                            PointCoordinate(0.75, 0.35),
                            PointCoordinate(0.65, 0.45),
                            PointCoordinate(0.55, 0.35),
                            PointCoordinate(0.6, 0.2),
                            # Close the ring
                        ]
                    ],
                ]
            ),
            "blueberry_type": "Bluegold",
            "bluegold_quality_options": "Plump",
        },
        3: [
            {
                "label_ref": "blueberry_010",
                "coordinates": PolygonCoordinates(
                    polygons=[
                        # First polygon
                        [
                            # First part
                            [
                                PointCoordinate(0.05, 0.15),
                                PointCoordinate(0.20, 0.10),
                                PointCoordinate(0.25, 0.25),
                                PointCoordinate(0.10, 0.30),
                                PointCoordinate(0.05, 0.15),
                                # Close the polygon
                            ]
                        ],
                        # Second part
                        [
                            [
                                PointCoordinate(0.50, 0.20),
                                PointCoordinate(0.65, 0.25),
                                PointCoordinate(0.60, 0.40),
                                PointCoordinate(0.45, 0.35),
                                PointCoordinate(0.50, 0.20),
                                # Close the polygon
                            ]
                        ],
                    ]
                ),
                "blueberry_type": "Duke",
                "duke_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "blueberry_011",
                "coordinates": PolygonCoordinates(
                    polygons=[
                        # Second polygon
                        [
                            # First part
                            [
                                PointCoordinate(0.30, 0.60),
                                PointCoordinate(0.50, 0.60),
                                PointCoordinate(0.50, 0.75),
                                PointCoordinate(0.30, 0.75),
                                PointCoordinate(0.30, 0.60),
                                # Close the polygon
                            ]
                        ],
                        # Second part
                        [
                            [
                                PointCoordinate(0.65, 0.55),
                                PointCoordinate(0.85, 0.55),
                                PointCoordinate(0.85, 0.70),
                                PointCoordinate(0.65, 0.70),
                                PointCoordinate(0.65, 0.55),
                                # Close the polygon
                            ]
                        ],
                    ]
                ),
                "blueberry_type": "Blueray",
                "blueray_quality_options": "Plump",
            },
            {
                "label_ref": "blueberry_012",
                "coordinates": PolygonCoordinates(
                    polygons=[
                        # Third polygon
                        [
                            # First part
                            [
                                PointCoordinate(0.10, 0.80),
                                PointCoordinate(0.25, 0.85),
                                PointCoordinate(0.20, 0.95),
                                PointCoordinate(0.05, 0.90),
                                PointCoordinate(0.10, 0.80),
                                # Close the polygon
                            ]
                        ],
                        # Second part
                        [
                            [
                                PointCoordinate(0.55, 0.75),
                                PointCoordinate(0.70, 0.80),
                                PointCoordinate(0.65, 0.95),
                                PointCoordinate(0.50, 0.90),
                                PointCoordinate(0.55, 0.75),
                                # Close the polygon
                            ]
                        ],
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
                "coordinates": PolygonCoordinates(
                    polygons=[
                        # First polygon
                        [
                            # First part
                            [
                                PointCoordinate(0.05, 0.35),
                                PointCoordinate(0.15, 0.33),
                                PointCoordinate(0.17, 0.43),
                                PointCoordinate(0.07, 0.45),
                                PointCoordinate(0.05, 0.35),
                                # Close the polygon
                            ]
                        ],
                        # Second part
                        [
                            [
                                PointCoordinate(0.80, 0.40),
                                PointCoordinate(0.90, 0.42),
                                PointCoordinate(0.88, 0.52),
                                PointCoordinate(0.78, 0.50),
                                PointCoordinate(0.80, 0.40),
                                # Close the polygon
                            ]
                        ],
                    ]
                ),
                "blueberry_type": "Blueray",
                "blueray_quality_options": "Plump",
            },
            {
                "label_ref": "blueberry_014",
                "coordinates": PolygonCoordinates(
                    polygons=[
                        # Second polygon
                        [
                            # First part
                            [
                                PointCoordinate(0.05, 0.05),
                                PointCoordinate(0.15, 0.05),
                                PointCoordinate(0.15, 0.10),
                                PointCoordinate(0.05, 0.10),
                                PointCoordinate(0.05, 0.05),
                                # Close the polygon
                            ]
                        ],
                        # Second part
                        [
                            [
                                PointCoordinate(0.80, 0.05),
                                PointCoordinate(0.95, 0.05),
                                PointCoordinate(0.95, 0.10),
                                PointCoordinate(0.80, 0.10),
                                PointCoordinate(0.80, 0.05),
                                # Close the polygon
                            ]
                        ],
                    ]
                ),
                "blueberry_type": "Bluegold",
                "bluegold_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "blueberry_015",
                "coordinates": PolygonCoordinates(
                    polygons=[
                        # Third polygon
                        [
                            # First part
                            [
                                PointCoordinate(0.15, 0.40),
                                PointCoordinate(0.25, 0.38),
                                PointCoordinate(0.27, 0.48),
                                PointCoordinate(0.17, 0.50),
                                PointCoordinate(0.15, 0.40),
                                # Close the polygon
                            ]
                        ],
                        # Second part
                        [
                            [
                                PointCoordinate(0.65, 0.65),
                                PointCoordinate(0.75, 0.63),
                                PointCoordinate(0.77, 0.73),
                                PointCoordinate(0.67, 0.75),
                                PointCoordinate(0.65, 0.65),
                                # Close the polygon
                            ]
                        ],
                    ]
                ),
                "blueberry_type": "Other blueberry type",
                "Specify blueberry type": "Lowbush",
            },
        ],
        104: [
            {
                "label_ref": "blueberry_016",
                "coordinates": PolygonCoordinates(
                    polygons=[
                        # Fourth polygon
                        [
                            # First part
                            [
                                PointCoordinate(0.20, 0.20),
                                PointCoordinate(0.30, 0.18),
                                PointCoordinate(0.32, 0.28),
                                PointCoordinate(0.22, 0.30),
                                PointCoordinate(0.20, 0.20),
                                # Close the polygon
                            ]
                        ],
                        # Second part
                        [
                            [
                                PointCoordinate(0.65, 0.20),
                                PointCoordinate(0.75, 0.22),
                                PointCoordinate(0.73, 0.32),
                                PointCoordinate(0.63, 0.30),
                                PointCoordinate(0.65, 0.20),
                                # Close the polygon
                            ]
                        ],
                    ]
                ),
                "blueberry_type": "Blueray",
                "blueray_quality_options": "Plump",
            },
            {
                "label_ref": "blueberry_014",
                "coordinates": PolygonCoordinates(
                    polygons=[
                        # Second polygon
                        [
                            # First part
                            [
                                PointCoordinate(0.30, 0.60),
                                PointCoordinate(0.50, 0.60),
                                PointCoordinate(0.50, 0.75),
                                PointCoordinate(0.30, 0.75),
                                PointCoordinate(0.30, 0.60),
                                # Close the polygon
                            ]
                        ],
                        # Second part
                        [
                            [
                                PointCoordinate(0.65, 0.55),
                                PointCoordinate(0.85, 0.55),
                                PointCoordinate(0.85, 0.70),
                                PointCoordinate(0.65, 0.70),
                                PointCoordinate(0.65, 0.55),
                                # Close the polygon
                            ]
                        ],
                    ]
                ),
                "blueberry_type": "Bluegold",
                "bluegold_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "blueberry_017",
                "coordinates": PolygonCoordinates(
                    polygons=[
                        # Fifth polygon
                        [
                            # First part
                            [
                                PointCoordinate(0.05, 0.05),
                                PointCoordinate(0.15, 0.05),
                                PointCoordinate(0.15, 0.10),
                                PointCoordinate(0.05, 0.10),
                                PointCoordinate(0.05, 0.05),
                                # Close the polygon
                            ]
                        ],
                        [
                            # Second part
                            [
                                PointCoordinate(0.80, 0.05),
                                PointCoordinate(0.95, 0.05),
                                PointCoordinate(0.95, 0.10),
                                PointCoordinate(0.80, 0.10),
                                PointCoordinate(0.80, 0.05),
                                # Close the polygon
                            ]
                        ],
                    ]
                ),
                "blueberry_type": "Other blueberry type",
                "Specify blueberry type": "Highbush",
            },
        ],
        105: [
            {
                "label_ref": "blueberry_016",
                "coordinates": PolygonCoordinates(
                    polygons=[
                        # Fourth polygon
                        [
                            # First part
                            [
                                PointCoordinate(0.40, 0.40),
                                PointCoordinate(0.50, 0.40),
                                PointCoordinate(0.50, 0.50),
                                PointCoordinate(0.40, 0.50),
                                PointCoordinate(0.40, 0.40),
                                # Close the polygon
                            ]
                        ],
                        # Second part
                        [
                            [
                                PointCoordinate(0.55, 0.55),
                                PointCoordinate(0.65, 0.55),
                                PointCoordinate(0.65, 0.65),
                                PointCoordinate(0.55, 0.65),
                                PointCoordinate(0.55, 0.55),
                                # Close the polygon
                            ]
                        ],
                    ]
                ),
                "blueberry_type": "Blueray",
                "blueray_quality_options": "Plump",
            },
            {
                "label_ref": "blueberry_014",
                "coordinates": PolygonCoordinates(
                    polygons=[
                        # Second polygon
                        [
                            # First part
                            [
                                PointCoordinate(0.10, 0.80),
                                PointCoordinate(0.25, 0.85),
                                PointCoordinate(0.20, 0.95),
                                PointCoordinate(0.05, 0.90),
                                PointCoordinate(0.10, 0.80),
                                # Close the polygon
                            ]
                        ],
                        # Second part
                        [
                            [
                                PointCoordinate(0.55, 0.75),
                                PointCoordinate(0.70, 0.80),
                                PointCoordinate(0.65, 0.95),
                                PointCoordinate(0.50, 0.90),
                                PointCoordinate(0.55, 0.75),
                                # Close the polygon
                            ]
                        ],
                    ]
                ),
                "blueberry_type": "Bluegold",
                "bluegold_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "blueberry_017",
                "coordinates": PolygonCoordinates(
                    polygons=[
                        # Fifth polygon
                        [
                            # First part
                            [
                                PointCoordinate(0.35, 0.05),
                                PointCoordinate(0.45, 0.05),
                                PointCoordinate(0.45, 0.15),
                                PointCoordinate(0.35, 0.15),
                                PointCoordinate(0.35, 0.05),
                                # Close the polygon
                            ]
                        ],
                        [
                            # Second part
                            [
                                PointCoordinate(0.55, 0.05),
                                PointCoordinate(0.65, 0.05),
                                PointCoordinate(0.65, 0.15),
                                PointCoordinate(0.55, 0.15),
                                PointCoordinate(0.55, 0.05),
                                # Close the polygon
                            ]
                        ],
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
    label_rows = project.list_label_rows_v2(data_title_eq=data_unit)
    assert isinstance(label_rows, list), f"Expected list of label rows for '{data_unit}', got {type(label_rows)}"
    assert label_rows, f"No label rows found for data unit: {data_unit}"

    label_row = label_rows[0]
    assert label_row is not None, f"Label row is None for {data_unit}"

    # Initialize label row using bundle
    with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
        label_row.initialise_labels()
        assert label_row.ontology_structure is not None, f"Ontology not initialized for label row: {data_unit}"

        for frame_number, items in frame_coordinates.items():
            assert isinstance(frame_number, int), f"Frame number must be int, got {type(frame_number)}"

            if not isinstance(items, list):  # Single or multiple objects in the frame
                items = [items]

            for item in items:
                label_ref = item["label_ref"]
                coord = item["coordinates"]
                blueberry_type = item["blueberry_type"]

                assert blueberry_type in {
                    "Bluegold",
                    "Duke",
                    "Blueray",
                    "Other blueberry type",
                }, f"Unexpected blueberry type '{blueberry_type}' in data unit '{data_unit}'"

                if label_ref not in object_instances_by_label_ref:
                    polygon_object_instance: ObjectInstance = polygon_ontology_object.create_instance()
                    assert polygon_object_instance is not None, f"Failed to create ObjectInstance for {label_ref}"

                    object_instances_by_label_ref[label_ref] = polygon_object_instance
                    checklist_attribute = None

                    # Set blueberry type attribute
                    if blueberry_type == "Bluegold":
                        assert bluegold_option is not None, "Missing 'bluegold_option'"
                        polygon_object_instance.set_answer(
                            attribute=blueberry_type_radio_attribute, answer=bluegold_option
                        )
                        checklist_attribute = bluegold_checklist_attribute
                    elif blueberry_type == "Duke":
                        assert duke_option is not None, "Missing 'duke_option'"
                        polygon_object_instance.set_answer(attribute=blueberry_type_radio_attribute, answer=duke_option)
                        checklist_attribute = duke_checklist_attribute
                    elif blueberry_type == "Blueray":
                        assert blueray_option is not None, "Missing 'blueray_option'"
                        polygon_object_instance.set_answer(
                            attribute=blueberry_type_radio_attribute, answer=blueray_option
                        )
                        checklist_attribute = blueray_checklist_attribute
                    elif blueberry_type == "Other blueberry type":
                        assert other_blueberry_option is not None, "Missing 'other_blueberry_option'"
                        polygon_object_instance.set_answer(
                            attribute=blueberry_type_radio_attribute, answer=other_blueberry_option
                        )
                        text_answer = item.get("Specify blueberry type", "")
                        assert isinstance(text_answer, str), "'Specify blueberry type' must be a string"
                        polygon_object_instance.set_answer(
                            attribute=other_blueberry_option_text_attribute,
                            answer=text_answer,
                        )

                    # Set checklist attributes
                    checklist_answers = []
                    quality_key = f"{blueberry_type.lower()}_quality_options"
                    quality_options = item.get(quality_key, "").split(", ")

                    for quality in quality_options:
                        option = None
                        if quality == "Plump":
                            option = (
                                bluegold_plump_option
                                if blueberry_type == "Bluegold"
                                else duke_plump_option
                                if blueberry_type == "Duke"
                                else blueray_plump_option
                                if blueberry_type == "Blueray"
                                else None
                            )
                        elif quality == "Juicy":
                            option = (
                                bluegold_juicy_option
                                if blueberry_type == "Bluegold"
                                else duke_juicy_option
                                if blueberry_type == "Duke"
                                else blueray_juicy_option
                                if blueberry_type == "Blueray"
                                else None
                            )
                        elif quality == "Large":
                            option = (
                                bluegold_large_option
                                if blueberry_type == "Bluegold"
                                else duke_large_option
                                if blueberry_type == "Duke"
                                else blueray_large_option
                                if blueberry_type == "Blueray"
                                else None
                            )

                        if option:
                            checklist_answers.append(option)
                        else:
                            assert blueberry_type == "Other blueberry type", (
                                f"Invalid quality '{quality}' for type '{blueberry_type}'"
                            )

                    if checklist_attribute and checklist_answers:
                        polygon_object_instance.set_answer(
                            attribute=checklist_attribute, answer=checklist_answers, overwrite=True
                        )

                else:
                    polygon_object_instance = object_instances_by_label_ref[label_ref]

                # Assign the object to the frame and track it
                polygon_object_instance.set_for_frames(coordinates=coord, frames=frame_number)

        # Add object instances to label_row **only if they have frames assigned**
        for polygon_object_instance in object_instances_by_label_ref.values():
            assert isinstance(polygon_object_instance, ObjectInstance), "Expected ObjectInstance type"
            if polygon_object_instance.get_annotation_frames():
                label_row.add_object_instance(polygon_object_instance)

        # Save label row using the bundle
        assert label_row is not None, "Trying to save a None label row"
        label_row.save(bundle=bundle)

print("Labels with blueberry type radio buttons, checklist attributes, and text labels added for all data units.")
