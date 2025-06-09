"""
Code Block Name: Rotatable Bounding Boxes Images/Videos
"""

# Import dependencies
from encord import EncordUserClient, Project
from encord.objects import ChecklistAttribute, Object, ObjectInstance, Option, RadioAttribute, TextAttribute
from encord.objects.coordinates import RotatableBoundingBoxCoordinates

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"
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

# Create radio button attribute for persimmon type
ontology_structure = project.ontology_structure
assert ontology_structure is not None, "Ontology structure is missing from the project"

# Find a bounding box annotation object in the project ontology
rbbox_ontology_object: Object = ontology_structure.get_child_by_title(title="Persimmons", type_=Object)
assert rbbox_ontology_object is not None, "Object 'Persimmons' not found in ontology"

# Get radio attribute for persimmon type
persimmon_type_radio_attribute = ontology_structure.get_child_by_title(type_=RadioAttribute, title="Type?")
assert persimmon_type_radio_attribute is not None, "Radio attribute 'Type?' not found"

# Create radio options
hachiya_option = persimmon_type_radio_attribute.get_child_by_title(type_=Option, title="Hachiya")
assert hachiya_option is not None, "Option 'Hachiya' not found under 'Type?'"

fuyu_option = persimmon_type_radio_attribute.get_child_by_title(type_=Option, title="Fuyu")
assert fuyu_option is not None, "Option 'Fuyu' not found under 'Type?'"

rjb_option = persimmon_type_radio_attribute.get_child_by_title(type_=Option, title="Rojo Brilliante")
assert rjb_option is not None, "Option 'Rojo Brilliante' not found under 'Type?'"

other_persimmon_option = persimmon_type_radio_attribute.get_child_by_title(type_=Option, title="Other persimmon type")
assert other_persimmon_option is not None, "Option 'Other persimmon type' not found under 'Type?'"

# Hachiya Qualities
hachiya_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Hachiya Qualities?"
)
assert hachiya_checklist_attribute is not None, "Checklist attribute 'Hachiya Qualities?' not found"

hachiya_plump_option = hachiya_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
assert hachiya_plump_option is not None, "Option 'Plump' not found under 'Hachiya Qualities?'"

hachiya_juicy_option = hachiya_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
assert hachiya_juicy_option is not None, "Option 'Juicy' not found under 'Hachiya Qualities?'"

hachiya_large_option = hachiya_checklist_attribute.get_child_by_title(type_=Option, title="Large")
assert hachiya_large_option is not None, "Option 'Large' not found under 'Hachiya Qualities?'"

# Fuyu Qualities
fuyu_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="Fuyu Qualities?")
assert fuyu_checklist_attribute is not None, "Checklist attribute 'Fuyu Qualities?' not found"

fuyu_plump_option = fuyu_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
assert fuyu_plump_option is not None, "Option 'Plump' not found under 'Fuyu Qualities?'"

fuyu_juicy_option = fuyu_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
assert fuyu_juicy_option is not None, "Option 'Juicy' not found under 'Fuyu Qualities?'"

fuyu_large_option = fuyu_checklist_attribute.get_child_by_title(type_=Option, title="Large")
assert fuyu_large_option is not None, "Option 'Large' not found under 'Fuyu Qualities?'"

# Rojo Brilliante Qualities
rjb_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Rojo Brilliante Qualities?"
)
assert rjb_checklist_attribute is not None, "Checklist attribute 'Rojo Brilliante Qualities?' not found"

rjb_plump_option = rjb_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
assert rjb_plump_option is not None, "Option 'Plump' not found under 'Rojo Brilliante Qualities?'"

rjb_juicy_option = rjb_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
assert rjb_juicy_option is not None, "Option 'Juicy' not found under 'Rojo Brilliante Qualities?'"

rjb_large_option = rjb_checklist_attribute.get_child_by_title(type_=Option, title="Large")
assert rjb_large_option is not None, "Option 'Large' not found under 'Rojo Brilliante Qualities?'"

