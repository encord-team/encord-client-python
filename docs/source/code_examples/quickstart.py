from encord import EncordUserClient, Project

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key_content>",
    password="<your_private_key_password_if_necessary>",
)

# Get the project
project_hash: str = next((p["project"]["project_hash"] for p in user_client.get_projects()))
project: Project = user_client.get_project(project_hash)

# Get the labels (from one label_row, not entire set of labels from the project).
label_hash: str = next((lr["label_hash"] for lr in project.get_project().label_rows if lr["label_hash"] is not None))
labels: dict = project.get_label_row(label_hash)
print(labels)
