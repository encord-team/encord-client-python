"""
Code Block Name: Polylines PCD
"""

# Import dependencies

from encord import EncordUserClient, Project
from encord.objects import (
    ChecklistAttribute,
    Object,
    ObjectInstance,
    Option,
    RadioAttribute,
    TextAttribute,
)
from encord.objects.coordinates import PointCoordinate3D, PolylineCoordinates

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"  # Replace with the file path to your SSH private key
PROJECT_ID = "00000000-0000-0000-0000-000000000000"  # Replace with the unique ID for the Project
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

# Get polyline object for Object of Interest
polyline_ontology_object: Object = ontology_structure.get_child_by_title(title="Object of Interest", type_=Object)
assert polyline_ontology_object is not None, "Polyline object 'Object of Interest' not found in ontology"

# Get radio attribute for Object of Interest type
ooi_type_radio_attribute = ontology_structure.get_child_by_title(type_=RadioAttribute, title="Type?")
assert ooi_type_radio_attribute is not None, "Radio attribute 'Type?' not found in ontology"

# Get radio options
curb_option = ooi_type_radio_attribute.get_child_by_title(type_=Option, title="Curb")
assert curb_option is not None, "Option 'Curb' not found under radio attribute 'Type?'"

lane_divider_option = ooi_type_radio_attribute.get_child_by_title(type_=Option, title="Lane divider")
assert lane_divider_option is not None, "Option 'Lane divider' not found under radio attribute 'Type?'"

zebra_crossing_option = ooi_type_radio_attribute.get_child_by_title(type_=Option, title="Zebra crossing")
assert zebra_crossing_option is not None, "Option 'Zebra crossing' not found under radio attribute 'Type?'"

other_ooi_option = ooi_type_radio_attribute.get_child_by_title(type_=Option, title="Other")
assert other_ooi_option is not None, "Option 'Other' not found under radio attribute 'Type?'"

# Curb Qualities
curb_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="Qualities?")
assert curb_checklist_attribute is not None, "Checklist attribute 'Qualities?' not found"

curb_good_quality_option = curb_checklist_attribute.get_child_by_title(type_=Option, title="Good quality")
assert curb_good_quality_option is not None, "Option 'Good quality' not found under 'Qualities?'"

curb_well_lit_option = curb_checklist_attribute.get_child_by_title(type_=Option, title="Well lit")
assert curb_well_lit_option is not None, "Option 'Well lit' not found under 'Qualities?'"

curb_fully_visible_option = curb_checklist_attribute.get_child_by_title(type_=Option, title="Fully visible")
assert curb_fully_visible_option is not None, "Option 'Fully visible' not found under 'Curb Qualities?'"

# Lane divider Qualities
lane_divider_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Lane divider Qualities?"
)
assert lane_divider_checklist_attribute is not None, "Checklist attribute 'Lane divider Qualities?' not found"

lane_divider_good_quality_option = lane_divider_checklist_attribute.get_child_by_title(
    type_=Option, title="Good quality"
)
assert lane_divider_good_quality_option is not None, "Option 'Good quality' not found under 'Lane divider Qualities?'"

lane_divider_well_lit_option = lane_divider_checklist_attribute.get_child_by_title(type_=Option, title="Well lit")
assert lane_divider_well_lit_option is not None, "Option 'Well lit' not found under 'Lane divider Qualities?'"

lane_divider_fully_visible_option = lane_divider_checklist_attribute.get_child_by_title(
    type_=Option, title="Fully visible"
)
assert lane_divider_fully_visible_option is not None, "Option 'Fully visible' not found under 'Lane divider Qualities?'"

# Zebra crossing Qualities
zebra_crossing_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Zebra crossing Qualities?"
)
assert zebra_crossing_checklist_attribute is not None, "Checklist attribute 'Zebra crossing Qualities?' not found"

zebra_crossing_good_quality_option = zebra_crossing_checklist_attribute.get_child_by_title(
    type_=Option, title="Good quality"
)
assert zebra_crossing_good_quality_option is not None, (
    "Option 'Good quality' not found under 'Zebra crossing Qualities?'"
)

zebra_crossing_well_lit_option = zebra_crossing_checklist_attribute.get_child_by_title(type_=Option, title="Well lit")
assert zebra_crossing_well_lit_option is not None, "Option 'Well lit' not found under 'Zebra crossing Qualities?'"

zebra_crossing_fully_visible_option = zebra_crossing_checklist_attribute.get_child_by_title(
    type_=Option, title="Fully visible"
)
assert zebra_crossing_fully_visible_option is not None, (
    "Option 'Fully visible' not found under 'Zebra crossing Qualities?'"
)

