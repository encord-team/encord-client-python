from encord import EncordUserClient

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)


# Remove Group from Project
project = user_client.get_project("<project_hash>")
groups = user_client.list_groups()
for group in groups:
    if group.name == "TestGroup":
        project.remove_group(group.group_hash)


# Remove Group from Dataset
dataset = user_client.get_dataset("<dataset_hash>")
groups = user_client.list_groups()
for group in groups:
    if group.name == "TestGroup":
        dataset.remove_groups(group.group_hash)


# Remove Group from Ontology
ontology = user_client.get_ontology("<ontology_hash>")
groups = user_client.list_groups()
for group in groups:
    if group.name == "TestGroup":
        ontology.remove_group(group.group_hash)
