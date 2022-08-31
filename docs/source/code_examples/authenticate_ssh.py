from os.path import expanduser

from encord import Dataset, EncordUserClient, Project

with open(expanduser("~/.ssh/private_key"), "r", encoding="utf-8") as f:
    private_key = f.read()

user_client = EncordUserClient.create_with_ssh_private_key(private_key)
project: Project = user_client.get_project("<project_id>")
dataset: Dataset = user_client.get_dataset("<dataset_id>")
