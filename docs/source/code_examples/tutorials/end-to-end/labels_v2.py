"""
Working with the LabelRowV2
===========================

DENIS: probably the code links not working will be the blocker for me using this tool.
DENIS: Think about having easy back links. Maybe one "setup" script, and then every section can be started
   from the setup.

The :class:`encord.objects.LabelRowV2` class is a wrapper around the Encord label row data format. It
provides a convenient way to read, create, and manipulate labels.

This is just an illustrative example.

.. figure:: /images/cvat_project_export.png

    Export Project.

"""

#%%
# Imports and authentication
# --------------------------
# First, import dependencies and authenticate a project manager.
from pathlib import Path
from typing import List

from encord import EncordUserClient, Project
from encord.objects import (
    Classification,
    LabelRowV2,
    Object,
    ObjectInstance,
    OntologyStructure,
)
from encord.objects.coordinates import BoundingBoxCoordinates
from encord.orm.project import Project as OrmProject

#%%
# .. note::
#
#   To interact with Encord, you need to authenticate a client. You can find more details
#   :ref:`here <authentication:User authentication>`.
#

# Authentication: adapt the following line to your private key path
private_key_path = Path.home() / ".ssh" / "id_ed25519"

with private_key_path.open() as f:
    private_key = f.read()

user_client = EncordUserClient.create_with_ssh_private_key(private_key)

# Find project to work with based on title.
project_orm: OrmProject = next((p["project"] for p in user_client.get_projects(title_eq="Your project name")))
project: Project = user_client.get_project(project_orm.project_hash)


#%%
# Get metadata around labels
# ------------------------------
#
# Sometimes you might want to inspect some metadata around the label rows, such as the label hash,
# when the label was created, the corresponding data hash, or the creation date of the label.

label_rows: List[LabelRowV2] = project.list_label_rows_v2()


for label_row in label_rows:
    print(f"Label hash: {label_row.label_hash}")
    print(f"Label created at: {label_row.created_at}")
    print(f"Annotation task status: {label_row.annotation_task_status}")

#%%
# Inspect the filters in :meth:`~encord.project.Project.list_label_rows_v2` to only get a subset of the label rows.
#
# You can find more examples around all the available read properties by inspecting the properties of the
# :class:`~encord.objects.LabelRowV2` class.
#
# Starting to read or write labels
# --------------------------------
#
# To start reading or writing labels, you need to call the :meth:`~encord.objects.LabelRowV2.initialise_labelling`
# method which will download the state of the label from the Encord server.
#
# Once this method has been called, you can create your first label.
# DENIS: think of creating a screenshot from the platform here.

first_label_row: LabelRowV2 = label_rows[0]

first_label_row.initialise_labelling()
# ^ Check the reference for possible arguments

# Once you have added new labels, you will need to call .save() to upload all labels to the server.
first_label_row.save()

#%%
# Creating/reading object instances
# ---------------------------------
# The :class:`encord.objects.LabelRowV2` class works with its corresponding ontology. If you add object instances
# or classification instances, these will be created from the ontology. You can read more about object instances
# here: https://docs.encord.com/ontologies/use/#objects
#
# Defining the ontology object
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
ontology_structure: OntologyStructure = first_label_row.ontology_structure
box_ontology_object: Object = ontology_structure.get_item_by_title(title="Box of a human", type_=Object)
# ^ optionally specify the `type_` to narrow the return type and also have a runtime check.

# %%
# Creating and saving an object instance
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#

box_object_instance: ObjectInstance = box_ontology_object.create_instance()

box_object_instance.set_for_frames(
    coordinates=BoundingBoxCoordinates(
        height=0.5,
        width=0.5,
        top_left_x=0.2,
        top_left_y=0.2,
    ),
    # Add the bounding box to the first frame
    frames=0,
)

# Link the object instance to the label row.
first_label_row.add_object_instance(box_object_instance)


first_label_row.save()  # Upload the label to the server

#%%
# Inspecting an object instance
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# You can now get all the object instances that are part of the label row.

# Check the get_object_instances optional filters for when you have many different object/classification instances.
all_object_instances: List[ObjectInstance] = first_label_row.get_object_instances()

assert all_object_instances[0] == box_object_instance

#%%
# Adding object instances to multiple frames.
# -------------------------------------------
#
# Sometimes, you might want to work with a video where a single object instance is present in multiple frames.
# For example, you are tracking a car across multiple frames. In this case you would create one
# object instance and place it on all the frames where it is present.
# If objects are never present in multiple frames, you would always create a new object instance for a new frame.

# Assume you have the coordinates of a single object for the first 3 frames of a video.
# These are indexed by frame number.
coordinates_per_frame = {
    3: BoundingBoxCoordinates(
        height=0.5,
        width=0.5,
        top_left_x=0.2,
        top_left_y=0.2,
    ),
    4: BoundingBoxCoordinates(
        height=0.5,
        width=0.5,
        top_left_x=0.3,
        top_left_y=0.3,
    ),
    5: BoundingBoxCoordinates(
        height=0.5,
        width=0.5,
        top_left_x=0.4,
        top_left_y=0.4,
    ),
}


# OPTION 1 - think in terms of "the frames per object instance"
box_object_instance_2: ObjectInstance = box_ontology_object.create_instance()

for frame_number, coordinates in coordinates_per_frame.items():
    box_object_instance_2.set_for_frames(coordinates=coordinates, frames=frame_number)

# OPTION 2 - think in terms of the "object instances per frame"
box_object_instance_3: ObjectInstance = box_ontology_object.create_instance()

for frame_view in first_label_row.get_frame_views():
    if frame_view.frame_number in coordinates_per_frame:
        frame_view.add_object_instance(
            object_instance=box_object_instance_3,
            coordinates=coordinates_per_frame[frame_view.frame_number],
        )


#%%
# Read access across multiple frames
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# As shown above with OPTION 1 and OPTION 2, you can think of the individual object instances and on which
# frames they are present or you can think of the individual frames and which objects they have.
# For a read access thinking of the individual frames can be particularly convenient.

for label_row_frame_view in first_label_row.get_frame_views():
    frame_number = label_row_frame_view.frame
    print(f"Frame number: {frame_number}")
    object_instances_in_frame: List[ObjectInstance] = label_row_frame_view.get_object_instances()
    for object_instance in object_instances_in_frame:
        print(f"Object instance: {object_instance}")
        object_instance_frame_view = object_instance.get_frame_view(frame=frame_number)
        print(f"Coordinates: {object_instance_frame_view.coordinates}")


#%%
# Working with a classification instance
# ---------------------------------------------
#
# Creating a classification instance is similar to creating an object instance. The only differences are that you
# cannot create have more than one classification instance of the same type on the same frame and that there is
# no coordinates to be set for classification instances.
#
# You can read more about classification instances here: https://docs.encord.com/ontologies/use/#classifications
#
# Get the ontology object
# ^^^^^^^^^^^^^^^^^^^^^^^^

# Assume that the following text classification exists in the ontology.
text_ontology_classification: Classification = ontology_structure.get_item_by_title(
    title="Free text about the frame", type_=Classification
)
text_classification_instance = text_ontology_classification.create_instance()


#
# Add the classification instance to the label row
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# First set the value of the classification instance
text_classification_instance.set_answer(answer="This is a text classification.")

# Then add it to the label row
first_label_row.add_classification_instance(text_classification_instance)

#
# Read classification instances
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# Check the convenient filters of get_classification_instances() for your use cases
all_classification_instances = first_label_row.get_classification_instances()
assert all_classification_instances[0] == text_classification_instance

# * set/read answers for objects or classifications
# * set/read dynamic answers.