# Other persimmon type text input
other_persimmon_option_text_attribute = ontology_structure.get_child_by_title(
    type_=TextAttribute, title="Specify persimmon type"
)
assert other_persimmon_option_text_attribute is not None, "Text attribute 'Specify persimmon type' not found"

# Dictionary of labels per data unit and per frame with persimmon type specified, including quality options
video_frame_labels = {
    "cherries-001.jpg": {
        0: {
            "label_ref": "persimmon_001",
            "coordinates": RotatableBoundingBoxCoordinates(
                height=0.4, width=0.4, top_left_x=0.05, top_left_y=0.55, theta=23
            ),
            "persimmon_type": "Rojo Brilliante",
            "rjb_quality_options": "Plump, Juicy",
        },
    },
    "cherries-010.jpg": {
        0: [
            {
                "label_ref": "persimmon_002",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.4, width=0.4, top_left_x=0.05, top_left_y=0.55, theta=23
                ),
                "persimmon_type": "Fuyu",
                "fuyu_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "persimmon_003",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.2, width=0.1, top_left_x=0.2, top_left_y=0.2, theta=25
                ),
                "persimmon_type": "Rojo Brilliante",
                "rjb_quality_options": "Plump",
            },
            {
                "label_ref": "persimmon_004",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.2, width=0.1, top_left_x=0.3, top_left_y=0.3, theta=27
                ),
                "persimmon_type": "Other persimmon type",
                "Specify persimmon type": "Triumph",
            },
        ],
    },
    "cherries-ig": {
        0: {
            "label_ref": "persimmon_005",
            "coordinates": RotatableBoundingBoxCoordinates(
                height=0.4, width=0.4, top_left_x=0.05, top_left_y=0.55, theta=23
            ),
            "persimmon_type": "Hachiya",
            "hachiya_quality_options": "Plump, Juicy",
        },
        2: [
            {
                "label_ref": "persimmon_006",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.1, width=0.2, top_left_x=0.2, top_left_y=0.2, theta=23
                ),
                "persimmon_type": "Fuyu",
                "fuyu_quality_options": "Large",
            },
            {
                "label_ref": "persimmon_007",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.1, width=0.2, top_left_x=0.4, top_left_y=0.2, theta=127
                ),
                "persimmon_type": "Rojo Brilliante",
                "rjb_quality_options": "Plump",
            },
            {
                "label_ref": "persimmon_008",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.2, width=0.1, top_left_x=0.6, top_left_y=0.3, theta=137
                ),
                "persimmon_type": "Other persimmon type",
                "Specify persimmon type": "Hiro",
            },
        ],
    },
    "cherries-is": {
        0: {
            "label_ref": "persimmon_009",
            "coordinates": RotatableBoundingBoxCoordinates(
                height=0.4, width=0.4, top_left_x=0.05, top_left_y=0.55, theta=23
            ),
            "persimmon_type": "Hachiya",
            "hachiya_quality_options": "Plump",
        },
        3: [
            {
                "label_ref": "persimmon_010",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.4, width=0.4, top_left_x=0.05, top_left_y=0.05, theta=23
                ),
                "persimmon_type": "Fuyu",
                "fuyu_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "persimmon_011",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.3, width=0.3, top_left_x=0.5, top_left_y=0.05, theta=23
                ),
                "persimmon_type": "Rojo Brilliante",
                "rjb_quality_options": "Plump, Juicy",
            },
            {
                "label_ref": "persimmon_012",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.2, width=0.1, top_left_x=0.7, top_left_y=0.05, theta=23
                ),
                "persimmon_type": "Other persimmon type",
                "Specify persimmon type": "Maru",
            },
        ],
    },
    "cherries-vid-001.mp4": {
        103: [
            {
                "label_ref": "persimmon_013",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.5, width=0.5, top_left_x=0.05, top_left_y=0.55, theta=23
                ),
                "persimmon_type": "Rojo Brilliante",
                "rjb_quality_options": "Plump",
            },
            {
                "label_ref": "persimmon_014",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.2, width=0.2, top_left_x=0.3, top_left_y=0.2, theta=23
                ),
                "persimmon_type": "Hachiya",
                "hachiya_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "persimmon_015",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.2, width=0.1, top_left_x=0.6, top_left_y=0.2, theta=23
                ),
                "persimmon_type": "Other persimmon type",
                "Specify persimmon type": "Triumph",
            },
        ],
        104: [
            {
                "label_ref": "persimmon_016",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.5, width=0.5, top_left_x=0.05, top_left_y=0.55, theta=23
                ),
                "persimmon_type": "Rojo Brilliante",
                "rjb_quality_options": "Plump",
            },
            {
                "label_ref": "persimmon_014",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.2, width=0.2, top_left_x=0.3, top_left_y=0.2, theta=23
                ),
                "persimmon_type": "Hachiya",
                "hachiya_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "persimmon_017",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.2, width=0.1, top_left_x=0.6, top_left_y=0.2, theta=23
                ),
                "persimmon_type": "Other persimmon type",
                "Specify persimmon type": "Hiro",
            },
        ],
        105: [
            {
                "label_ref": "persimmon_016",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.5, width=0.5, top_left_x=0.05, top_left_y=0.55, theta=23
                ),
                "persimmon_type": "Rojo Brilliante",
                "rjb_quality_options": "Plump",
            },
            {
                "label_ref": "persimmon_014",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.2, width=0.2, top_left_x=0.3, top_left_y=0.2, theta=23
                ),
                "persimmon_type": "Hachiya",
                "hachiya_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "persimmon_017",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.2, width=0.1, top_left_x=0.6, top_left_y=0.2, theta=23
                ),
                "persimmon_type": "Other persimmon type",
                "Specify persimmon type": "Maru",
            },
        ],
    },
}

