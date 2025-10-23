"""
Code Block Name: Keypoints PCD
"""

# Import dependencies
from encord import EncordUserClient, Project
from encord.objects import Object
from encord.objects.coordinates import PointCoordinate3D

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"  # Replace with the file path to your SSH private key
PROJECT_ID = "00000000-0000-0000-0000-000000000000"  # Replace with the unique ID for the Project
BUNDLE_SIZE = 100

# Import dependencies
from encord import EncordUserClient, Project
from encord.objects import Object
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

# Get the ontology
ontology_structure = project.ontology_structure

# Find a cuboid annotation object in the project ontology
keypoint_ontology_object: Object = ontology_structure.get_child_by_title(title="Point of Interest", type_=Object)
assert keypoint_ontology_object is not None, "Keypoint object 'Point of Interest' not found in ontology."

# Dictionary of labels per data unit and per frame with Point of Interest type specified, including quality options
pcd_labels = {
    "scene-1094": {1: {"label_ref": "poi_001", "coordinates": PointCoordinate3D(x=0.01, y=0.02, z=0.03)}},
    "scene-0916": {
        1: [
            {"label_ref": "poi_002", "coordinates": PointCoordinate3D(x=0.03, y=0.03, z=0.03)},
            {"label_ref": "poi_003", "coordinates": PointCoordinate3D(x=0.5, y=0.4, z=0.3)},
            {"label_ref": "poi_004", "coordinates": PointCoordinate3D(x=0.9, y=0.3, z=0.3)},
        ],
    },
    "scene-0796": {
        0: {"label_ref": "poi_005", "coordinates": PointCoordinate3D(x=0.05, y=0.02, z=0.03)},
        2: [
            {"label_ref": "poi_006", "coordinates": PointCoordinate3D(x=0.3, y=0.3, z=0.3)},
            {"label_ref": "poi_007", "coordinates": PointCoordinate3D(x=0.4, y=0.5, z=0.3)},
            {"label_ref": "poi_008", "coordinates": PointCoordinate3D(x=0.11, y=0.2, z=0.3)},
        ],
    },
    "scene-1100": {
        0: {"label_ref": "poi_009", "coordinates": PointCoordinate3D(x=0.1, y=0.2, z=0.3)},
        3: [
            {"label_ref": "poi_010", "coordinates": PointCoordinate3D(x=0.3, y=0.3, z=0.3)},
            {"label_ref": "poi_011", "coordinates": PointCoordinate3D(x=0.8, y=0.5, z=0.3)},
            {"label_ref": "poi_012", "coordinates": PointCoordinate3D(x=0.11, y=0.2, z=0.3)},
        ],
    },
    "scene-0655": {
        1: [
            {"label_ref": "poi_013", "coordinates": PointCoordinate3D(x=0.2, y=0.1, z=0.3)},
            {"label_ref": "poi_014", "coordinates": PointCoordinate3D(x=0.6, y=0.6, z=0.3)},
            {"label_ref": "poi_015", "coordinates": PointCoordinate3D(x=0.10, y=0.1, z=0.3)},
        ],
        2: [
            {"label_ref": "poi_016", "coordinates": PointCoordinate3D(x=0.4, y=0.1, z=0.3)},
            {"label_ref": "poi_014", "coordinates": PointCoordinate3D(x=0.8, y=0.5, z=0.3)},
            {"label_ref": "poi_017", "coordinates": PointCoordinate3D(x=0.11, y=0.2, z=0.3)},
        ],
        3: [
            {"label_ref": "poi_016", "coordinates": PointCoordinate3D(x=0.5, y=0.2, z=0.3)},
            {"label_ref": "poi_014", "coordinates": PointCoordinate3D(x=0.7, y=0.4, z=0.3)},
            {"label_ref": "poi_017", "coordinates": PointCoordinate3D(x=0.9, y=0.3, z=0.3)},
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
                instances_by_ref[ref] = keypoint_ontology_object.create_instance()

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
