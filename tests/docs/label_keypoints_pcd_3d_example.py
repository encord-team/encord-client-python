"""
Code Block Name: Keypoints PCD
"""

# Import dependencies

from encord import EncordUserClient, Project
from encord.objects import ChecklistAttribute, Object, ObjectInstance, Option, RadioAttribute, TextAttribute
from encord.objects.coordinates import PointCoordinate3D

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

# Get keypoint object for Point of Interest
keypoint_ontology_object: Object = ontology_structure.get_child_by_title(title="Point of Interest", type_=Object)
assert keypoint_ontology_object is not None, "Keypoint object 'Point of Interest' not found in ontology"

# Get radio attribute for Point of Interest type
poi_type_radio_attribute = ontology_structure.get_child_by_title(type_=RadioAttribute, title="Type?")
assert poi_type_radio_attribute is not None, "Radio attribute 'Type?' not found"

# Get radio options
sign_option = poi_type_radio_attribute.get_child_by_title(type_=Option, title="Sign")
assert sign_option is not None, "Option 'Sign' not found under radio attribute 'Type?'"

traffic_light_option = poi_type_radio_attribute.get_child_by_title(type_=Option, title="Traffic light")
assert traffic_light_option is not None, "Option 'Traffic light' not found under radio attribute 'Type?'"

other_poi_option = poi_type_radio_attribute.get_child_by_title(type_=Option, title="Other Point of Interest type")
assert other_poi_option is not None, "Option 'Other Point of Interest type' not found under radio attribute 'Type?'"

# Get checklist attributes and options for Sign
sign_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="Sign Qualities?")
assert sign_checklist_attribute is not None, "Checklist attribute 'Sign Qualities?' not found"

sign_well_positioned_option = sign_checklist_attribute.get_child_by_title(type_=Option, title="Well positioned")
assert sign_well_positioned_option is not None, "Option 'Well positioned' not found under 'Sign Qualities?'"

sign_good_visibility_option = sign_checklist_attribute.get_child_by_title(type_=Option, title="Good visibility")
assert sign_good_visibility_option is not None, "Option 'Good visibility' not found under 'Sign Qualities?'"

sign_good_condition_option = sign_checklist_attribute.get_child_by_title(type_=Option, title="Good condition")
assert sign_good_condition_option is not None, "Option 'Good condition' not found under 'Sign Qualities?'"

# Get checklist attributes and options for Traffic light
traffic_light_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Traffic light Qualities?"
)
assert traffic_light_checklist_attribute is not None, "Checklist attribute 'Traffic light Qualities?' not found"

traffic_light_well_positioned_option = traffic_light_checklist_attribute.get_child_by_title(
    type_=Option, title="Well positioned"
)
assert traffic_light_well_positioned_option is not None, (
    "Option 'Well positioned' not found under 'Traffic light Qualities?'"
)

traffic_light_good_visibility_option = traffic_light_checklist_attribute.get_child_by_title(
    type_=Option, title="Good visibility"
)
assert traffic_light_good_visibility_option is not None, (
    "Option 'Good visibility' not found under 'Traffic light Qualities?'"
)

traffic_light_good_condition_option = traffic_light_checklist_attribute.get_child_by_title(
    type_=Option, title="Good condition"
)
assert traffic_light_good_condition_option is not None, (
    "Option 'Good condition' not found under 'Traffic light Qualities?'"
)

# Get text attribute for specifying other Point of Interest types
other_poi_option_text_attribute = ontology_structure.get_child_by_title(
    type_=TextAttribute, title="Specify Point of Interest type"
)
assert other_poi_option_text_attribute is not None, "Text attribute 'Specify Point of Interest type' not found"

