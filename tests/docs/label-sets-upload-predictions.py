"""
Code Block Name: Label sets - Upload predictions and create a version
"""

from uuid import UUID

from encord.orm.label_set import LabelSetOrigin, ProjectSource, VersionJobDone, VersionJobFailed
from encord.user_client import EncordUserClient

SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"  # Replace with file path to your SSH private key
PROJECT_ID = "00000000-0000-0000-0000-000000000000"  # Replace with Project unique ID
BRANCH_NAME = "preds/model-7"  # One branch per model; the label set captures it
BUNDLE_SIZE = 100  # Customize as needed

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Specify Project
project = user_client.get_project(PROJECT_ID)
assert project is not None, f"Project with ID {PROJECT_ID} could not be loaded"

# 1. Initialise the label rows on the branch, creating a row where none exists yet
label_rows = project.list_label_rows_v2(branch_name=BRANCH_NAME)
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for label_row in label_rows:
        label_row.initialise_labels(bundle=bundle)

# 2. Replace what is on each row with this run's predictions and save
# initialise_labels() loads the previous run too, so clear it first or the version holds both runs.
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for label_row in label_rows:
        for object_instance in label_row.get_object_instances():
            label_row.remove_object(object_instance)
        for classification_instance in label_row.get_classification_instances():
            label_row.remove_classification(classification_instance)
        # Add the model's output to the row here, for example:
        # instance = project.ontology_structure.get_child_by_title("Car").create_instance()
        # instance.set_for_frames(BoundingBoxCoordinates(...), frames=0, confidence=0.93)
        # label_row.add_object_instance(instance)
        label_row.save(bundle=bundle)

# 3. Create a label set that reads the branch
label_set = user_client.create_label_set(
    "Model 7",
    sources=[ProjectSource(project_id=UUID(PROJECT_ID), branch_name=BRANCH_NAME)],
    origin=LabelSetOrigin.IMPORT,
)

# 4. Queue a frozen version of the predictions and wait for it
job_id = label_set.create_version_job("run 12")
job = label_set.get_version_job(job_id, timeout_seconds=600)
if isinstance(job, VersionJobDone):
    version = label_set.get_version(job.version_id)
    print(f"Version {version.version_number} holds {version.label_count} labels")
elif isinstance(job, VersionJobFailed):
    print(f"No version was created: {job.error}")
else:
    print(f"Still running; read it again later with get_version_job({job_id})")

# Later runs of the same model: repeat steps 1, 2 and 4 on the same branch and set; each run is a new version.
# A new model version gets its own branch and its own label set.
