"""
Code Block Name: Keypoints Images/Videos
"""

from encord import EncordUserClient, Project
from encord.objects import Object, ObjectInstance
from encord.objects.coordinates import PointCoordinate

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"  # Replace with the file path to your SSH private key
PROJECT_ID = "00000000-0000-0000-0000-000000000000"  # Replace with the unique Project ID
BUNDLE_SIZE = 10

# Data unit titles in your Project
IMAGE_TITLE = "blueberries-001.jpg"
IMG_GROUP_TITLE = "blueberries-ig"
IMG_SEQUENCE_TITLE = "blueberries-is"
VIDEO_TITLE = "blueberries-vid-001.mp4"

# Ontology object title for your KEYPOINT object
KEYPOINT_OBJECT_TITLE = "Floral Axis"

# Authorize connection to Encord
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use domain="https://api.us.encord.com"
    domain="https://api.encord.com",
)

project: Project = user_client.get_project(PROJECT_ID)

# Find a KEYPOINT object in the ontology by title
ontology_structure = project.ontology_structure
keypoint_object: Object = ontology_structure.get_child_by_title(title=KEYPOINT_OBJECT_TITLE, type_=Object)
assert keypoint_object is not None, f"Keypoint object '{KEYPOINT_OBJECT_TITLE}' not found in ontology."

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

# Keypoint coordinates: A single point roughly near the centre
kp = PointCoordinate(0.5, 0.5)

# Create instances and attach to frames
label_rows_to_save = []

# 1. One image > frame 0
image_lr = label_rows.get(IMAGE_TITLE)
if image_lr is not None:
    inst: ObjectInstance = keypoint_object.create_instance()
    inst.set_for_frames(coordinates=kp, frames=0)
    image_lr.add_object_instance(inst)
    label_rows_to_save.append(image_lr)

# 2. One image group > frame 0
img_group_lr = label_rows.get(IMG_GROUP_TITLE)
if img_group_lr is not None:
    inst: ObjectInstance = keypoint_object.create_instance()
    inst.set_for_frames(coordinates=kp, frames=0)
    img_group_lr.add_object_instance(inst)
    label_rows_to_save.append(img_group_lr)

# 3. One image sequence > frame 0
img_sequence_lr = label_rows.get(IMG_SEQUENCE_TITLE)
if img_sequence_lr is not None:
    inst: ObjectInstance = keypoint_object.create_instance()
    inst.set_for_frames(coordinates=kp, frames=0)
    img_sequence_lr.add_object_instance(inst)
    label_rows_to_save.append(img_sequence_lr)

# 4. One video > reuse SAME instance across 3 consecutive frames (frames 100, 101, 102)
video_lr = label_rows.get(VIDEO_TITLE)
if video_lr is not None:
    inst: ObjectInstance = keypoint_object.create_instance()
    for f in [100, 101, 102]:
        inst.set_for_frames(coordinates=kp, frames=f)
    video_lr.add_object_instance(inst)
    label_rows_to_save.append(video_lr)

# Save label rows
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for lr in label_rows_to_save:
        lr.save(bundle=bundle)
        print(f"Saved label row for {lr.data_title}")

print("Done: created one keypoint on image, image group, image sequence, and 3 video frames.")
