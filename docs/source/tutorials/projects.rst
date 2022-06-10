.. include:: ../substitutes.rst

********
Projects
********

The project tutorials are divided into a couple of subsets.
First, we show general concepts like creating a new project from the |sdk|.
Afterwards, we go into more detail such as working with attributes (e.g. labels),
and incorporating advanced features such as integrating our automation models and algorithms.
Make sure that you have associated a :xref:`public-private_key_pair` with |company| before you start.
If not you can do so by following the :ref:`authentication:Public key authentication` tutorial.

Creating a Project
==================

You can create a new project using the :meth:`create_project() <.EncordUserClient.create_project>` method that takes three parameters:

* :meth:`project_title <.EncordUserClient.create_project>`: the title of the project as a string

* :meth:`dataset_ids <.EncordUserClient.create_project>`: a list of ``<dataset_hash>`` strings for the datasets to add to the project.
  For more details on creating datasets, see :ref:`tutorials/datasets:Creating a dataset`.
  This can be set to an empty list

* :meth:`project_description <.EncordUserClient.create_project>`: the description of the project as a string.
  This parameter is optional

:meth:`create_project() <.EncordUserClient.create_project>` will return the ``<project_hash>`` of the created project.
The user that calls this method becomes the admin of the project.
The following shows the general structure for creating a project.

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/creating_a_project.py
            :language: python

    .. tab:: Example output

        .. code-block::

            "aaaaaaaa-bbbb-cccc-eeee-ffffffffffff"  # the <project_hash>



Copying a project
=================

