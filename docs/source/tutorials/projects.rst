.. include:: ../substitutes.rst

********
Projects
********

The project tutorials are divided into a couple of subsets.
First, we show general concepts like creating a new project from the |sdk|.
Afterwards, we go into more detail such as working with attributes (e.g. labels),
and incorporating advanced features such as integrating our automation models and algorithms.
Make sure that you have associated a :xref:`public-private_key_pair` with |company| before you start.
If not you can do so by following the :ref:`authentication:User authentication` tutorial.

Creating a Project
====================

You can create a new project using the :meth:`create_project() <.EncordUserClient.create_project>` method.

------------

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



.. note:: If you do not copy over the collaborators, then the reviewer and label mapping settings will not be copied over either.



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

> 👍 Tip
>For collaborative teams using our SDK, we recommend creating shared service accounts and creating SSH keys for those shared accounts. For example, to have several people create ontologies, datasets, and projects programatically, create an email account for use with Encord (for example, encord-admins@mycompany.com) and generate an SSH for that email account.

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

Project details
==================
To obtain details about your project, you first need to complete the :ref:`authentication:User authentication` and create a 'project' object. The code snippet below shows how to do this using the project id.

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/creating_a_project_object.py
            :language: python


Collaborator session information
---------------------------------

Use the :meth:`list_collaborator_timers() <.EncordUserClient.list_collaborator_timers>` method on a 'project' object to obtain session information for each collaborator that has worked on the project within a specified range of dates.

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/list_collaborator_timers.py
            :language: python

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

A central component of a project is the ontology - an in-depth description of which can be found `here <https://docs.encord.com/docs/annotate-ontologies>`_.

Ontologies are top-level entities that can be attached to projects that provide a template structure for labels.
Please note that while a project can only have a single ontology attached to it, one ontology can be attached to multiple projects.

- To access the ontology you can use the :meth:`~encord.user_client.EncordUserClient.get_ontology()` method, that allows you to work with its `structure` property.
- The structure comes as the :class:`~encord.ontology.ontology_labels_impl.OntologyStructure` class which has good self documenting examples on how to be used.

Labels
======
Check the end to end tutorials for a guide on how to read, construct, and save labels.

Submitting a label row for review
---------------------------------

The following method can be used to submit a label row for review.

.. code-block::

    project.submit_label_row_for_review("<label_hash>")

The above method will submit the annotation task corresponding to the label row and create the review tasks corresponding to it based on the sampling rate in the project settings.

Reviewing label logs
--------------------

While the :meth:`get_label_row() <encord.project.Project.get_label_row>` will gives static information about the labels at the point in time, the :meth:`get_label_logs() <encord.project.Project.get_label_logs>` gives you an actions log that was created in the UI to create all the current labels.
Those actions include for example adding, editing, and deleting labels.
Check the :meth:`Action <encord.orm.label_log.Action>` `Enum` for all possible actions.

Possible use cases of consuming these actions would be to gather performance statistics around labelling.

Check the signature of the :meth:`get_label_logs() <encord.project.Project.get_label_logs>` function to see different ways to narrow down the response.

If you are using an an API key you will need the `label_logs.read` permission.

.. tabs::

    .. tab:: Code

        .. code-block::

            # print first log
            logs = project.get_label_logs(data_hash="7d452929-9d2a-4aac-9010-4aa1dc8d4806")
            for log in logs:
                print(log)
                break

    .. tab:: Example output

        .. code-block::

            LabelLog(
                    log_hash=None,
                    user_hash=None,
                    user_email="xxxxx@cord.tech",
                    annotation_hash="2t5kCNyw",
                    identifier="2t5kCNyw",
                    data_hash="7d452929-9d2a-4aac-9010-4aa1dc8d4806",
                    feature_hash="KOYgD/K3",
                    action=0,
                    label_name="Text classification",
                    time_taken=1482,
                    created_at="2022-11-30 17:27:10",
                    frame=1,
                )


