"""
Code Block Name: Cuboids
"""

# Import dependencies
from encord import EncordUserClient, Project
from encord.objects import Object
from encord.objects.coordinates import CuboidCoordinates

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

# Create radio button attribute for Person type
ontology_structure = project.ontology_structure

# Find a cuboid annotation object in the project ontology
cuboid_ontology_object: Object = ontology_structure.get_child_by_title(title="Person", type_=Object)
assert cuboid_ontology_object is not None, "Cuboid object 'Person' not found in ontology."

# Dictionary of labels per data unit and per frame with Person type specified, including quality options
pcd_labels = {
    "scene-1094": {
        0: {
            "label_ref": "person_001",
            "coordinates": CuboidCoordinates(
                position=(9, 9, 9), 
                orientation=(0.11, 0.77, 0.33), 
                size=(0.2, 0.2, 0.2)
                ),
        }
    },
    "scene-0916": {
        0: [
            {
                "label_ref": "person_002",
                "coordinates": CuboidCoordinates(
                    position=(0.4, 0.4, 0.4), 
                    orientation=(0.0, 0.0, 0.4), 
                    size=(0.1, 0.1, 0.1)
                ),
            },
            {
                "label_ref": "person_003",
                "coordinates": CuboidCoordinates(
                    position=(0.2, 0.2, 0.0), 
                    orientation=(0.0, 0.0, 0.1), 
                    size=(0.5, 0.5, 0.5)
                ),
            },
            {
                "label_ref": "person_004",
                "coordinates": CuboidCoordinates(
                    position=(0.2, 0.2, 0.0), 
                    orientation=(0.0, 0.0, 0.1), 
                    size=(0.7, 0.7, 0.7)
                ),
            },
        ],
    },
    "scene-0796": {
        0: {
            "label_ref": "person_005",
            "coordinates": CuboidCoordinates(
                position=(0.4, 0.4, 0.0), 
                orientation=(0.0, 0.0, 0.4), 
                size=(0.12, 0.12, 0.12)
            ),
        },
        2: [
            {
                "label_ref": "person_006",
                "coordinates": CuboidCoordinates(
                    position=(0.1, 0.1, 0.0), 
                    orientation=(0.0, 0.0, 0.2), 
                    size=(0.5, 0.5, 0.5)
                ),
            },
            {
                "label_ref": "person_007",
                "coordinates": CuboidCoordinates(
                    position=(0.1, 0.1, 0.0), 
                    orientation=(0.0, 0.0, 0.2), 
                    size=(0.0132, 0.0132, 0.0132)
                ),
            },
            {
                "label_ref": "person_008",
                "coordinates": CuboidCoordinates(
                    position=(0.2, 0.2, 0.0), 
                    orientation=(0.0, 0.0, 0.1), 
                    size=(0.8, 0.8, 0.8)
                ),
            },
        ],
    },
    "scene-1100": {
        0: {
            "label_ref": "person_009",
            "coordinates": CuboidCoordinates(
                position=(0.4, 0.4, 0.0), 
                orientation=(0.0, 0.0, 0.4), 
                size=(0.012, 0.012, 0.012)
            ),
        },
        3: [
            {
                "label_ref": "person_010",
                "coordinates": CuboidCoordinates(
                    position=(0.4, 0.4, 0.0), 
                    orientation=(0.0, 0.0, 0.4), 
                    size=(0.5, 0.5, 0.5)
                ),
            },
            {
                "label_ref": "person_011",
                "coordinates": CuboidCoordinates(
                    position=(0.3, 0.3, 0.0), 
                    orientation=(0.0, 0.0, 0.3), 
                    size=(0.13, 0.13, 0.13)
                ),
            },
            {
                "label_ref": "person_012",
                "coordinates": CuboidCoordinates(
                    position=(0.2, 0.2, 0.0), 
                    orientation=(0.0, 0.0, 0.1), 
                    size=(0.9, 0.9, 0.9)
                ),
            },
        ],
    },
    "scene-0655": {
        13: [
            {
                "label_ref": "person_013",
                "coordinates": CuboidCoordinates(
                    position=(0.5, 0.5, 0.0), 
                    orientation=(0.0, 0.0, 0.5), 
                    size=(0.11, 0.11, 0.11)
                ),
            },
            {
                "label_ref": "person_014",
                "coordinates": CuboidCoordinates(
                    position=(0.2, 0.2, 0.0), 
                    orientation=(0.0, 0.0, 0.2), 
                    size=(0.6, 0.6, 0.6)
                ),
            },
            {
                "label_ref": "person_015",
                "coordinates": CuboidCoordinates(
                    position=(0.2, 0.2, 0.0), 
                    orientation=(0.0, 0.0, 0.1), 
                    size=(0.8, 0.8, 0.8)
                ),
            },
        ],
        14: [
            {
                "label_ref": "person_016",
                "coordinates": CuboidCoordinates(
                    position=(0.5, 0.5, 0.0), 
                    orientation=(0.0, 0.0, 0.5), 
                    size=(0.3, 0.3, 0.3)
                ),
            },
            {
                "label_ref": "person_014",
                "coordinates": CuboidCoordinates(
                    position=(0.2, 0.2, 0.0), 
                    orientation=(0.0, 0.0, 0.2), 
                    size=(0.6, 0.6, 0.6)
                ),
            },
            {
                "label_ref": "person_017",
                "coordinates": CuboidCoordinates(
                    position=(0.2, 0.2, 0.0), 
                    orientation=(0.0, 0.0, 0.1), 
                    size=(0.8, 0.8, 0.8)
                ),
            },
        ],
        15: [
            {
                "label_ref": "person_016",
                "coordinates": CuboidCoordinates(
                    position=(0.5, 0.5, 0.0), 
                    orientation=(0.0, 0.0, 0.5), 
                    size=(0.1, 0.1, 0.1)
                ),
            },
            {
                "label_ref": "person_014",
                "coordinates": CuboidCoordinates(
                    position=(0.2, 0.2, 0.0), 
                    orientation=(0.0, 0.0, 0.2), 
                    size=(0.6, 0.6, 0.6)
                ),
            },
            {
                "label_ref": "person_017",
                "coordinates": CuboidCoordinates(
                    position=(0.2, 0.2, 0.0), 
                    orientation=(0.0, 0.0, 0.1), 
                    size=(0.8, 0.8, 0.8)
                ),
            },
        ],
    },
}


# Initialize label rows
label_row_map = {}
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for data_title in pcd_labels.keys():
        rows = project.list_label_rows_v2(data_title_eq=data_title)
        if not rows:
            print(f"Skipping: No label row found for {data_title}")
            continue
        lr = rows[0]
        lr.initialise_labels(bundle=bundle)
        label_row_map[data_title] = lr

# Create instances
label_rows_to_save = []
for data_title, frames in pcd_labels.items():
    lr = label_row_map.get(data_title)
    if not lr:
        continue

    instances_by_ref = {}

    for frame_no, items in frames.items():
        # normalize to list
        items = items if isinstance(items, list) else [items]

        for item in items:
            ref = item["label_ref"]
            coords = item["coordinates"]

            if ref not in instances_by_ref:
                instances_by_ref[ref] = cuboid_ontology_object.create_instance()

            instances_by_ref[ref].set_for_frames(coordinates=coords, frames=frame_no)

    # Add only instances that have at least one frame
    for inst in instances_by_ref.values():
        if inst.get_annotation_frames():
            lr.add_object_instance(inst)

    label_rows_to_save.append(lr)

# Save all label rows
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for lr in label_rows_to_save:
        lr.save(bundle=bundle)
        print(f"Saved label row for {lr.data_title}")