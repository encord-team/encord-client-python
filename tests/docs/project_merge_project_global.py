"""
Code Block Name: Merge Projects - Global
"""

# Import dependencies
from encord import EncordUserClient
from tqdm import tqdm

# Instantiate the client. Replace \<private_key_path> with the path to the file containing your private key
user_client = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path="<private_key_path>"
    )

# Specify Projects to merge 
project_hashes_to_merge = ["<project_hash-1>", "<project_hash-2>"] #Include as many Projects as you need

# Create target Project
def create_target_project(user_client, project_hashes_to_merge):
    dataset_hashes = set([])
    ontology_hash = ""

    for p_hash in project_hashes_to_merge:
        p = user_client.get_project(p_hash)
        new_dataset_hashes = {x['dataset_hash'] for x in p.datasets}
        if new_dataset_hashes.intersection(dataset_hashes):
            raise Exception(f'Source projects should not share datasets!')
        dataset_hashes.update(new_dataset_hashes)

        if not ontology_hash:
            ontology_hash = p.ontology_hash
        elif ontology_hash != p.ontology_hash:
            raise Exception(f'All projects must share the same ontology but '
                            f'https://app.encord.com/projects/view/{p_hash}/summary. does not!')

    project_hash = user_client.create_project(
        "Merged Project",
        list(dataset_hashes),
        f"Merged Projects: {project_hashes_to_merge}",
        ontology_hash=ontology_hash
    )

    return user_client.get_project(project_hash)

# Main function
def main(project_hashes_to_merge):
    target_project = create_target_project(user_client, project_hashes_to_merge)

    for source_p_hash in project_hashes_to_merge:
        print(f'Merging in project {source_p_hash}')
        source_project = user_client.get_project(source_p_hash)
        for lr_s in tqdm(source_project.list_label_rows_v2()):
            matches = target_project.list_label_rows_v2(data_hashes=[lr_s.data_hash])
            if len(matches) != 1:
                print(f'Something went wrong, zero or multiple matches found {matches}')
                print(lr_s)
            assert len(matches) == 1
            lr_t = matches[0]
            lr_s.initialise_labels()
            lr_t.initialise_labels()

            for obj in lr_s.get_object_instances():
                lr_t.add_object_instance(obj.copy())

            for cl in lr_s.get_classification_instances():
                lr_t.add_classification_instance(cl.copy())
            lr_t.save()
    print('Done!')
    print(f'Access project on https://app.encord.com/projects/view/{target_project.project_hash}/summary')

# Run the main function
if __name__ == '__main__':
    main(project_hashes_to_merge)