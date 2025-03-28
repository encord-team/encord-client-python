# Import dependencies
from encord import EncordUserClient, Project
from encord.objects import ChecklistAttribute, Object, ObjectInstance, Option, RadioAttribute, TextAttribute
from encord.objects.coordinates import RotatableBoundingBoxCoordinates

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

# Create radio button attribute for persimmon type
ontology_structure = project.ontology_structure

# Find a bounding box annotation object in the project ontology
rbbox_ontology_object: Object = ontology_structure.get_child_by_title(title="Persimmons", type_=Object)

persimmon_type_radio_attribute = ontology_structure.get_child_by_title(type_=RadioAttribute, title="Type?")

# Create options for the radio buttons
hachiya_option = persimmon_type_radio_attribute.get_child_by_title(type_=Option, title="Hachiya")
fuyu_option = persimmon_type_radio_attribute.get_child_by_title(type_=Option, title="Fuyu")
rjb_option = persimmon_type_radio_attribute.get_child_by_title(type_=Option, title="Rojo Brilliante")
other_persimmon_option = persimmon_type_radio_attribute.get_child_by_title(type_=Option, title="Other persimmon type")

# Create checklist attributes and options for each persimmon type
# Hachiya Qualities
hachiya_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Hachiya Qualities?"
)
hachiya_plump_option = hachiya_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
hachiya_juicy_option = hachiya_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
hachiya_large_option = hachiya_checklist_attribute.get_child_by_title(type_=Option, title="Large")

# Fuyu Qualities
fuyu_checklist_attribute = ontology_structure.get_child_by_title(type_=ChecklistAttribute, title="Fuyu Qualities?")
fuyu_plump_option = fuyu_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
fuyu_juicy_option = fuyu_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
fuyu_large_option = fuyu_checklist_attribute.get_child_by_title(type_=Option, title="Large")

# Rojo Brilliante Qualities
rjb_checklist_attribute = ontology_structure.get_child_by_title(
    type_=ChecklistAttribute, title="Rojo Brilliante Qualities?"
)
rjb_plump_option = rjb_checklist_attribute.get_child_by_title(type_=Option, title="Plump")
rjb_juicy_option = rjb_checklist_attribute.get_child_by_title(type_=Option, title="Juicy")
rjb_large_option = rjb_checklist_attribute.get_child_by_title(type_=Option, title="Large")

# Other persimmon Types
other_persimmon_option_text_attribute = ontology_structure.get_child_by_title(
    type_=TextAttribute, title="Specify persimmon type"
)

# Dictionary of labels per data unit and per frame with persimmon type specified, including quality options
video_frame_labels = {
    "cherries-001.jpg": {
        0: {
            "label_ref": "persimmon_001",
            "coordinates": RotatableBoundingBoxCoordinates(
                height=0.4, width=0.4, top_left_x=0.1, top_left_y=0.1, theta=23
            ),
            "persimmon_type": "Rojo Brilliante",
            "rjb_quality_options": "Plump, Juicy",
        }
    },
    "cherries-010.jpg": {
        0: [
            {
                "label_ref": "persimmon_002",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.4, width=0.4, top_left_x=0.1, top_left_y=0.1, theta=23
                ),
                "persimmon_type": "Fuyu",
                "fuyu_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "persimmon_003",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.2, width=0.1, top_left_x=0.5, top_left_y=0.5, theta=25
                ),
                "persimmon_type": "Rojo Brilliante",
                "rjb_quality_options": "Plump",
            },
            {
                "label_ref": "persimmon_004",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.2, width=0.1, top_left_x=0.5, top_left_y=0.5, theta=27
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
                height=0.4, width=0.4, top_left_x=0.1, top_left_y=0.1, theta=23
            ),
            "persimmon_type": "Hachiya",
            "hachiya_quality_options": "Plump, Juicy",
        },
        2: [
            {
                "label_ref": "persimmon_006",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.1, width=0.2, top_left_x=0.3, top_left_y=0.2, theta=23
                ),
                "persimmon_type": "Fuyu",
                "fuyu_quality_options": "Large",
            },
            {
                "label_ref": "persimmon_007",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.1, width=0.2, top_left_x=0.4, top_left_y=0.5, theta=127
                ),
                "persimmon_type": "Rojo Brilliante",
                "rjb_quality_options": "Plump",
            },
            {
                "label_ref": "persimmon_008",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.2, width=0.1, top_left_x=0.5, top_left_y=0.5, theta=137
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
                height=0.4, width=0.4, top_left_x=0.1, top_left_y=0.1, theta=23
            ),
            "persimmon_type": "Hachiya",
            "hachiya_quality_options": "Plump",
        },
        3: [
            {
                "label_ref": "persimmon_010",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.4, width=0.4, top_left_x=0.1, top_left_y=0.1, theta=23
                ),
                "persimmon_type": "Fuyu",
                "fuyu_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "persimmon_011",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.3, width=0.3, top_left_x=0.2, top_left_y=0.2, theta=23
                ),
                "persimmon_type": "Rojo Brilliante",
                "rjb_quality_options": "Plump, Juicy",
            },
            {
                "label_ref": "persimmon_012",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.2, width=0.1, top_left_x=0.5, top_left_y=0.5, theta=23
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
                    height=0.5, width=0.5, top_left_x=0.2, top_left_y=0.0, theta=23
                ),
                "persimmon_type": "Rojo Brilliante",
                "rjb_quality_options": "Plump",
            },
            {
                "label_ref": "persimmon_014",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.2, width=0.2, top_left_x=0.1, top_left_y=0.1, theta=23
                ),
                "persimmon_type": "Hachiya",
                "hachiya_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "persimmon_015",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.2, width=0.1, top_left_x=0.5, top_left_y=0.5, theta=23
                ),
                "persimmon_type": "Other persimmon type",
                "Specify persimmon type": "Triumph",
            },
        ],
        104: [
            {
                "label_ref": "persimmon_016",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.5, width=0.5, top_left_x=0.2, top_left_y=0.2, theta=23
                ),
                "persimmon_type": "Rojo Brilliante",
                "rjb_quality_options": "Plump",
            },
            {
                "label_ref": "persimmon_014",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.2, width=0.2, top_left_x=0.1, top_left_y=0.1, theta=23
                ),
                "persimmon_type": "Hachiya",
                "hachiya_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "persimmon_017",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.2, width=0.1, top_left_x=0.5, top_left_y=0.5, theta=23
                ),
                "persimmon_type": "Other persimmon type",
                "Specify persimmon type": "Hiro",
            },
        ],
        105: [
            {
                "label_ref": "persimmon_016",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.5, width=0.5, top_left_x=0.2, top_left_y=0.2, theta=23
                ),
                "persimmon_type": "Rojo Brilliante",
                "rjb_quality_options": "Plump",
            },
            {
                "label_ref": "persimmon_014",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.2, width=0.2, top_left_x=0.1, top_left_y=0.1, theta=23
                ),
                "persimmon_type": "Hachiya",
                "hachiya_quality_options": "Plump, Juicy, Large",
            },
            {
                "label_ref": "persimmon_017",
                "coordinates": RotatableBoundingBoxCoordinates(
                    height=0.2, width=0.1, top_left_x=0.5, top_left_y=0.5, theta=23
                ),
                "persimmon_type": "Other persimmon type",
                "Specify persimmon type": "Maru",
            },
        ],
    },
}

