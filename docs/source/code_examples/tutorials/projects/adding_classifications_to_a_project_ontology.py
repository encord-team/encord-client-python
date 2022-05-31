from encord import EncordUserClient, ProjectManager
from encord.project_ontology.classification_type import ClassificationType

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key("<your_private_key>")
project_manager: ProjectManager = user_client.get_project_manager("<project_hash>")

success: bool = project_manager.add_classification(
    "Animal",
    classification_type=ClassificationType.RADIO,
    required=True,
    options=["Cat", "Dog"],
)
print(success)
