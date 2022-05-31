from encord import EncordUserClient, ProjectManager

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key("<your_private_key>")
project_manager: ProjectManager = user_client.get_project_manager("<project_hash>")


success: bool = project_manager.remove_datasets(
    [
        "<dataset_hash1>",
        "<dataset_hash2>",
        # ...
    ]
)
print(success)
