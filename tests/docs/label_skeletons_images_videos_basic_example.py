"""
Code Block Name: Primatives Images/Videos
"""

from encord import EncordUserClient, Project
from encord.objects import Object, ObjectInstance
from encord.objects.coordinates import SkeletonCoordinate, SkeletonCoordinates
from encord.objects.skeleton_template import SkeletonTemplate

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"  # Replace with the file path to your SSH private key
PROJECT_ID = "00000000-0000-0000-0000-000000000000"  # Replace with the unique Project ID
BUNDLE_SIZE = 10

IMAGE_TITLE = "cherries-001.jpg"
IMG_GROUP_TITLE = "cherries-ig"
IMG_SEQUENCE_TITLE = "cherries-is"
VIDEO_TITLE = "cherries-vid-001.mp4"

# Authorize connection to Encord
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use domain="https://api.us.encord.com"
    domain="https://api.encord.com",
)

project: Project = user_client.get_project(PROJECT_ID)

# Ontology pieces
ontology = project.ontology_structure
skeleton_object: Object = ontology.get_child_by_title(title="Strawberries", type_=Object)
assert skeleton_object is not None, "Ontology object 'Strawberries' not found."

# The primitive template your object uses
assert "Triangle" in ontology.skeleton_templates, "Skeleton template 'Triangle' not found in ontology."
template: SkeletonTemplate = ontology.skeleton_templates["Triangle"]

# Grab the point ids defined by the template
point_ids = [pt.feature_hash for pt in template.skeleton.values()]
assert len(point_ids) >= 3, "Template 'Triangle' should have at least 3 points."

# Coordinate set
tri_coords = SkeletonCoordinates(
    values=[
        SkeletonCoordinate(x=0.30, y=0.30, name="point_0", color="#000000", value="point_0", feature_hash=point_ids[0]),
        SkeletonCoordinate(x=0.45, y=0.30, name="point_1", color="#000000", value="point_1", feature_hash=point_ids[1]),
        SkeletonCoordinate(x=0.35, y=0.45, name="point_2", color="#000000", value="point_2", feature_hash=point_ids[2]),
    ],
    name="Triangle",
)

# Initialize label rows
label_rows = {}
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for title in [IMAGE_TITLE, IMG_GROUP_TITLE, IMG_SEQUENCE_TITLE, VIDEO_TITLE]:
        rows = project.list_label_rows_v2(data_title_eq=title)
        assert isinstance(rows, list), f"Expected list for '{title}', got {type(rows)}"
        if not rows:
            print(f"Skipping: No label row found for {title}")
            continue
        lr = rows[0]
        lr.initialise_labels(bundle=bundle)
        assert lr.ontology_structure is not None, f"Ontology not initialized for '{title}'"
        label_rows[title] = lr

# Create one skeleton instance per data unit and assign frames
to_save = []

# 1. One image > frame 0
lr = label_rows.get(IMAGE_TITLE)
if lr:
    inst: ObjectInstance = skeleton_object.create_instance()
    inst.set_for_frames(coordinates=tri_coords, frames=0)
    lr.add_object_instance(inst)
    to_save.append(lr)

# 2. One image group > frame 0
lr = label_rows.get(IMG_GROUP_TITLE)
if lr:
    inst: ObjectInstance = skeleton_object.create_instance()
    inst.set_for_frames(coordinates=tri_coords, frames=0)
    lr.add_object_instance(inst)
    to_save.append(lr)

# 3. One image sequence > frame 0
lr = label_rows.get(IMG_SEQUENCE_TITLE)
if lr:
    inst: ObjectInstance = skeleton_object.create_instance()
    inst.set_for_frames(coordinates=tri_coords, frames=0)
    lr.add_object_instance(inst)
    to_save.append(lr)

# 4. One video > reuse same instance across 3 consecutive frames
lr = label_rows.get(VIDEO_TITLE)
if lr:
    inst: ObjectInstance = skeleton_object.create_instance()
    for f in [100, 101, 102]:
        inst.set_for_frames(coordinates=tri_coords, frames=f)
    lr.add_object_instance(inst)
    to_save.append(lr)

# Save label rows
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for lr in to_save:
        lr.save(bundle=bundle)
        print(f"Saved label row for {lr.data_title}")

print("Done: placed a minimal 'Strawberries' skeleton (Triangle) on image, image group, image sequence, and 3 video frames.")
