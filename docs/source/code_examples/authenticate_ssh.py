from pathlib import Path

from encord import Dataset, EncordUserClient, Project

# adapt the following line to your private key path
private_key_path = Path.home() / ".ssh" / "id_ed25519"

with private_key_path.open() as f:
    private_key = f.read()

user_client = EncordUserClient.create_with_ssh_private_key(private_key)
project: Project = user_client.get_project("<project_id>")
dataset: Dataset = user_client.get_dataset("<dataset_id>")
