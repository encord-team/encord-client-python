from encord import EncordUserClient, Project
from encord.project_ontology.classification_type import ClassificationType

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)
project: Project = user_client.get_project("<project_hash>")

success: bool = project.add_classification(
    "Animal",
    classification_type=ClassificationType.RADIO,
    required=True,
    options=["Cat", "Dog"],
)
print(success)
