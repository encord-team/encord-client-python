"""
Code Block Name: Manual QA to Workflow - Global
"""

# Import dependencies
import logging
import time
from typing import List, Optional

from tqdm import tqdm

from encord import EncordUserClient, Project


# Create target workflow Project
def create_target_project(
    user_client: EncordUserClient,
    source_project_hash: str,
    target_project_name: str,
    workflow_template_hash: str,
) -> Project:
    # Retrieve all the required information you need to create your target project from the source Project
    source_p = user_client.get_project(source_project_hash)
    source_dataset_hashes = {x["dataset_hash"] for x in source_p.datasets}
    ontology_hash = source_p.ontology_hash

    target_project_hash: str = user_client.create_project(
        target_project_name,
        list(source_dataset_hashes),
        ontology_hash=ontology_hash,
        workflow_template_hash=workflow_template_hash,
    )

    return user_client.get_project(target_project_hash)


# Migrate Projects using bundles to facilitate the migration of large Projects
def process_by_bundle(
    source_project: Project,
    target_project: Project,
    bundle_size: int = 100,
    feature_hashes_to_include: Optional[List[str]] = None,
) -> List[str]:
    new_problematic_label_rows = []
    all_source_label_rows = source_project.list_label_rows_v2()

    all_batches = [
        all_source_label_rows[i : i + bundle_size] for i in range(0, len(all_source_label_rows), bundle_size)
    ]
    for source_rows_batch in tqdm(all_batches):
        source_bundle = source_project.create_bundle()
        for label_row_s in source_rows_batch:
            if feature_hashes_to_include:
                label_row_s.initialise_labels(
                    include_object_feature_hashes=set(feature_hashes_to_include),
                    bundle=source_bundle,
                )
            else:
                label_row_s.initialise_labels(
                    bundle=source_bundle,
                )

        source_bundle.execute()

        target_label_rows = {}
        target_bundle = target_project.create_bundle()
        for label_row_s in source_rows_batch:
            matches = target_project.list_label_rows_v2(data_hashes=[label_row_s.data_hash])
            if len(matches) != 1:
                logging.info(f"Something went wrong, zero or multiple matches found {matches}")
                # Track problematic label rows
                new_problematic_label_rows.append(label_row_s.data_hash)
                continue
            label_row_t = matches[0]
            label_row_t.initialise_labels(bundle=target_bundle, overwrite=True)
            target_label_rows[label_row_s.data_hash] = label_row_t
        target_bundle.execute()

        target_bundle = target_project.create_bundle()

        for label_row_s in source_rows_batch:
            label_row_t = target_label_rows[label_row_s.data_hash]
            label_row_s_status = label_row_s.annotation_task_status
            if label_row_s_status == "COMPLETED":
                label_row_t.workflow_complete()

            for obj in label_row_s.get_object_instances():
                label_row_t.add_object_instance(obj.copy())

            for cl in label_row_s.get_classification_instances():
                label_row_t.add_classification_instance(cl.copy())
            label_row_t.save(bundle=target_bundle)
        target_bundle.execute()

    return new_problematic_label_rows


# Define the main function
def main(
    keyfile: str,
    source_project_hash: str,
    target_project_name: str,
    workflow_template_hash: str,
    bundle_size: int = 50,
    feature_hashes_to_include: Optional[List[str]] = None,
):
    user_client = EncordUserClient.create_with_ssh_private_key(ssh_private_key_path=keyfile)
    target_project = create_target_project(
        user_client, source_project_hash, target_project_name, workflow_template_hash
    )
    source_project = user_client.get_project(source_project_hash)

    # Process label rows by bundle
    problematic_label_rows = process_by_bundle(source_project, target_project, bundle_size, feature_hashes_to_include)

    # Write problematic label rows to a log file
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    sanitized_project_name = target_project_name.replace(" ", "_")
    log_filename = f"problematic_label_rows_log_{sanitized_project_name}_{timestamp}.txt"
    with open(log_filename, "w") as log_file:
        for data_hash in problematic_label_rows:
            log_file.write(f"{data_hash}\n")
    print("Done!")
    print(f"Access project on https://app.encord.com/projects/view/{target_project.project_hash}/summary")


# Run the main function. Insert your parameters here
if __name__ == "__main__":
    keyfile = "<private_key_path>"
    source_project_hash = "<source_project_hash>"
    target_project_name = "<target_project_name>"
    workflow_template_hash = "<workflow_template_hash> "
    bundle_size = 50
    feature_hashes_to_include = None

    main(
        keyfile,
        source_project_hash,
        target_project_name,
        workflow_template_hash,
        bundle_size,
        feature_hashes_to_include,
    )
