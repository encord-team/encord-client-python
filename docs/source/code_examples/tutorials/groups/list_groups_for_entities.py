from encord import EncordUserClient

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)


# List Project Groups
project = user_client.get_project("<project_hash>")
project_groups = project.list_groups()

print(project_groups)

# List Dataset Groups
dataset = user_client.get_dataset("<dataset_hash>")
dataset_groups = dataset.list_groups()

print(dataset_groups)


# List Ontology Groups
ontology = user_client.get_ontology("<ontology_hash>")
for ontology_group in ontology.list_groups():
    print(ontology_group)


