"""
Working with the LabelRowV2
===========================

DENIS: Think about having easy back links. Maybe one "setup" script, and then every section can be started
   from the setup.

The :class:`encord.objects.LabelRowV2` class is a wrapper around the Encord label row data format. It
provides a convenient way to read, create, and manipulate labels.
"""

#%%
# Imports and authentication
# --------------------------
# First, import dependencies and authenticate a project manager.
from pathlib import Path
from typing import List

from encord import EncordUserClient, Project
from encord.objects import (
    AnswerForFrames,
    Classification,
    LabelRowV2,
    Object,
    ObjectInstance,
    OntologyStructure,
    RadioAttribute,
)
from encord.objects.coordinates import BoundingBoxCoordinates
from encord.objects.utils import Range
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

first_label_row: LabelRowV2 = label_rows[0]

first_label_row.initialise_labels()
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


#%%
# Add the classification instance to the label row
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# First set the value of the classification instance
# DENIS: show how you place it on frames.
text_classification_instance.set_answer(answer="This is a text classification.")

# Then add it to the label row
first_label_row.add_classification_instance(text_classification_instance)

#%%
# Read classification instances
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# Check the convenient filters of get_classification_instances() for your use cases
all_classification_instances = first_label_row.get_classification_instances()
assert all_classification_instances[0] == text_classification_instance

#%%
# Working with object/classification instance attributes
# ------------------------------------------------------
#
# Both object instances and classification instances can have attributes. You can read more about examples
# using these links: https://docs.encord.com/annotate/editor/images#frame-classification and
# https://docs.encord.com/annotate/editor/images#frame-classification
#
# In the ontology you might have already configured text, radio, or checklist attributes for your object/classification.
# With the LabelRowV2, you can set or get the values of these attributes. Here, we refer to as "setting or getting an
# answer to an attribute".
#
# Answering classification instance attributes
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# The case for answering classification instance attributes is simpler, so let's start with those.
#
# You will again need to deal with the original ontology object to interact with answers to attributes. We have
# exposed convenient accessors to find the right attributes to get the attributes or the respective options by
# their title.
#
# .. note::
#
#     When working with attributes, you will see that the first thing to do is often to grab the ontology object.
#     Usually, when calling the `get_item_by_title` the `type_` is recommended, but still optional. However, for
#     classifications this is often required.
#
#     The reason is that the classification title is always equal to the title of the top level attribute of this
#     classification. Therefore, it is important to distinguish what exactly you're trying to search for.
#
# Text attributes
# """""""""""""""
#
# Answering text attributes is the simplest case and has already been shown in the section on classification instances
# above.

# Assume that the following text classification exists in the ontology.
text_ontology_classification: Classification = ontology_structure.get_item_by_title(
    title="Free text about the frame",
    # Do not forget to specify the type here
    type_=Classification,
)
text_classification_instance = text_ontology_classification.create_instance()

# First set the value of the classification instance
text_classification_instance.set_answer(answer="This is a text classification.")

assert text_classification_instance.get_answer() == "This is a text classification."

# %%
# We encourage you to read the `set_answer` and `get_answer` docstrings to understand the different behaviours and
# possible options which you can set.
#
# Checklist attributes
# """"""""""""""""""""
#
# Assume we have a checklist with "all colours in the picture" which defines a bunch of colours that we can
# see in the image. You will need to get all the options from the checklist ontology that you would like to
# select as answers.

checklist_ontology_classification: Classification = ontology_structure.get_item_by_title(
    title="All colours in the picture",
    # Do not forget to specify the type here
    type_=Classification,
)
checklist_classification_instance = checklist_ontology_classification.create_instance()

# Prefer using the `checklist_ontology_classification` over the `ontology_structure` to get the options.
# The more specific the ontology item that you're searching from is, the more likely you will avoid title clashes.
green_option = checklist_ontology_classification.get_item_by_title(
    "Green"
)  # DENIS: make it work with type: Option (so ppl don't have to write FlatOption.
blue_option = checklist_ontology_classification.get_item_by_title("Blue")

checklist_classification_instance.set_answer([green_option, blue_option])

