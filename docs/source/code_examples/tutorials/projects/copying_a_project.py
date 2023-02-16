from encord import EncordUserClient, Project

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)
project: Project = user_client.get_project("<project_hash>")


# Basic copy

new_project_hash: str = project.copy_project(
    copy_datasets=True,
    copy_collaborators=True,
    copy_models=False,  # Not strictly needed
)
print(new_project_hash)


# Advanced copy

from encord.orm.project import (
    CopyDatasetAction,
    CopyDatasetOptions,
    CopyLabelsOptions,
    ReviewApprovalState,
)

project.copy_project(
    new_title="foo",
    new_description="bar",
    copy_collaborators=True,
    copy_datasets=CopyDatasetOptions(
        action=CopyDatasetAction.CLONE,  # This will also create a new dataset
        dataset_title="baz",
        dataset_description="quz",
        datasets_to_data_hashes_map={
            "<dataset_hash>": ["<data_hash_1", "<data_hash_2"]
        },
    ),
    copy_labels=CopyLabelsOptions(
        accepted_label_statuses=[ReviewApprovalState.APPROVED],
        accepted_label_hashes=["<label_hash_1>", "<label_hash_2>"],
    ),
)