Models
======

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

    model_row_hash = project.create_model_row(
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
    from encord.constants.model import Device

    # Run training and print resulting model iteration object
    model_iteration = project.model_train(
      "<model_uid>",
      label_rows=["<label_row_1>", "<label_row_2>", ...], # Label row uid's
      epochs=500, # Number of passes through training dataset.
      batch_size=24, # Number of training examples utilized in one iteration.
      weights=fast_rcnn_R_50_FPN_1x, # Model weights.
      device=Device.CUDA # (CPU or CUDA/GPU, default is CUDA).
    )

    print(model_iteration)


It is important that the weights used for the model training is compatible with the created model.
For example, if you have created a ``faster_rcnn`` object detection model, you should use ``faster_rcnn`` weights.

The following pre-trained weights are available for training and are all imported using ``from encord.constants.model_weights import *``.

.. code-block::

    # Fast AI (classification)
    fast_ai

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
    inference_result = project.model_inference(
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

    inference_result = project.model_inference(
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

    inference_result = project.model_inference(
      "<model_iteration_id>",  # Model iteration ID
      file_paths=["path/to/file/1.jpg", "path/to/file/2.jpg"],  # Local file paths to images
      detection_frame_range=[1,1],
    )
    print(inference_result)

For running inference on locally stored videos, only ``mp4`` and ``webm`` video types are supported.


.. code-block::

    inference_result = project.model_inference(
      "<model_iteration_id>",  # Model iteration ID
      file_paths=["path/to/file/1.mp4", "path/to/file/2.mp4"],  # Local file paths to videos
      detection_frame_range=[0, 100],  # Run detection on frames 0 to 100
    )
    print(inference_result)


The model inference API also accepts a list of base64 encoded strings.

.. code-block::

    inference_result = project.model_inference(
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
            sample_label = project.get_label_row("sample_label_uid")

            # Prepare interpolation
            key_frames = sample_label["data_units"]["sample_data_hash"]["labels"]
            objects_to_interpolate = ["sample_object_uid"]

            # Run interpolation
            interpolation_result = project.object_interpolation(key_frames, objects_to_interpolate)
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


Once this is downloaded, you can unzip the file to create a directory which contains all your images/videos, together with an `annotations.xml` file which contains your CVAT ontology, CVAT labels, and CVAT tags (which are the equivalent of Encord Classifications for entire images/frames).

Importing with the |sdk|
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::
    As imports can take quite some time, we recommend increasing the :class:`.EncordUserClient` request timeouts as described here :ref:`tutorials/configurations:Network configurations`.



.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/cvat_importer.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            project_hash = "0a5c5a7e-da96-44c1-a355-a53259c0e73e"
            dataset_hash = "bd19ef7c-b698-434f-a7cc-d3c01fc5da3e"
            encord.utilities.client_utilities.Issues(
                errors=[],
                warnings=[
                    encord.utilities.client_utilities.Issue(
                        issue_type='In Encord a specific label can only have one possible shape. If '
                            'the same label is used for multiple shapes, multiple labels need '
                            'to be created.',
                        instances=[
                            "The label `not_yet_annotated` was used for multiple shapes "
                            "`[<CvatShape.POLYGON: 'polygon'>, <CvatShape.TAG: 'tag'>]`. "
                            "Each shape which is translatable to Encord will lead to a "
                            "distinct editor entry."
                        ]
                    )
                ],
                infos=[]
            )
            issues = None


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


API keys
========
We recommend using a :class:`encord.project.Project` as described in :ref:`tutorials/projects:Managing a project`.
This will be simpler than dealing with the soon to be deprecated API keys which should only be used under specific circumstances as described in :ref:`authentication:Resource authentication`.

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


You use the ``<project_id>`` and ``<project_api_key>`` to obtain an :ref:`authentication:Resource authentication` which is specific to the project with the specified permissions.

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