assert sorted(checklist_classification_instance.get_answer()) == sorted([green_option, blue_option])

# %%
# Radio attributes
# """"""""""""""""
#
# Let's assume we have a radio classification called "Scenery" with the options "Mountains", "Ocean", and "Desert".

scenery_ontology_classification: Classification = ontology_structure.get_item_by_title(
    title="Scenery",
    # Do not forget to specify the type here
    type_=Classification,
)

mountains_option = scenery_ontology_classification.get_item_by_title(title="Mountains")

darkness_classification_instance = scenery_ontology_classification.create_instance()

darkness_classification_instance.set_answer(mountains_option)

assert darkness_classification_instance.get_answer() == mountains_option

# %%
# Radio attributes can also be nested. You can read more about nested options here:
# https://docs.encord.com/ontologies/use/#nested-classifications
#
# Let's say that if you have the Mountains scenery, there is an additional radio classification called "Mountains count"
# with the answers "One", "Two", and "Many". Continuing the example above, you can set the nested answer like this:

mountains_count_attribute = mountains_option.get_item_by_title("Mountains count")
two_mountains_option = mountains_count_attribute.get_item_by_title("Two")

darkness_classification_instance.set_answer(two_mountains_option)

# Note, that if for `set_answer` or `get_answer` the attribute of the classification cannot be inferred, we need
# to manually specify it.
# DENIS: this is not darkness anymore!
assert darkness_classification_instance.get_answer(attribute=mountains_count_attribute) == two_mountains_option

# %%
# Answering object instance attributes
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# Setting answers on object instances is almost identical to setting answers on classification instances.
# You will need to possibly get the attribute, but also the answer options from the ontology.

car_ontology_object: Object = ontology_structure.get_item_by_title("Car")
car_brand_attribute = car_ontology_object.get_item_by_title(title="Car brand", type_=RadioAttribute)
# Again, doing ontology_structure.get_item_by_title("Mercedes") is also possible, but might be more ambiguous.
mercedes_option = car_brand_attribute.get_item_by_title(title="Mercedes")

car_object_instance = car_ontology_object.create_instance()

car_object_instance.set_answer(mercedes_option)

# The attribute cannot be inferred, so we need to specify it.
assert car_object_instance.get_answer(attribute=car_brand_attribute) == mercedes_option

# %%
# Setting answers for dynamic attributes
# --------------------------------------
#
# Dynamic attributes are attributes for object instances where the answer can change in each frame.
# You can read more about them here: https://docs.encord.com/annotate/editor/videos/#dynamic-classification
#
# These behave very similarly to static attributes, however, they expect that a frame is passed to the `set_answer`
# which will set the answer for the specific frame.
#
# The read access, however, behaves slightly different to show which answers have been set for which frames.

person_ontology_object: Object = ontology_structure.get_item_by_title("Person", type_=Object)

position_attribute = person_ontology_object.get_item_by_title(
    title="Position",  # The options here are "Standing" or "Walking"
    type_=RadioAttribute,
)

person_object_instance = person_ontology_object.create_instance()

# Assume you would add the right coordinates of this person for frames 0-10 here.
# Now assume the person is standing in frames 0-5 and walking in frames 6-10.

person_object_instance.set_answer(
    answer=position_attribute.get_item_by_title("Standing"),
    frames=Range(start=0, end=5),
    # Wherever you can set frames, you can either set a single int, a Range, or a list of Range.
)

person_object_instance.set_answer(
    answer=position_attribute.get_item_by_title("Walking"),
    frames=Range(start=6, end=10),
)

# DENIS: make sure that we refer to all the Range helpers.
assert person_object_instance.get_answer(attribute=position_attribute) == [
    AnswerForFrames(
        answer=position_attribute.get_item_by_title("Standing"),
        ranges=[Range(start=0, end=5)],
    ),
    AnswerForFrames(
        answer=position_attribute.get_item_by_title("Walking"),
        ranges=[Range(start=6, end=10)],
    ),
]


# * set/read dynamic answers. https://docs.encord.com/annotate/editor/videos/#dynamic-classification
# DENIS: show how to set the manual_annotation for example.
# DENIS: provide an actual reference ontology where all of these examples would work.
