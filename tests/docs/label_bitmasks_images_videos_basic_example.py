"""
Code Block Name: Bitmasks Images/Videos - Basic
"""

from encord import EncordUserClient, Project
from encord.objects import Object, ObjectInstance
from encord.objects.coordinates import BitmaskCoordinates
import numpy as np

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"  # Replace with your SSH private key
PROJECT_ID = "00000000-0000-0000-0000-000000000000"   # Replace with your Project ID
BUNDLE_SIZE = 10

# Data unit titles in your Project
IMAGE_TITLE = "apples-001.jpg"
IMG_GROUP_TITLE = "apples-ig"
IMG_SEQUENCE_TITLE = "apples-is"
VIDEO_TITLE = "apples-vid-001.mp4"

# Fixed frame size
FRAME_H, FRAME_W = 1080, 1920

# Authorize connection to Encord
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use domain="https://api.us.encord.com"
    domain="https://api.encord.com",
)

project: Project = user_client.get_project(PROJECT_ID)

# Find the bitmask object "Apples" in the ontology
ontology_structure = project.ontology_structure
bitmask_ontology_object: Object = ontology_structure.get_child_by_title(title="Apples", type_=Object)
assert bitmask_ontology_object is not None, "Bitmask object 'Apples' not found in ontology."

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

# Prepare boolean masks with shape matching frame size
mask_a_arr = np.ones((FRAME_H, FRAME_W), dtype=bool)
assert mask_a_arr.shape == (FRAME_H, FRAME_W), "Mask dimensions must match 1080x1920"

mask_b_arr = np.zeros((FRAME_H, FRAME_W), dtype=bool)
mask_b_arr[0:FRAME_H//3, 0:FRAME_W//3] = True
assert mask_b_arr.shape == (FRAME_H, FRAME_W), "Mask dimensions must match 1080x1920"

mask_c_arr = np.zeros((FRAME_H, FRAME_W), dtype=bool)
mask_c_arr[FRAME_H//4:FRAME_H//2, FRAME_W//4:FRAME_W//2] = True
assert mask_c_arr.shape == (FRAME_H, FRAME_W), "Mask dimensions must match 1080x1920"

mask_a = BitmaskCoordinates(mask_a_arr)
mask_b = BitmaskCoordinates(mask_b_arr)
mask_c = BitmaskCoordinates(mask_c_arr)

# Create instances and attach to frames
label_rows_to_save = []

# 1. One image > annotate frame 0
image_lr = label_rows.get(IMAGE_TITLE)
if image_lr is not None:
    inst: ObjectInstance = bitmask_ontology_object.create_instance()
    inst.set_for_frames(coordinates=mask_a, frames=0, manual_annotation=True)
    image_lr.add_object_instance(inst)
    label_rows_to_save.append(image_lr)

# 2. One image group > annotate frame 0
img_group_lr = label_rows.get(IMG_GROUP_TITLE)
if img_group_lr is not None:
    inst: ObjectInstance = bitmask_ontology_object.create_instance()
    inst.set_for_frames(coordinates=mask_b, frames=0, manual_annotation=True)
    img_group_lr.add_object_instance(inst)
    label_rows_to_save.append(img_group_lr)

# 3. One image sequence > annotate frame 0
img_sequence_lr = label_rows.get(IMG_SEQUENCE_TITLE)
if img_sequence_lr is not None:
    inst: ObjectInstance = bitmask_ontology_object.create_instance()
    inst.set_for_frames(coordinates=mask_c, frames=0, manual_annotation=True)
    img_sequence_lr.add_object_instance(inst)
    label_rows_to_save.append(img_sequence_lr)

# 4. One video > reuse SAME instance across 3 consecutive frames (100, 101, 102)
video_lr = label_rows.get(VIDEO_TITLE)
if video_lr is not None:
    inst: ObjectInstance = bitmask_ontology_object.create_instance()
    for f, bm in zip([100, 101, 102], [mask_a, mask_b, mask_c]):
        inst.set_for_frames(coordinates=bm, frames=f, manual_annotation=True)
    video_lr.add_object_instance(inst)
    label_rows_to_save.append(video_lr)

# Save label rows
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for lr in label_rows_to_save:
        lr.save(bundle=bundle)
        print(f"Saved label row for {lr.data_title}")

print("Done: created bitmasks on image, image group, image sequence, and 3 video frames for 'Apples'.")
