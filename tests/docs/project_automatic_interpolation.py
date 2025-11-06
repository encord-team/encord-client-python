"""
Code Block Name: Automatic Interpolation
"""

# Import dependencies
from encord import EncordUserClient

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"
PROJECT_ID = "00000000-0000-0000-0000-000000000000"
DATA_UNIT_TITLE = "cherries-vid-001.mp4"
DATA_UNIT_ID = "00000000-0000-0000-0000-000000000000"  # The data_hash for the data unit
LABEL_ROW_ID = "00000000-0000-0000-0000-000000000000"  # The label_hash for the data unit
LABEL_ID = "noQksGhW"  # The objectHash for the label

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Open the project you want to work on by specifying the Project ID
project = user_client.get_project(PROJECT_ID)

# Get the label row for a specific data unit
label_row = project.get_label_row(LABEL_ROW_ID)

print(label_row)
# Prepare interpolation
key_frames = label_row["data_units"][DATA_UNIT_ID]["labels"]
objects_to_interpolate = [LABEL_ID]

# Run interpolation
interpolation_result = project.object_interpolation(key_frames, objects_to_interpolate)
print(interpolation_result)