# Other text attribute
other_ooi_option_text_attribute = ontology_structure.get_child_by_title(type_=TextAttribute, title="Specify type")
assert other_ooi_option_text_attribute is not None, "Text attribute 'Specify type' not found"

# Dictionary of labels per data unit and per frame with type specified, including quality options
pcd_labels = {
    "scene-1094": {
        0: {
            "label_ref": "ooi_001",
            "coordinates": PolylineCoordinates(
                [
                    PointCoordinate3D(2.013, 2.02, 2.015),
                    PointCoordinate3D(3.033, 3.033, 3.033),
                    PointCoordinate3D(4.053, 4.023, 4.017),
                    PointCoordinate3D(0.043, 0.013, 0.043),
                ]
            ),
            "ooi_type": "Curb",
            "curb_quality_options": "Good quality, Well lit",
        }
    },
    "scene-0916": {
        0: [
            {
                "label_ref": "ooi_002",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate3D(3.000, 2.300, 0.000),
                        PointCoordinate3D(3.300, 3.300, 0.000),
                        PointCoordinate3D(5.300, 3.300, 0.000),
                        PointCoordinate3D(4.300, 1.300, 0.000),
                    ]
                ),
                "ooi_type": "Lane divider",
                "lane_divider_quality_options": "Good quality, Well lit, Fully visible",
            },
            {
                "label_ref": "ooi_003",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate3D(4.300, 5.300, 0.000),
                        PointCoordinate3D(6.300, 6.300, 0.000),
                        PointCoordinate3D(8.300, 5.300, 0.000),
                        PointCoordinate3D(7.300, 4.300, 0.000),
                    ]
                ),
                "ooi_type": "Zebra crossing",
                "zebra_crossing_quality_options": "Good quality",
            },
            {
                "label_ref": "ooi_004",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate3D(7.300, 2.300, 0.000),
                        PointCoordinate3D(9.300, 3.300, 0.000),
                        PointCoordinate3D(11.300, 2.300, 0.000),
                        PointCoordinate3D(10.300, 1.300, 0.000),
                    ]
                ),
                "ooi_type": "Other",
                "Type": "Cane",
            },
        ],
    },
    "scene-0796": {
        0: {
            "label_ref": "ooi_005",
            "coordinates": PolylineCoordinates(
                [
                    PointCoordinate3D(1.300, 2.300, 0.000),
                    PointCoordinate3D(3.300, 3.300, 0.000),
                    PointCoordinate3D(5.300, 2.300, 0.000),
                    PointCoordinate3D(4.300, 1.300, 0.000),
                ]
            ),
            "ooi_type": "Curb",
            "curb_quality_options": "Good quality, Well lit",
        },
        2: [
            {
                "label_ref": "ooi_006",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate3D(1.300, 2.300, 0.000),
                        PointCoordinate3D(3.300, 3.300, 0.000),
                        PointCoordinate3D(5.300, 2.300, 0.000),
                        PointCoordinate3D(4.300, 1.300, 0.000),
                    ]
                ),
                "ooi_type": "Lane divider",
                "lane_divider_quality_options": "Fully visible",
            },
            {
                "label_ref": "ooi_007",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate3D(4.300, 5.300, 0.000),
                        PointCoordinate3D(6.300, 6.300, 0.000),
                        PointCoordinate3D(8.300, 5.300, 0.000),
                        PointCoordinate3D(7.300, 4.300, 0.000),
                    ]
                ),
                "ooi_type": "Zebra crossing",
                "zebra_crossing_quality_options": "Good quality",
            },
            {
                "label_ref": "ooi_008",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate3D(7.300, 2.300, 0.000),
                        PointCoordinate3D(9.300, 3.300, 0.000),
                        PointCoordinate3D(11.300, 2.300, 0.000),
                        PointCoordinate3D(10.300, 1.300, 0.000),
                    ]
                ),
                "ooi_type": "Other",
                "Type": "Cane",
            },
        ],
    },
    "scene-1100": {
        0: {
            "label_ref": "ooi_009",
            "coordinates": PolylineCoordinates(
                [
                    PointCoordinate3D(1.300, 2.300, 0.000),
                    PointCoordinate3D(3.300, 3.300, 0.000),
                    PointCoordinate3D(5.300, 2.300, 0.000),
                    PointCoordinate3D(4.300, 1.300, 0.000),
                ]
            ),
            "ooi_type": "Curb",
            "curb_quality_options": "Good quality",
        },
        3: [
            {
                "label_ref": "ooi_010",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate3D(1.300, 2.300, 0.000),
                        PointCoordinate3D(3.300, 3.300, 0.000),
                        PointCoordinate3D(5.300, 2.300, 0.000),
                        PointCoordinate3D(4.300, 1.300, 0.000),
                    ]
                ),
                "ooi_type": "Lane divider",
                "lane_divider_quality_options": "Good quality, Well lit, Fully visible",
            },
            {
                "label_ref": "ooi_011",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate3D(4.300, 5.300, 0.000),
                        PointCoordinate3D(6.300, 6.300, 0.000),
                        PointCoordinate3D(8.300, 5.300, 0.000),
                        PointCoordinate3D(7.300, 4.300, 0.000),
                    ]
                ),
                "ooi_type": "Zebra crossing",
                "zebra_crossing_quality_options": "Good quality",
            },
            {
                "label_ref": "ooi_012",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate3D(7.300, 2.300, 0.000),
                        PointCoordinate3D(9.300, 3.300, 0.000),
                        PointCoordinate3D(11.300, 2.300, 0.000),
                        PointCoordinate3D(10.300, 1.300, 0.000),
                    ]
                ),
                "ooi_type": "Other",
                "Type": "Cane",
            },
        ],
    },
    "scene-0655": {
        103: [
            {
                "label_ref": "ooi_013",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate3D(1.300, 2.300, 0.000),
                        PointCoordinate3D(3.300, 3.300, 0.000),
                        PointCoordinate3D(5.300, 2.300, 0.000),
                        PointCoordinate3D(4.300, 1.300, 0.000),
                    ]
                ),
                "ooi_type": "Zebra crossing",
                "zebra_crossing_quality_options": "Good quality",
            },
            {
                "label_ref": "ooi_014",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate3D(4.300, 5.300, 0.000),
                        PointCoordinate3D(6.300, 6.300, 0.000),
                        PointCoordinate3D(8.300, 5.300, 0.000),
                        PointCoordinate3D(7.300, 4.300, 0.000),
                    ]
                ),
                "ooi_type": "Curb",
                "curb_quality_options": "Good quality, Well lit, Fully visible",
            },
            {
                "label_ref": "ooi_015",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate3D(7.300, 2.300, 0.000),
                        PointCoordinate3D(9.300, 3.300, 0.000),
                        PointCoordinate3D(11.300, 2.300, 0.000),
                        PointCoordinate3D(10.300, 1.300, 0.000),
                    ]
                ),
                "ooi_type": "Other",
                "Type": "Cane",
            },
        ],
        104: [
            {
                "label_ref": "ooi_016",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate3D(1.300, 2.300, 0.000),
                        PointCoordinate3D(3.300, 3.300, 0.000),
                        PointCoordinate3D(5.300, 2.300, 0.000),
                        PointCoordinate3D(4.300, 1.300, 0.000),
                    ]
                ),
                "ooi_type": "Zebra crossing",
                "zebra_crossing_quality_options": "Good quality",
            },
            {
                "label_ref": "ooi_014",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate3D(4.130, 5.230, 0.000),
                        PointCoordinate3D(6.130, 6.230, 0.000),
                        PointCoordinate3D(8.130, 5.230, 0.000),
                        PointCoordinate3D(7.130, 4.230, 0.000),
                    ]
                ),
                "ooi_type": "Curb",
                "curb_quality_options": "Good quality, Well lit, Fully visible",
            },
            {
                "label_ref": "ooi_017",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate3D(7.300, 2.300, 0.000),
                        PointCoordinate3D(9.300, 3.300, 0.000),
                        PointCoordinate3D(11.300, 2.300, 0.000),
                        PointCoordinate3D(10.300, 1.300, 0.000),
                    ]
                ),
                "ooi_type": "Other",
                "Type": "Cane",
            },
        ],
        105: [
            {
                "label_ref": "ooi_016",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate3D(1.130, 2.230, 0.000),
                        PointCoordinate3D(3.130, 3.230, 0.000),
                        PointCoordinate3D(5.130, 2.230, 0.000),
                        PointCoordinate3D(4.130, 1.230, 0.000),
                    ]
                ),
                "ooi_type": "Zebra crossing",
                "zebra_crossing_quality_options": "Good quality",
            },
            {
                "label_ref": "ooi_014",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate3D(4.330, 5.530, 0.000),
                        PointCoordinate3D(6.330, 6.530, 0.000),
                        PointCoordinate3D(8.330, 5.530, 0.000),
                        PointCoordinate3D(7.330, 4.530, 0.000),
                    ]
                ),
                "ooi_type": "Curb",
                "curb_quality_options": "Good quality, Well lit, Fully visible",
            },
            {
                "label_ref": "ooi_017",
                "coordinates": PolylineCoordinates(
                    [
                        PointCoordinate3D(7.130, 2.230, 0.000),
                        PointCoordinate3D(9.130, 3.230, 0.000),
                        PointCoordinate3D(11.130, 2.230, 0.000),
                        PointCoordinate3D(10.130, 1.230, 0.000),
                    ]
                ),
                "ooi_type": "Other",
                "Type": "Cane",
            },
        ],
    },
}

