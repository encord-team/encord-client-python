"""
Preparing your data for labelling
=================================

This example shows you how to go from your raw data to a project with your label
structure (ontology) defined, your dataset attached, and ready to be labelled.

Imports
--------------
"""
# sphinx_gallery_thumbnail_path = 'images/end-to-end-thumbs/product-image.svg'

from pathlib import Path

from encord import EncordUserClient
from encord.project import Project
from encord.dataset import Dataset
from encord.orm.dataset import CreateDatasetResponse, StorageLocation
from encord.project_ontology.classification_type import ClassificationType
from encord.project_ontology.object_type import ObjectShape
from encord.utilities.project_user import ProjectUserRole

#%%
# Authenticating
# --------------
# To interact with Encord, you need to authenticate a client. You can find more details
# :ref:`here <authentication:Authentication>`.

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key("<your_private_key>")

#%%
# 1. Creating and populating the dataset
# --------------------------------------
# This section shows how to create a dataset and add both videos and images to the
# dataset.

# Create the dataset
dataset_response: CreateDatasetResponse = user_client.create_dataset("Example Title", StorageLocation.CORD_STORAGE)
dataset_hash = dataset_response.dataset_hash

# Add data to the dataset
dataset: Dataset = user_client.get_dataset(dataset_hash)

image_files = sorted([p.as_posix() for p in Path("path/to/images").iterdir() if p.suffix in {".jpg", ".png"}])
dataset.create_image_group(image_files)

video_files = [p.as_posix() for p in Path("path/to/videos").iterdir() if p.suffix in {".mp4", ".webm"}]

for v in video_files:
    dataset.upload_video(v)

#%%
# 2. Listing available data in the dataset
# ----------------------------------------

for data_row in dataset.data_rows:
    print(f"data-hash: '{data_row.uid}', " f"data-type: {data_row.data_type}, " f"title: '{data_row.title}'")

#%%
# The code will produce an output similar to the following:
#
# .. code-block:: text
#
#     data-hash: '<data_hash>', data-type: DataType.IMG_GROUP, title: 'image-group-68dd3'
#     data-hash: '<data_hash>', data-type: DataType.VIDEO, title: 'video1.mp4'
#

#%%
# 3. Creating project with an ontology
# ------------------------------------

# == Creating a project containing the dataset created above == #
project_hash = user_client.create_project(
    project_title="The title of the project",
    dataset_hashes=[dataset_hash],
    project_description="A description of what this project is all about.",
)

# == Adding objects and classifications to the project ontology == #
project: Project = user_client.get_project(project_hash)

# Objects
project.add_object(name="Dog (polygon)", shape=ObjectShape.POLYGON)
project.add_object(name="Snake (polyline)", shape=ObjectShape.POLYLINE)
project.add_object(name="Tiger (bounding_box)", shape=ObjectShape.BOUNDING_BOX)
project.add_object(name="Ant (key-point)", shape=ObjectShape.KEY_POINT)

# Classifications
project.add_classification(
    name="Has Animal (radio)",
    classification_type=ClassificationType.RADIO,
    required=True,
    options=["yes", "no"],
)
project.add_classification(
    name="Other objects (checklist)",
    classification_type=ClassificationType.CHECKLIST,
    required=False,
    options=["person", "car", "leash"],
)
project.add_classification(
    name="Description (text)",
    classification_type=ClassificationType.TEXT,
    required=False,
    # Note no `options` defined for text classifications.
)

#%%
# 4. Adding your team to the project
# ----------------------------------
# To allow annotators, reviewers and team managers to access your project, they need to
# be added to the project by their emails (Encord accounts). You add each type of member
# by one call to the project client each:

project.add_users(
    ["annotator1@your.domain", "annotator2@your.domain"],
    user_role=ProjectUserRole.ANNOTATOR,
)
project.add_users(
    ["reviewer1@your.domain", "reviewer2@your.domain"],
    user_role=ProjectUserRole.REVIEWER,
)
project.add_users(
    ["annotator_reviewer@your.domain"],
    user_role=ProjectUserRole.ANNOTATOR_REVIEWER,
)
project.add_users(
    ["team_manager@your.domain"],
    user_role=ProjectUserRole.TEAM_MANAGER,
)

#%%
# At this point, your data is ready to be annotated with the project-specific
# information defined in the project ontology.
