from encord import EncordUserClient, Project

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)
project: Project = user_client.get_project("<workflows_project_hash>")

label_row = project.list_label_rows_v2()[0]
label_row.initialise_labels()
project.submit_label_row_for_review(label_row.label_hash)