# Cache label rows after initialization
label_row_map = {}

# Step 1: Initialize all label rows using a bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for data_unit in pcd_labels.keys():
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

for data_unit, frame_coordinates in pcd_labels.items():
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
            ooi_type = item["ooi_type"]

            assert ooi_type in {
                "Curb",
                "Lane divider",
                "Zebra crossing",
                "Other",
            }, f"Unexpected type '{ooi_type}' in {data_unit}"

            if label_ref not in object_instances_by_label_ref:
                polyline_object_instance: ObjectInstance = polyline_ontology_object.create_instance()
                assert polyline_object_instance is not None, "Failed to create ObjectInstance"
                checklist_attribute = None
                quality_options = []

                # Assign radio and checklist attributes based on the type
                if ooi_type == "Curb":
                    assert curb_option is not None, "Missing 'curb_option'"
                    polyline_object_instance.set_answer(attribute=ooi_type_radio_attribute, answer=curb_option)
                    checklist_attribute = curb_checklist_attribute
                    quality_options = [q.strip() for q in item.get("curb_quality_options", "").split(",") if q.strip()]
                elif ooi_type == "Lane divider":
                    assert lane_divider_option is not None, "Missing 'lane_divider_option'"
                    polyline_object_instance.set_answer(attribute=ooi_type_radio_attribute, answer=lane_divider_option)
                    checklist_attribute = lane_divider_checklist_attribute
                    quality_options = [
                        q.strip() for q in item.get("lane_divider_quality_options", "").split(",") if q.strip()
                    ]
                elif ooi_type == "Zebra crossing":
                    assert zebra_crossing_option is not None, "Missing 'zebra_crossing_option'"
                    polyline_object_instance.set_answer(
                        attribute=ooi_type_radio_attribute, answer=zebra_crossing_option
                    )
                    checklist_attribute = zebra_crossing_checklist_attribute
                    quality_options = [
                        q.strip() for q in item.get("zebra_crossing_quality_options", "").split(",") if q.strip()
                    ]
                elif ooi_type == "Other":
                    assert other_ooi_option is not None, "Missing 'other_ooi_option'"
                    polyline_object_instance.set_answer(attribute=ooi_type_radio_attribute, answer=other_ooi_option)
                    text_answer = item.get("Type", "")
                    assert isinstance(text_answer, str), "'Type' must be a string"
                    polyline_object_instance.set_answer(attribute=other_ooi_option_text_attribute, answer=text_answer)
                    quality_options = []

                # Process checklist options
                checklist_answers = []
                for quality in quality_options:
                    option = None
                    if quality == "Good quality":
                        option = (
                            curb_good_quality_option
                            if ooi_type == "Curb"
                            else lane_divider_good_quality_option
                            if ooi_type == "Lane divider"
                            else zebra_crossing_good_quality_option
                            if ooi_type == "Zebra crossing"
                            else None
                        )
                    elif quality == "Well lit":
                        option = (
                            curb_well_lit_option
                            if ooi_type == "Curb"
                            else lane_divider_well_lit_option
                            if ooi_type == "Lane divider"
                            else zebra_crossing_well_lit_option
                            if ooi_type == "Zebra crossing"
                            else None
                        )
                    elif quality == "Fully visible":
                        option = (
                            curb_fully_visible_option
                            if ooi_type == "Curb"
                            else lane_divider_fully_visible_option
                            if ooi_type == "Lane divider"
                            else zebra_crossing_fully_visible_option
                            if ooi_type == "Zebra crossing"
                            else None
                        )

                    if option:
                        checklist_answers.append(option)
                    else:
                        assert ooi_type == "Other", f"Invalid quality '{quality}' for type '{ooi_type}'"

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

print("Labels with radio buttons, checklist attributes, and text labels added for all data units.")
