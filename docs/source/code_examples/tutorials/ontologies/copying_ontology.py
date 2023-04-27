from encord import EncordUserClient

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)

ontology = user_client.get_ontology("<ontology_hash>")
new_ontology = user_client.create_ontology(
    "copy ontology",
    description="<my ontology description>",
    structure=ontology.structure,
)
