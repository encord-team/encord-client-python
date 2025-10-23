"""
Code Block Name: Polylines PCD
"""

# Import dependencies

from encord import EncordUserClient, Project
from encord.objects import Object
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

# Get the ontology
ontology_structure = project.ontology_structure

# Find a polyline annotation object in the project ontology
polyline_ontology_object: Object = ontology_structure.get_child_by_title(title="Object of Interest", type_=Object)
assert polyline_ontology_object is not None, "Cuboid object 'Object of Interest' not found in ontology."

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
                instances_by_ref[ref] = polyline_ontology_object.create_instance()

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