# Bundle size
BUNDLE_SIZE = 100

# Cache label rows after initialization
label_row_map = {}

# Step 1: Initialize all label rows with a bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for data_unit in video_frame_labels.keys():
        label_rows = project.list_label_rows_v2(data_title_eq=data_unit)
        if not label_rows:
            print(f"Skipping: No label row found for {data_unit}")
            continue

        label_row = label_rows[0]
        label_row.initialise_labels(bundle=bundle)
        label_row_map[data_unit] = label_row  # Cache it for processing later

# Step 2: Process labels and collect label rows to save
label_rows_to_save = []

for data_unit, frame_coordinates in video_frame_labels.items():
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
            persimmon_type = item["persimmon_type"]

            if label_ref not in object_instances_by_label_ref:
                rbbox_object_instance: ObjectInstance = rbbox_ontology_object.create_instance()
                checklist_attribute = None
                quality_options = []

                # Set persimmon type and checklist attributes
                if persimmon_type == "Hachiya":
                    rbbox_object_instance.set_answer(attribute=persimmon_type_radio_attribute, answer=hachiya_option)
                    checklist_attribute = hachiya_checklist_attribute
                    quality_options = item.get("hachiya_quality_options", "").split(", ")
                elif persimmon_type == "Fuyu":
                    rbbox_object_instance.set_answer(attribute=persimmon_type_radio_attribute, answer=fuyu_option)
                    checklist_attribute = fuyu_checklist_attribute
                    quality_options = item.get("fuyu_quality_options", "").split(", ")
                elif persimmon_type == "Rojo Brilliante":
                    rbbox_object_instance.set_answer(attribute=persimmon_type_radio_attribute, answer=rjb_option)
                    checklist_attribute = rjb_checklist_attribute
                    quality_options = item.get("rjb_quality_options", "").split(", ")
                elif persimmon_type == "Other persimmon type":
                    rbbox_object_instance.set_answer(
                        attribute=persimmon_type_radio_attribute, answer=other_persimmon_option
                    )
                    rbbox_object_instance.set_answer(
                        attribute=other_persimmon_option_text_attribute, answer=item.get("Specify persimmon type", "")
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
        if rbbox_object_instance.get_annotation_frames():  # Ensures it has at least one frame
            label_row.add_object_instance(rbbox_object_instance)

    # Collect for saving in the next bundle
    label_rows_to_save.append(label_row)

# Step 3: Save all label rows with a bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for label_row in label_rows_to_save:
        label_row.save(bundle=bundle)
        print(f"Saved label row for {label_row.data_title}")

print("Labels with persimmon type radio buttons, checklist attributes, and text labels added for all data units.")
