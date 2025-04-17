"""
Code Block Name: Split Projects
"""

# import dependencies
from encord import EncordUserClient, Project
from encord.objects import LabelRowV2
from pathlib import Path
from typing import List

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"
PROJECT_ID = "f8b81f75-d1d5-4cb8-895b-44db9957392e"
PROJECT_SIZE = 50  # Specify the size Project first project
START_NUMBER = 100  # Specify the start number of the second project


# Prepare target Projects
def get_destination_projects(
    user_client: EncordUserClient, source_project: Project, n_target_projects: int
) -> List[Project]:
    dest_project_ids = []
    for idx in range(n_target_projects):
        target_title = source_project.title + f" slice {idx + 1}"
        if found_projects := user_client.get_projects(title_eq=target_title):
            if len(found_projects) > 1:
                print(
                    f"A few projects with name {target_title} found. Can't proceed, as target name should be unique."
                )
                exit(1)
            if found_projects:
                dest_project_id = found_projects[0]["project"]["project_hash"]
                dest_project_ids.append(dest_project_id)
                continue
        dest_project_id = source_project.copy_project(
            copy_datasets=True, copy_collaborators=True, new_title=target_title
        )
        dest_project_ids.append(dest_project_id)

    print(f"Destination project ids: {dest_project_ids}")
    return [user_client.get_project(project_hash=p) for p in dest_project_ids]


# Prepare data for new Projects
def get_destination_label_row(destination_project: Project, data_hash: str) -> LabelRowV2:
    result = destination_project.list_label_rows_v2(data_hashes=[data_hash])
    if not result:
        print("No such data hash in the destination project, something wrong!")
        exit(1)
    return result[0]


# The main function. Substitute your variables here
def main(
    ssh_key: str = SSH_PATH,
    source_project: str = PROJECT_ID,
    target_project_size: int = PROJECT_SIZE,
    continue_from: int = START_NUMBER,
):
    user_client = EncordUserClient.create_with_ssh_private_key(ssh_private_key_path=ssh_key)

    project = user_client.get_project(project_hash=source_project)
    n_items = len(project.list_label_rows_v2())
    n_target_projects = int(n_items / target_project_size) + 1

    print(f"Project {project.title} has {n_items} entries.")
    if n_target_projects < 2:
        print("Nothing to do!")
        exit(0)
    print(f"Splitting source project into {n_target_projects} of size {target_project_size}")

    destination_projects = get_destination_projects(user_client, project, n_target_projects)

    source_label_rows = project.list_label_rows_v2()
    for idx, (src_label_row, destination_project) in enumerate(
        zip(source_label_rows, [p for p in destination_projects for _ in range(target_project_size)])
    ):
        if continue_from > idx:
            continue

        src_label_row.initialise_labels()

        dst_label_row = get_destination_label_row(destination_project, src_label_row.data_hash)
        dst_label_row.initialise_labels()

        src = src_label_row.to_encord_dict()

        dst = dst_label_row.to_encord_dict()
        dst["object_answers"] = src["object_answers"]
        dst["classification_answers"] = src["classification_answers"]
        dst["object_actions"] = src["object_actions"]
        dst["data_units"] = src["data_units"]

        dst_label_row.from_labels_dict(dst)
        dst_label_row.save()
        print(
            f"{idx + 1}/{len(source_label_rows)}: '{src_label_row.data_title}' labels copied to project {destination_project.title}"
        )


# Run the main function
if __name__ == "__main__":
    main(
        ssh_key=SSH_PATH,
        source_project=PROJECT_ID,
        target_project_size=PROJECT_SIZE,
        continue_from=START_NUMBER,
    )
