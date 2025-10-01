"""
Code Block Name: Bounding Boxes Images/Videos - Basic
"""

from encord import EncordUserClient, Project
from encord.objects import Object, ObjectInstance
from encord.objects.coordinates import BoundingBoxCoordinates

# User imput
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"  # Replace with the file path to your SSH private key
PROJECT_ID = "00000000-0000-0000-0000-000000000000"  # Replace with the unique Project ID
BUNDLE_SIZE = 10

# Data unit titles in your Project.
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

# Find bounding box object "Cherries" in the ontology.
ontology_structure = project.ontology_structure
box_ontology_object: Object = ontology_structure.get_child_by_title(title="Cherries", type_=Object)
assert box_ontology_object is not None, "Bounding box object 'Cherries' not found in ontology."

# Initialise label rows
label_rows = {}
all_titles = [IMAGE_TITLE, IMG_GROUP_TITLE, IMG_SEQUENCE_TITLE, VIDEO_TITLE]

with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for title in all_titles:
        rows = project.list_label_rows_v2(data_title_eq=title)
        assert isinstance(rows, list), f"Expected list for '{title}', got {type(rows)}"
        if not rows:
            print(f"Skipping: No label row found for {title}")
            continue
        lr = rows[0]
        lr.initialise_labels(bundle=bundle)
        assert lr.ontology_structure is not None, f"Ontology not initialized for '{title}'"
        label_rows[title] = lr

# Coordinates for the bounding box
box = BoundingBoxCoordinates(height=0.35, width=0.35, top_left_x=0.1, top_left_y=0.1)

# Create instances and attach to frames
label_rows_to_save = []

# 1. One image > annotate frame 0
image_lr = label_rows.get(IMAGE_TITLE)
if image_lr is not None:
    inst: ObjectInstance = box_ontology_object.create_instance()
    inst.set_for_frames(coordinates=box, frames=0)
    image_lr.add_object_instance(inst)
    label_rows_to_save.append(image_lr)

# 2. One image group > annotate frame 0
img_group_lr = label_rows.get(IMG_GROUP_TITLE)
if img_group_lr is not None:
    inst: ObjectInstance = box_ontology_object.create_instance()
    inst.set_for_frames(coordinates=box, frames=0)
    img_group_lr.add_object_instance(inst)
    label_rows_to_save.append(img_group_lr)

# 3. One image sequence > annotate frame 0
img_sequence_lr = label_rows.get(IMG_SEQUENCE_TITLE)
if img_sequence_lr is not None:
    inst: ObjectInstance = box_ontology_object.create_instance()
    inst.set_for_frames(coordinates=box, frames=0)
    img_sequence_lr.add_object_instance(inst)
    label_rows_to_save.append(img_sequence_lr)

# 4. One video > reuse SAME instance across 3 consecutive frames (frames 100, 101, 102)
video_lr = label_rows.get(VIDEO_TITLE)
if video_lr is not None:
    inst: ObjectInstance = box_ontology_object.create_instance()
    consecutive_frames = [100, 101, 102]
    for f in consecutive_frames:
        inst.set_for_frames(coordinates=box, frames=f)
    video_lr.add_object_instance(inst)
    label_rows_to_save.append(video_lr)

# Save the label rows
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for lr in label_rows_to_save:
        lr.save(bundle=bundle)
        print(f"Saved label row for {lr.data_title}")

print("Done: created one bounding box on image, image group, image sequence, and 3 video frames.")
