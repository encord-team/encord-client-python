from pathlib import Path

from encord import EncordUserClient

# adapt the following line to your private key path
private_key_path = Path.home() / ".ssh" / "id_ed25519"

with private_key_path.open() as f:
    private_key = f.read()

user_client = EncordUserClient.create_with_ssh_private_key(private_key)

project_hash = "!!! USE YOUR PROJECT ID"
project = user_client.get_project(project_hash)

# Get all labels of tasks that have already been initiated.
label_hashes = []
for label_row in project.label_rows:
    # Trying to run `get_label_rows` on a label_row without a `label_hash` would fail.
    if label_row["label_hash"] is not None:
        label_hashes.append(label_row["label_hash"])

all_labels = project.get_label_rows(label_hashes)
print(all_labels)