Copying a project creates another project with the same ontology and settings [#F1]_.
You can also decide to copy over the same users, datasets and models (which aren't copied over by default).

The :meth:`copy_project() <encord.project.Project.copy_project>` method takes the following parameters, all of which are optional:

* :meth:`copy_datasets <encord.project.Project.copy_project>`: when set to ``True``, the datasets from the original project will be copied over and new tasks will be created from them
* :meth:`copy_collaborators <encord.project.Project.copy_project>`:  when set to ``True``, the collaborators from the original project will be copied over with their existing roles
* :meth:`copy_models <encord.project.Project.copy_project>`:  when set to ``True``, the models and their training data from the original project will be copied over

The parameters above are set to ``False`` by default, meaning you do not need to include any of them if you
do not want to copy that feature into your new project.

:meth:`copy_project <encord.project.Project.copy_project>` returns the ``<project_hash>`` of the new project.

Here is an example of copying a project:

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/copying_a_project.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            "00000000-bbbb-cccc-eeee-ffffffffffff"  # the <project_hash>


.. rubric:: Footnotes

.. [#f1] If you do not copy over the collaborators, then the reviewer and label mapping settings will not be copied over either.



Listing existing projects
=========================

You can query and list all the available projects of a given user.
In the example below, a user authenticates with |company| and then fetches all projects available.

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/listing_existing_projects.py
            :language: python

    .. tab:: Example output

        .. code-block::

            [
                {
                    "project": {
                        "created_at": datetime.datetime(...),
                        "description": "Example description",
                        "last_edited_at": datetime.datetime(...),
                        "project_hash": "<project_hash>",
                        "title": "Example title"
                    },
                    "user_role": <ProjectUserRole.ADMIN: 0>
                },
                ...
            ]


.. note::

    :meth:`.EncordUserClient.get_projects` has multiple optional arguments that allow you to perform a filtered search when querying projects.

    For example, if you only want projects with titles starting with "Validation", you could use :meth:`user_client.get_datasets(title_like="Validation%") <.EncordUserClient.get_datasets>`.
    Other keyword arguments such as :meth:`created_before  <.EncordUserClient.get_projects>` or :meth:`edited_after <.EncordUserClient.get_projects>` may also be of interest.


Adding users to projects
========================

Users can be added to an existing project using their emails.
You can specify the role of the users being added using the :class:`.ProjectUserRole` enum.
You can find more details of the different roles in the :class:`doc-strings <.ProjectUserRole>`.

Below is an example of how to add two new annotators to the project.
Note how all users get assigned the same role.

.. autolink-concat:: section

.. autolink-preface::
    from encord.utilities.project_user import ProjectUserRole

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/adding_users_to_datasets.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            [
                ProjectUser(
                    user_email="example1@encord.com",
                    user_role=ProjectUserRole.ANNOTATOR,
                    project_hash="<project_hash>"
                ),
                ProjectUser(
                    user_email="example2@encord.com",
                    user_role=ProjectUserRole.ANNOTATOR,
                    project_hash="<project_hash>",
                )
            ]


The return value is a list of :class:`.ProjectUser`.
Each :class:`.ProjectUser` contains information about email, :class:`.ProjectUserRole` and ``<project_hash>``.

Managing a project
==================
Your default choice for interacting with a project is via the :ref:`authentication:Public key authentication`.


.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/creating_a_project_object.py
            :language: python


API keys
========
We recommend using a :class:`encord.project.Project` as described in :ref:`tutorials/projects:Managing a project`.
This will be simpler than dealing with API keys which should only be used under specific circumstances as described in :ref:`authentication:API key authentication`.

Creating a project API key
--------------------------

Creating a project API key with specific rights
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can create a project API key through :meth:`create_project_api_key() <.EncordUserClient.create_project_api_key>`, which is required to interact with a project using the :class:`encord.project.Project`.

This method takes three arguments:

* ``project_id``: the ``<project_hash>`` of your project, obtained - for example - by :ref:`tutorials/projects:Creating a project` or :ref:`tutorials/projects:Listing existing projects`
* ``api_key_title``: the title of the API key
* ``scopes``: a list of :class:`.APIKeyScopes` enum values specifying what is accessible with the API key.

The following code example creates an API key with read and write permissions for the project labels.
For the full set of permissions, see :class:`.APIKeyScopes`.

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/creating_a_project_api_key.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            # the <project_api_key>
            "0-1aABCDE_aFGcdeHIfJ2KfLMgNO3PQh4RST5UV6W_X"


You use the ``<project_id>`` and ``<project_api_key>`` to obtain an :ref:`authentication:API key authentication` which is specific to the project with the specified permissions.

.. note::
    This capability is only available to project admins.

Creating a master API key with full rights
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is also possible to create or get a master API key with full access to *all* :class:`.APIKeyScopes`.
The following example show how to get hold of a master key:

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/creating_a_master_api_key.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            # the <project_api_key>
            "0-1aABCDE_aFGcdeHIfJ2KfLMgNO3PQh4RST5UV6W_X"


Fetching project API keys
-------------------------

All API keys for an existing project can be obtained using the ``<project_hash>`` which uniquely identifies a project.
Before you can fetch API keys, you need to i) :ref:`create a project <tutorials/projects:Creating a project>` and ii) :ref:`add API keys <tutorials/projects:Creating a project api key>`.

.. autolink-concat:: section

.. autolink-preface::
    from encord.orm.project_api_key import ProjectAPIKey, APIKeyScopes


.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/fetching_project_api_keys.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            [
                ProjectAPIKey(
                    api_key="0-1aABCDE_aFGcdeHIfJ2KfLMgNO3PQh4RST5UV6W_X",
                    title="Example title",
                    scopes=[
                        APIKeyScopes.LABEL_READ,
                        APIKeyScopes.LABEL_WRITE,
                    ]
                ),
                # ...
            ]


.. note::
    This capability is available to only the Admin of a project.
..
    fetching_project_api_keys

Data
====

Adding datasets to a project
----------------------------

To add an existing dataset to a project, you use the ``<dataset_hash>`` as follows:

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/adding_datasets_to_projects.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            True  # False if unsuccessful

.. note::
    You need to be an admin of the datasets that you want to add.

.. note::
    :meth:`add_datasets() <encord.project.Project.add_datasets>` will throw an error if it is unable to add a dataset to a project.
    See the doc-string documentation for further details.

Removing datasets from a project
--------------------------------

You can remove existing datasets from a project, using the dataset ``<dataset_hash>`` for every dataset which needs to be removed.
To get those hashes, you can follow the example in :ref:`tutorials/datasets:Listing existing datasets`.

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/removing_datasets_from_projects.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            True  # False if unsuccessful



.. note::
    You need to be an admin of the datasets that you want to remove.

.. note::
    :meth:`remove_datasets() <encord.project.Project.remove_datasets>` will throw an error if it is unable to remove a dataset from a project.
    See the doc-string documentation for further details.


Ontology
========
A central component of a project is the |ontology|.
The ontology essentially defines the label structure of a given project.
For a |platform| description of the |ontology|, please see :xref:`configure_label_editor_(ontology)`.


Fetching a project's ontology
-----------------------------

You can fetch the |ontology| of an existing project for viewing via the |sdk|.
For a |platform|-related description of the |ontology|, please see :xref:`configure_label_editor_(ontology)`.

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/fetching_project_ontology.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            {"classifications": [{"attributes": [{"featureNodeHash": "237c442f",
                                                  "id": "1.1",
                                                  "name": "Radio Example",
                                                  "options": [{"featureNodeHash": "00fe752c",
                                                               "id": "1.1.1",
                                                               "label": "Cat",
                                                               "value": "cat"},
                                                              {"featureNodeHash": "0538f289",
                                                               "id": "1.1.2",
                                                               "label": "Dog",
                                                               "value": "dog"},
                                                              {"featureNodeHash": "4d2c4767",
                                                               "id": "1.1.3",
                                                               "label": "Horse",
                                                               "value": "horse"}],
                                                  "required": False,
                                                  "type": "radio"}],
                                  "featureNodeHash": "21b68c3b",
                                  "id": "1"},
                                 {"attributes": [{"featureNodeHash": "d7c2ad1b",
                                                  "id": "2.1",
                                                  "name": "Checkbox example",
                                                  "options": [{"featureNodeHash": "88903c98",
                                                               "id": "2.1.1",
                                                               "label": "check 1: are "
                                                                        "there people in "
                                                                        "the image",
                                                               "value": "check_1:_are_there_people_in_the_image"},
                                                              {"featureNodeHash": "a5c19b1b",
                                                               "id": "2.1.2",
                                                               "label": "check if there is "
                                                                        "a pink elephant "
                                                                        "with cat eyes in "
                                                                        "the image",
                                                               "value": "check_if_there_is_a_pink_elephant_with_cat_eyes_in_the_image"}],
                                                  "required": False,
                                                  "type": "checklist"}],
                                  "featureNodeHash": "59151c93",
                                  "id": "2"},
                                 {"attributes": [{"featureNodeHash": "2afbce16",
                                                  "id": "3.1",
                                                  "name": "Text example",
                                                  "required": False,
                                                  "type": "text"}],
                                  "featureNodeHash": "8161c61a",
                                  "id": "3"}],
             "objects": [{"color": "#D33115",
                          "featureNodeHash": "41d0a534",
                          "id": "1",
                          "name": "cat",
                          "shape": "polygon"},
                         {"color": "#FCDC00",
                          "featureNodeHash": "edf21536",
                          "id": "2",
                          "name": "bus",
                          "shape": "polygon"},
                         {"color": "#DBDF00",
                          "featureNodeHash": "2a9ab898",
                          "id": "3",
                          "name": "airplane",
                          "shape": "bounding_box"},
                         {"color": "#A4DD00",
                          "featureNodeHash": "56996de1",
                          "id": "4",
                          "name": "bird",
                          "shape": "point"}]}


Adding components to a project ontology
---------------------------------------

The ontology has two types of components, classifications and objects.

Classifications relate to whole frames.
For example, if you want to be able to annotate whether an image is of a cat or a dog as a whole, you will add an animal classification with options "Cat" and "Dog."

Objects, on the other hand, are specific to locations in a frame.
For example, if you want to annotate where the dog is in the image, you would add a dog object to the ontology.
Objects are located using a graphical annotation, such as a bounding box or a polygon, indicating where the dog is.


Adding a classification to an ontology
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Here we are in the "cat vs. dog" scenario from above.
Classifications for cats and dogs are added to an ontology using the :meth:`add_classification() <encord.project.Project.add_classification>` method.

The :meth:`add_classification() <encord.project.Project.add_classification>` method takes the following parameters:

* ``name``: the description of the classification as a string
* ``classification_type``: a value from the :class:`.ClassificationType` enum.
* ``required``: a boolean value specifying whether the classification is mandatory
* ``options``: a list of options that the annotator can choose from in case of :class:`CHECKLIST <.ClassificationType>`/:class:`RADIO <.ClassificationType>`.
  Omit this parameter if adding a ``TEXT`` classification.

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/adding_classifications_to_a_project_ontology.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            True  # False if unsuccessful



Adding an object to an ontology
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Here we are in the "where is the dog" scenario.
Objects are added to an existing ontology using the :meth:`add_object() <encord.project.Project.add_object>` method.

The :meth:`add_object() <encord.project.Project.add_object>` method takes the following parameters:

* ``name``: the description of the object as a string
* ``shape``: the shape of the object used to annotate it of type :class:`.ObjectShape` enum


.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/adding_objects_to_a_project_ontology.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            True  # False if unsuccessful


Labels
======

.. note::
    This section is undergoing a review [Monday, May 23rd 2022].

A label row has this structure:

.. code-block::

    {
        "label_hash": "<label_hash>",
        "data_title": "<data_title>",
        "data_type": "<data_type>",
        "data_units": { ... },
        "object_answers": { ... },
        "classification_answers": { ... },
        "label_status": "<label_status>",
    }

A label row contains a single data unit or a collection of data units together with associated labels, and is specific to a data asset with type video or image group.

#.  A label row with a data asset of type ``video`` contains a single data unit.
#.  A label row with a data asset of type ``img_group`` contains any number of data units.

A data unit can have any number of vector labels (e.g. bounding box, polygon, polyline, keypoint) and classifications.

Getting label rows
------------------

A project's ``<label_hash>`` is found in the project information ``project_manager.get_project()``, which also contain information about the ``data_title``, ``data_type`` and ``label_status``.

.. code-block::

    {
        ...,
        "label_rows": [{
            "label_hash": "<label_hash>",
            "data_hash": "<data_hash>",
            "dataset_hash": "<dataset_hash>",
            "dataset_title": "<sample_dataset_title>",
            "data_title": "example.mp4",
            "data_type": "VIDEO",
            "label_status": "LABELLED",
            "annotation_task_status": "IN_REVIEW"
        },
        # ...
        ]
    }


Use the :class:`encord.project.Project` to fetch individual label objects.

.. code-block::

    label = project_manager.get_label_row("<label_hash>")

Use the :meth:`project.get_labels_list() <encord.orm.project.Project.get_labels_list>` method to get a list of label hashes (``<label_hash>``) in a project and fetch all project labels.

.. code-block::

    project = project_manager.get_project()

    label_rows = []
    for label_hash in project.get_labels_list():
        lb = project_manager.get_label_row(label_hash)
        label_rows.append(lb)

The label row object contains data units with signed URLs (``<data_link>``) to the labeled data asset.

.. code-block::

    {
        "label_hash": "<label_hash>",
        "data_hash": "data_hash",
        "data_type": "sample_data_type",
        "data_units": {
            ...,
            "<data_unit_hash>": {
                "data_hash": "<data_unit_hash>",
                "data_title": "Example title",
                "data_link": "<data_link>",
                "data_type": "img_group",  # or "video"
                "data_fps": "<fps>" # For videos
                "data_sequence": "<data_sequence>",  # defines order of data units
                "labels": { ... },
            },
        },
        "object_answers": { ... },
        "classification_answers": { ... }
    }


For the ``img_group`` data type, the ``labels`` dictionary contains ``objects`` and ``classifications``.

.. code-block::

    {
        "objects": {
            [{object 1}, {object 2}, ...]
        }
        "classifications": {
            [{classification 1}, {classification 2}, ...]
        }
    }


For the ``video`` data type, the ``labels`` dictionary contains a series of frames.

.. code-block::

    {
        "<frame>": {
            "objects": {
                [{object 1}, {object 2}, ...]
            }
            "classifications": {
                [{classification 1}, {classification 2}, ...]
            }
        },
        ...
    }


The objects and classifications answer dictionaries contain 'answers' attributes that describe the object or classification.
This is to avoid storing the information at every frame in the label dictionary.
The ``object answers`` dictionary is in the form:

.. code-block::

    {
        "objectHash": {
            "objectHash": objectHash,
            "classifications": [{answer 1}, {answer 2}, ...]
        },
        ...
    }

The ``classification answers`` dictionary is in the form:

.. code-block::

    {
        "classificationHash": {
            "classificationHash": classificationHash,
            "classifications": [{answer 1}, {answer 2}, ...]
        },
        ...
    }


Saving label rows
-----------------

Labels are saved to their ``<label_hash>`` from a label row instance.
To save labels for the data which was not labeled before, follow the steps under :ref:`tutorials/projects:Creating a label row` below.

.. code-block::

    project_manager.save_label_row('<label_hash>', sample_label)

Label rows have to be saved in the same format as fetched.
The function :meth:`construct_answer_dictionaries() <encord.utilities.label_utilities.construct_answer_dictionaries>` helps construct answer dictionaries for all objects and classifications in the label row if they do not exist, returning a label row object with updated object and classification answer dictionaries.

.. code-block:: python

    from encord.utilities.label_utilities import construct_answer_dictionaries

    sample_label = project_manager.get_label_row("sample_label_uid")
    updated_label = label_utilities.construct_answer_dictionaries(sample_label)
    project_manager.save_label_row(sample_label["label_hash"], updated_label)


Creating a label row
--------------------

If you want to save labels to a unit of data (``video``, ``img_group``) for which a label row (and thus a ``<label_hash>``) does not yet exist, you need to first create a label row associated with the data.

#. Get the data_hash ``<data_hash>`` that you want to create labels for.
   To do this, request all label rows and note the ones that are NOT_LABELLED under 'label_status' (or, where ``<label_hash>`` is None):

   .. code-block:: python

       project = project_manager.get_project()
       print(project.label_rows)

   In this example project, we have two videos.
   The first is not labeled so you can use its ``<data_hash>`` uid to create a new label row for this video.


   .. code-block::

       [
         {
         "label_hash": None,
         "data_hash": "<data_hash>",
         "data_title": "sample_video_1.mp4",
         "cord_type": 0,
         "data_type": "VIDEO",
         "label_status": "NOT_LABELLED"
         },
         {
         "label_hash": "<label_hash>",
         "data_hash": "<data_hash>",
         "data_title": "sample_video_2.mp4',
         "cord_type": 0,
         "data_type": "VIDEO",
         "label_status": "LABELLED"
         }
       ]


#. Create the label row:

    .. code-block:: python

        data_hash = label_row["data_hash"]
        my_label_row = project_manager.create_label_row(data_hash)


    The label row will have the expected structure and can be updated as needed.
    You can retrieve its uid via ``my_label_row.label_hash`` and run other operations such as get and save.

Submitting a label row for review
---------------------------------

The following method can be used to submit a label row for review.

.. code-block::

    project_manager.submit_label_row_for_review("<label_hash>")

The above method will submit the annotation task corresponding to the label row and create the review tasks corresponding to it based on the sampling rate in the project settings.

Getting data rows
-----------------

A data row contains a data unit, or a collection of data units, and has attributes ``<data_hash>``, ``video``, and ``images``.

.. code-block::

    {
        "data_hash": <data_hash>,
        "video": video,
        "images": [ images ],
    }


#. A data row with a data asset of type ``video`` contains a single data unit in the form of a video
#. A data row with a data asset of type ``img_group`` contains as many data units as there are images in the group


.. code-block:: python

    # type: Tuple[Optional[dict], Optional[List[dict]]
    video, images = project_manager.get_data("<data_hash>", generate_signed_url=True)

You can optionally return signed URLs for timed public access to that resource (default is False).

Reviewing label logs
--------------------

You can query information about a project's labels by using the :meth:`get_label_logs() <encord.project.Project.get_label_logs>` method of a corresponding :class:`ProjectManager <encord.project.Project>`.
You will need an API key with the ``label_logs.read`` permission.
The :meth:`get_label_logs() <encord.project.Project.get_label_logs>` method takes a number of optional parameters to narrow down the retrieved logs:

.. code-block::

    logs = project_manager.get_label_logs(user_hash=<user_hash>)
    for log in logs:
        print(log)

.. code-block::

    def get_label_logs(
        self,
        user_hash: str = None,
        data_hash: str = None,
        from_unix_seconds: int = None,
        to_unix_seconds: int = None
        )
        -> List[LabelLog]


Models
======

.. note::
    This section is undergoing a review [Monday, May 23rd 2022].

The |sdk| allows you to interact with Encord's advanced model features.
Our model library includes state-of-the-art classification, object detection, segmentation, and pose estimation models.

Creating a model row
--------------------

The easiest way to get started with creating a model row is to navigate to the 'models' tab in your project on the |platform|. Create a model and set parameters accordingly.

.. figure:: /images/python_sdk_model_create.png

    Getting model API details.

Click on the *Model API details* button to toggle a code snippet with create model row API details when you are happy with your selected parameters.

.. code-block:: python

    from encord.constants.model import FASTER_RCNN

    model_row_hash = project_manager.create_model_row(
        title="Sample title",
        description="Sample description",  # Optional
        #  List of feature feature uid's (hashes) to be included in the model.
        features=["<feature_hash_1>", "<feature_hash_2>", ...],
        model=FASTER_RCNN
    )
    print(model_row_hash)


The following models are available, and are all imported using ``from encord.constants.model import *``.

.. code-block::

    # Classification
    FAST_AI = "fast_ai"
    RESNET18 = "resnet18"
    RESNET34 = "resnet34"
    RESNET50 = "resnet50"
    RESNET101 = "resnet101"
    RESNET152 = "resnet152"
    VGG16 = "vgg16"
    VGG19 = "vgg19"

    # Object detection
    YOLOV5 = "yolov5"
    FASTER_RCNN = "faster_rcnn"

    # Instance segmentation
    MASK_RCNN = "mask_rcnn"


Training
--------

To get started with model training, navigate to the 'models' tab in your project on the |platform|.
Start by creating a model by following the :xref:`create_model_guidelines`.
You can also use an existing model by clicking on the *Train* button.

Navigate through the training flow and set parameters accordingly.

.. figure:: /images/python_sdk_model_train.png

    API details for training a model.

Click on the *Training API details* button to toggle a code snippet with model training API details when you are happy with your selected label rows and parameters.


.. code-block::

    from encord.constants.model_weights import *

    # Run training and print resulting model iteration object
    model_iteration = project_manager.model_train(
      <model_uid>,
      label_rows=["<label_row_1>", "<label_row_2>", ...], # Label row uid's
      epochs=500, # Number of passes through training dataset.
      batch_size=24, # Number of training examples utilized in one iteration.
      weights=fast_ai, # Model weights.
      device="cuda" # Device (CPU or CUDA/GPU, default is CUDA).
    )
    print(model_iteration)


It is important that the weights used for the model training is compatible with the created model.
For example, if you have created a ``faster_rcnn`` object detection model, you should use ``faster_rcnn`` weights.

The following pre-trained weights are available for training and are all imported using ``from encord.constants.model_weights import *``.

.. code-block::

    # Fast AI (classification)
    fast_ai

    # Yolo V5 (object detection)
    yolov5x
    yolov5s

    # Faster RCNN (object detection)
    faster_rcnn_R_50_C4_1x
    faster_rcnn_R_50_DC5_1x
    faster_rcnn_R_50_FPN_1x
    faster_rcnn_R_50_C4_3x
    faster_rcnn_R_50_DC5_3x
    faster_rcnn_R_50_FPN_3x
    faster_rcnn_R_101_C4_3x
    faster_rcnn_R_101_DC5_3x
    faster_rcnn_R_101_FPN_3x
    faster_rcnn_X_101_32x8d_FPN_3x

    # Mask RCNN (instance segmentation)
    mask_rcnn_X_101_32x8d_FPN_3x
    mask_rcnn_R_50_C4_1x
    mask_rcnn_R_50_C4_3x
    mask_rcnn_R_101_FPN_3x


Inference
---------

To get started with model inference, make sure you have created a project API key with ``model.inference`` added to access scopes.
The easiest way to get started with model inference is to navigate to the 'models' tab in your project.

Open the model training log for the model you would like to use for inference.

.. figure:: /images/python_sdk_model_inference.png

    API details for running inference.

Click the 'Inference API details' icon next to the download button to toggle a code snippet with model inference details.

.. code-block::

    # Run inference and print inference result
    inference_result = project_manager.model_inference(
      "<model_iteration_id>",  # Model iteration ID
      data_hashes=["video1_data_hash", "video2_data_hash"],  # List of data_hash values for videos/image groups
      detection_frame_range=[0, 100],  # Run detection on frames 0 to 100
    )
    print(inference_result)


You can run inference on existing videos/image groups in the platform.
You can do the same by specifying the ``data_hashes`` parameter which is the list of unique identifiers of the video/image groups on which you want to run inference.
You can define confidence, intersection-over-union (IoU) and polygon coarseness thresholds.
The default confidence threshold is set to ``0.6``, the default IoU threshold is set to ``0.3`` and the default value for the polygon coarseness is set to ``0.005``.


.. code-block::

    inference_result = project_manager.model_inference(
      "<model_iteration_id>",  # Model iteration ID
      data_hashes=["video1_data_hash", "video2_data_hash"],  # List of data_hash values for videos/image groups
      detection_frame_range=[0, 100],  # Run detection on frames 0 to 100
      conf_thresh=0.6,  # Set confidence threshold to 0.6
      iou_thresh=0.3,  # Set IoU threshold to 0.3
      rdp_thresh=0.005,  # Set polygon coarseness to 0.005
    )
    print(inference_result)


The model inference API also accepts a list of locally stored images to run inference on.
In case of locally stored images only JPEG and PNG file types are supported for running inference.

.. code-block::

    inference_result = project_manager.model_inference(
      "<model_iteration_id>",  # Model iteration ID
      file_paths=["path/to/file/1.jpg", "path/to/file/2.jpg"],  # Local file paths to images
      detection_frame_range=[1,1],
    )
    print(inference_result)

For running inference on locally stored videos, only ``mp4`` and ``webm`` video types are supported.


.. code-block::

    inference_result = project_manager.model_inference(
      "<model_iteration_id>",  # Model iteration ID
      file_paths=["path/to/file/1.mp4", "path/to/file/2.mp4"],  # Local file paths to videos
      detection_frame_range=[0, 100],  # Run detection on frames 0 to 100
    )
    print(inference_result)


The model inference API also accepts a list of base64 encoded strings.

.. code-block::

    inference_result = project_manager.model_inference(
      "<model_iteration_id>",  # Model iteration ID
      base64_strings=[base64_str_1, base_64_str_2],  # Base 64 encoded strings of images/videos
      detection_frame_range=[1,1],
    )
    print(inference_result)

Limits on the input values

* ``conf_thresh``: the value of this parameter should be between 0 and 1.
* ``iou_thresh``: the value of this parameter should be between 0 and 1.
* ``rdp_thresh``: the value for this paramater should be between 0 and 0.01.
* ``data_hashes``: the cumulative size of the videos/image groups specified should be less than or equal to 1 GB, otherwise a FileSizeNotSupportedError would be thrown.
* ``detection_frame_range``: the maximum difference between the 2 frame range values can be 1000, otherwise a DetectionRangeInvalidError would be thrown.



Algorithms
==========

.. note::
    This section is undergoing a review [Monday, May 23rd 2022].

The |sdk| allows you to interact with Encord's algorithmic automation features.
Our library includes sampling, augmentation, transformation and labeling algorithms.


Object interpolation
--------------------

The :class:`encord.project.Project` object interpolator allows you to run interpolation algorithms on project labels (requires a project ontology).

Interpolation is supported for the following annotation types:

#. Bounding box
#. Polygon
#. Keypoint

Use the :meth:`encord.project.Project.object_interpolation` method to run object interpolation.

Key frames, between which interpolation is run, can be obtained from label rows containing videos.
The objects to interpolate between key frames is a list of ``<object_hash>`` values obtained from the ``label_row["labels"]["<frame_number>"]["objects"]`` entry in the label row.
An object (identified by its ``<object_hash>``) is interpolated between the key frames where it is present.

The interpolation algorithm can be run on multiple objects with different ontological objects at the same time (i.e., you can run interpolation on bounding box, polygon, and keypoint, using the same function call) on any number of key frames.

.. tabs::

    .. tab:: Code

        .. code-block:: python

            # Fetch label row
            sample_label = project_manager.get_label_row("sample_label_uid")

            # Prepare interpolation
            key_frames = sample_label["data_units"]["sample_data_hash"]["labels"]
            objects_to_interpolate = ["sample_object_uid"]

            # Run interpolation
            interpolation_result = project_manager.object_interpolation(key_frames, objects_to_interpolate)
            print(interpolation_result)

    .. tab:: Example output

        .. code-block::

            {
                "frame": {
                    "objects": [
                        {
                            "objectHash": object_uid,
                            "featureHash": feature_uid (from editor ontology),
                            "polygon": {
                                "0": {
                                    "x": x1,
                                    "y": y1,
                                },
                                "1": {
                                    "x": x2,
                                    "y": y2,
                                },
                                "2" {
                                    "x": x3,
                                    "y": y3,
                                },
                                ...,
                            }
                        },
                        {
                            ...
                        }
                    ]
                },
                "frame": {
                    ...,
                }
            }


The interpolation algorithm can also be run from sample frames kept locally, with ``key_frames`` passed in a simple JSON structure (see :meth:`doc-strings <encord.project.Project.object_interpolation>`).

All that is required is a ``<feature_hash>`` and ``object_hash`` for each object in your set of key frames.


Other Resources
===============

.. note::
    This section is undergoing a review [Monday, May 23rd 2022].

CVAT Integration
----------------

If you are currently using :xref:`cvat` for image and video annotations, we have made it easy to import your entire project or single tasks to |company|.
This will create the ontology and import all labels and classifications.

Exporting Your CVAT Work
^^^^^^^^^^^^^^^^^^^^^^^^
You can either export an entire project or an individual task.
Keep in mind that every new export will create an entirely new project.

Exporting from the CVAT UI
""""""""""""""""""""""""""

For project exports:

.. figure:: /images/cvat_project_export.png

    Export Project.

Or for task exports:

.. figure:: /images/cvat_task_export.png

    Export Task.

Then in the popup, please ensure that images are saved too:

.. figure:: /images/cvat_project_export_popup.png
    :width: 450

    Export Project.


.. note::
    Choose the "CVAT for images 1.1" export format for images and the "CVAT for video 1.1" export format for videos.

    If your project contains videos and images, you can only choose the "CVAT for images 1.1" in which case you will loose interpolation information across video frames.


Once this is downloaded, you can unzip the file to create a directory which contains all your images/videos, together with an `annotations.xml` file which contains your CVAT ontology, CVAT labels, and CVAT tags (which are the equivalent of Encord Classifications for entire images/frames).

Importing with the |sdk|
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block::

    ssh_key = os.environ.get("SSH_KEY")
    user_client = EncordUserClient.create_with_ssh_private_key(ssh_key)

    # We have placed the unzipped Pizza Project directory into a
    # `data` folder relative to this script
    data_folder = "data/Pizza Project"
    dataset_name = "Pizza Images Dataset"
    cvat_importer_ret = user_client.create_project_from_cvat(
        LocalImport(file_path=data_folder),
        dataset_name
    )

    # Check if the import was a success and inspect the return value
    if type(cvat_importer_ret) == CvatImporterSuccess:
        print(f"project_hash = {cvat_importer_ret.project_hash}")
        print(f"dataset_hash = {cvat_importer_ret.dataset_hash}")
        print(f"issues = {cvat_importer_ret.issues}")

If the return object is a :class:`.CvatImporterSuccess`, you can open the web app and will find that the project was already added.

For possible import options and return types consult the in :meth:`code documentation <.EncordUserClient.create_project_from_cvat>`.

The :class:`Issues <.client_utilities.Issues>` Object - CVAT to Encord Import Limitations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We encourage you to inspect the returned :class:`Issues <.client_utilities.Issues>` object closely.
This will inform you about possible limitations during the project/task import.

For example, within CVAT the same label in the ontology can be used for different shapes.
Within Encord, a label in the ontology is bound to a specific shape.
During import, the importer will detect whether the same CVAT label was used for multiple shapes and create different Encord ontology items for each of them.

There are other limitations which are documented in the :class:`Issues <.client_utilities.Issues>` object.
Please reach out to the Encord team if those need clarification.


