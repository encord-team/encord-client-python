from encord import EncordUserClient

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)


# List Project Groups
project = user_client.get_project("<project_hash>")
project_groups = project.get_groups()

print(project_groups)

# List Dataset Groups
dataset = user_client.get_dataset("<dataset_hash>")
dataset_groups = dataset.get_groups()

print(dataset_groups)


# List Ontology Groups
ontology = user_client.get_ontology("<ontology_hash>")
ontology_groups = ontology.get_groups()

print(ontology_groups)