# Dictionary of labels per data unit and per frame with Point of Interest type specified, including quality options
pcd_labels = {
    "scene-1094": {
        1: {
            "label_ref": "poi_001",
            "coordinates": PointCoordinate3D(x=0.01, y=0.02, z=0.03),
            "poi_type": "Sign",
            "sign_quality_options": "Well positioned, Good visibility, Good condition",
        }
    },
    "scene-0916": {
        1: [
            {
                "label_ref": "poi_002",
                "coordinates": PointCoordinate3D(x=0.03, y=0.03, z=0.03),
                "poi_type": "Traffic light",
                "traffic_light_quality_options": "Well positioned, Good visibility, Good condition",
            },
            {
                "label_ref": "poi_003",
                "coordinates": PointCoordinate3D(x=0.5, y=0.4, z=0.3),
                "poi_type": "Traffic light",
                "traffic_light_quality_options": "Good visibility",
            },
            {
                "label_ref": "poi_004",
                "coordinates": PointCoordinate3D(x=0.9, y=0.3, z=0.3),
                "poi_type": "Other Point of Interest type",
                "Specify Point of Interest type": "Curb",
            },
        ],
    },
    "scene-0796": {
        0: {
            "label_ref": "poi_005",
            "coordinates": PointCoordinate3D(x=0.05, y=0.02, z=0.03),
            "poi_type": "Sign",
            "sign_quality_options": "Well positioned, Good visibility, Good condition",
        },
        2: [
            {
                "label_ref": "poi_006",
                "coordinates": PointCoordinate3D(x=0.3, y=0.3, z=0.3),
                "poi_type": "Sign",
                "sign_quality_options": "Good condition",
            },
            {
                "label_ref": "poi_007",
                "coordinates": PointCoordinate3D(x=0.4, y=0.5, z=0.3),
                "poi_type": "Sign",
                "sign_quality_options": "Good visibility",
            },
            {
                "label_ref": "poi_008",
                "coordinates": PointCoordinate3D(x=0.11, y=0.2, z=0.3),
                "poi_type": "Other Point of Interest type",
                "Specify Point of Interest type": "Post box",
            },
        ],
    },
    "scene-1100": {
        0: {
            "label_ref": "poi_009",
            "coordinates": PointCoordinate3D(x=0.1, y=0.2, z=0.3),
            "poi_type": "Traffic light",
            "traffic_light_quality_options": "Well positioned, Good visibility, Good condition",
        },
        3: [
            {
                "label_ref": "poi_010",
                "coordinates": PointCoordinate3D(x=0.3, y=0.3, z=0.3),
                "poi_type": "Traffic light",
                "traffic_light_quality_options": "Well positioned, Good visibility, Good condition",
            },
            {
                "label_ref": "poi_011",
                "coordinates": PointCoordinate3D(x=0.8, y=0.5, z=0.3),
                "poi_type": "Traffic light",
                "traffic_light_quality_options": "Good condition",
            },
            {
                "label_ref": "poi_012",
                "coordinates": PointCoordinate3D(x=0.11, y=0.2, z=0.3),
                "poi_type": "Other Point of Interest type",
                "Specify Point of Interest type": "Post box",
            },
        ],
    },
    "scene-0655": {
        1: [
            {
                "label_ref": "poi_013",
                "coordinates": PointCoordinate3D(x=0.2, y=0.1, z=0.3),
                "poi_type": "Sign",
                "sign_quality_options": "Good condition",
            },
            {
                "label_ref": "poi_014",
                "coordinates": PointCoordinate3D(x=0.6, y=0.6, z=0.3),
                "poi_type": "Sign",
                "sign_quality_options": "Well positioned, Good visibility, Good condition",
            },
            {
                "label_ref": "poi_015",
                "coordinates": PointCoordinate3D(x=0.10, y=0.1, z=0.3),
                "poi_type": "Other Point of Interest type",
                "Specify Point of Interest type": "Curb",
            },
        ],
        2: [
            {
                "label_ref": "poi_016",
                "coordinates": PointCoordinate3D(x=0.4, y=0.1, z=0.3),
                "poi_type": "Sign",
                "sign_quality_options": "Good condition",
            },
            {
                "label_ref": "poi_014",
                "coordinates": PointCoordinate3D(x=0.8, y=0.5, z=0.3),
                "poi_type": "Sign",
                "sign_quality_options": "Well positioned, Good visibility, Good condition",
            },
            {
                "label_ref": "poi_017",
                "coordinates": PointCoordinate3D(x=0.11, y=0.2, z=0.3),
                "poi_type": "Other Point of Interest type",
                "Specify Point of Interest type": "Post box",
            },
        ],
        3: [
            {
                "label_ref": "poi_016",
                "coordinates": PointCoordinate3D(x=0.5, y=0.2, z=0.3),
                "poi_type": "Sign",
                "sign_quality_options": "Good condition",
            },
            {
                "label_ref": "poi_014",
                "coordinates": PointCoordinate3D(x=0.7, y=0.4, z=0.3),
                "poi_type": "Sign",
                "sign_quality_options": "Well positioned, Good visibility, Good condition",
            },
            {
                "label_ref": "poi_017",
                "coordinates": PointCoordinate3D(x=0.9, y=0.3, z=0.3),
                "poi_type": "Other Point of Interest type",
                "Specify Point of Interest type": "Post box",
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
            poi_type = item["poi_type"]

            assert poi_type in {
                "Sign",
                "Traffic light",
                "Other Point of Interest type",
            }, f"Unexpected type '{poi_type}' in {data_unit}"

            if label_ref not in object_instances_by_label_ref:
                keypoint_object_instance: ObjectInstance = keypoint_ontology_object.create_instance()
                assert keypoint_object_instance is not None, "Failed to create ObjectInstance"
                checklist_attribute = None
                quality_options = []

                # Assign radio and checklist attributes based on the type
                if poi_type == "Sign":
                    assert sign_option is not None, "Missing 'sign_type'"
                    keypoint_object_instance.set_answer(attribute=poi_type_radio_attribute, answer=sign_option)
                    checklist_attribute = sign_checklist_attribute
                    quality_options = [q.strip() for q in item.get("sign_quality_options", "").split(",") if q.strip()]
                elif poi_type == "Traffic light":
                    assert traffic_light_option is not None, "Missing 'lane_divider_option'"
                    keypoint_object_instance.set_answer(attribute=poi_type_radio_attribute, answer=traffic_light_option)
                    checklist_attribute = traffic_light_checklist_attribute
                    quality_options = [
                        q.strip() for q in item.get("traffic_light_quality_options", "").split(",") if q.strip()
                    ]
                elif poi_type == "Other Point of Interest type":
                    assert other_poi_option is not None, "Missing 'other_ooi_option'"
                    keypoint_object_instance.set_answer(attribute=poi_type_radio_attribute, answer=other_poi_option)
                    text_answer = item.get("Type", "")
                    assert isinstance(text_answer, str), "'Type' must be a string"
                    keypoint_object_instance.set_answer(attribute=other_poi_option_text_attribute, answer=text_answer)
                    quality_options = []

                # Process checklist options
                checklist_answers = []
                for quality in quality_options:
                    option = None
                    if quality == "Well positioned":
                        option = (
                            sign_well_positioned_option
                            if poi_type == "Sign"
                            else traffic_light_well_positioned_option
                            if poi_type == "Traffic light"
                            else None
                        )
                    elif quality == "Good visibility":
                        option = (
                            sign_good_visibility_option
                            if poi_type == "Sign"
                            else traffic_light_good_visibility_option
                            if poi_type == "Traffic light"
                            else None
                        )
                    elif quality == "Good condition":
                        option = (
                            sign_good_condition_option
                            if poi_type == "Sign"
                            else traffic_light_good_condition_option
                            if poi_type == "Traffic light"
                            else None
                        )

                    if option:
                        checklist_answers.append(option)
                    else:
                        assert poi_type == "Other Point of Interest type", (
                            f"Invalid quality '{quality}' for type '{poi_type}'"
                        )

                if checklist_attribute and checklist_answers:
                    keypoint_object_instance.set_answer(
                        attribute=checklist_attribute, answer=checklist_answers, overwrite=True
                    )

                object_instances_by_label_ref[label_ref] = keypoint_object_instance

            else:
                keypoint_object_instance = object_instances_by_label_ref[label_ref]

            # Assign coordinates for this frame
            keypoint_object_instance.set_for_frames(coordinates=coord, frames=frame_number)

    # Add object instances to the label row if they have frames assigned
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

print("Labels with radio buttons, checklist attributes, and text labels added for all data units.")