# Cache label rows after initialization
label_row_map = {}

# Step 1: Initialize all label rows with a bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for data_unit in video_frame_labels.keys():
        label_rows = project.list_label_rows_v2(data_title_eq=data_unit)
        assert isinstance(label_rows, list), f"Expected list of label rows for '{data_unit}', got {type(label_rows)}"
        assert label_rows, f"No label row found for {data_unit}"

        label_row = label_rows[0]
        assert label_row is not None, f"Label row is None for {data_unit}"

        label_row.initialise_labels(bundle=bundle)
        assert label_row.ontology_structure is not None, f"Ontology not initialized for label row: {data_unit}"

        label_row_map[data_unit] = label_row  # Cache it for processing later

# Step 2: Process labels and collect label rows to save
label_rows_to_save = []

for data_unit, frame_coordinates in video_frame_labels.items():
    label_row = label_row_map.get(data_unit)
    assert label_row is not None, f"Missing initialized label row for {data_unit}"

    object_instances_by_label_ref = {}

    for frame_number, items in frame_coordinates.items():
        assert isinstance(frame_number, int), f"Frame number must be int, got {type(frame_number)}"

        if not isinstance(items, list):
            items = [items]

        for item in items:
            label_ref = item["label_ref"]
            coord = item["coordinates"]
            persimmon_type = item["persimmon_type"]

            assert persimmon_type in {
                "Hachiya",
                "Fuyu",
                "Rojo Brilliante",
                "Other persimmon type",
            }, f"Unexpected persimmon type '{persimmon_type}' in {data_unit}"

            if label_ref not in object_instances_by_label_ref:
                rbbox_object_instance: ObjectInstance = rbbox_ontology_object.create_instance()
                assert rbbox_object_instance is not None, f"Failed to create ObjectInstance for {label_ref}"

                checklist_attribute = None
                quality_options = []

                # Set persimmon type and checklist attributes
                if persimmon_type == "Hachiya":
                    assert hachiya_option is not None, "Missing 'hachiya_option'"
                    rbbox_object_instance.set_answer(attribute=persimmon_type_radio_attribute, answer=hachiya_option)
                    checklist_attribute = hachiya_checklist_attribute
                    quality_options = item.get("hachiya_quality_options", "").split(", ")
                elif persimmon_type == "Fuyu":
                    assert fuyu_option is not None, "Missing 'fuyu_option'"
                    rbbox_object_instance.set_answer(attribute=persimmon_type_radio_attribute, answer=fuyu_option)
                    checklist_attribute = fuyu_checklist_attribute
                    quality_options = item.get("fuyu_quality_options", "").split(", ")
                elif persimmon_type == "Rojo Brilliante":
                    assert rjb_option is not None, "Missing 'rjb_option'"
                    rbbox_object_instance.set_answer(attribute=persimmon_type_radio_attribute, answer=rjb_option)
                    checklist_attribute = rjb_checklist_attribute
                    quality_options = item.get("rjb_quality_options", "").split(", ")
                elif persimmon_type == "Other persimmon type":
                    assert other_persimmon_option is not None, "Missing 'other_persimmon_option'"
                    rbbox_object_instance.set_answer(
                        attribute=persimmon_type_radio_attribute, answer=other_persimmon_option
                    )
                    text_answer = item.get("Specify persimmon type", "")
                    assert isinstance(text_answer, str), "'Specify persimmon type' must be a string"
                    rbbox_object_instance.set_answer(
                        attribute=other_persimmon_option_text_attribute, answer=text_answer
                    )
                    quality_options = []

                # Set checklist answers based on quality options
                checklist_answers = []
                for quality in quality_options:
                    option = None
                    if quality == "Plump":
                        option = (
                            hachiya_plump_option
                            if persimmon_type == "Hachiya"
                            else fuyu_plump_option
                            if persimmon_type == "Fuyu"
                            else rjb_plump_option
                            if persimmon_type == "Rojo Brilliante"
                            else None
                        )
                    elif quality == "Juicy":
                        option = (
                            hachiya_juicy_option
                            if persimmon_type == "Hachiya"
                            else fuyu_juicy_option
                            if persimmon_type == "Fuyu"
                            else rjb_juicy_option
                            if persimmon_type == "Rojo Brilliante"
                            else None
                        )
                    elif quality == "Large":
                        option = (
                            hachiya_large_option
                            if persimmon_type == "Hachiya"
                            else fuyu_large_option
                            if persimmon_type == "Fuyu"
                            else rjb_large_option
                            if persimmon_type == "Rojo Brilliante"
                            else None
                        )

                    if option:
                        checklist_answers.append(option)
                    else:
                        assert (
                            persimmon_type == "Other persimmon type"
                        ), f"Invalid quality '{quality}' for persimmon type '{persimmon_type}'"

                if checklist_attribute and checklist_answers:
                    rbbox_object_instance.set_answer(
                        attribute=checklist_attribute, answer=checklist_answers, overwrite=True
                    )

                object_instances_by_label_ref[label_ref] = rbbox_object_instance

            else:
                rbbox_object_instance = object_instances_by_label_ref[label_ref]

            # Assign coordinates for this frame
            rbbox_object_instance.set_for_frames(coordinates=coord, frames=frame_number)

    # Add object instances to label_row **only if they have frames assigned**
    for rbbox_object_instance in object_instances_by_label_ref.values():
        assert isinstance(rbbox_object_instance, ObjectInstance), "Expected ObjectInstance type"
        if rbbox_object_instance.get_annotation_frames():
            label_row.add_object_instance(rbbox_object_instance)

    # Collect for saving in the next bundle
    label_rows_to_save.append(label_row)

# Step 3: Save all label rows with a bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for label_row in label_rows_to_save:
        assert label_row is not None, "Trying to save a None label row"
        label_row.save(bundle=bundle)
        print(f"Saved label row for {label_row.data_title}")

print("Labels with persimmon type radio buttons, checklist attributes, and text labels added for all data units.")
