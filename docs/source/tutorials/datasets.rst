.. include:: ../substitutes.rst

********
Datasets
********

The |sdk| allows you to interact with the datasets you have added to |company|.
The attributes and member functions of the Dataset class can be found here: :class:`Dataset <encord.dataset.Dataset>`.

Each dataset can have a list of :class:`DataRows <encord.dataset.DataRow>` which are the individual videos, image groups, images, or DICOM series within the Dataset.

Below, you can find tutorials on how to interact with your datasets when you have associated a :xref:`public-private_key_pair` with |company|.


Creating a dataset
==================

To create a dataset, first select where your data will be hosted with the appropriate :class:`StorageLocation <encord.orm.dataset.StorageLocation>`.
The following example will create a dataset called "Example Title" that will expect data hosted on AWS S3.
If you just with to upload your data from local storage to |company|, :class:`CORD_STORAGE <encord.orm.dataset.StorageLocation>` would be the appropriate choice.

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/datasets/creating_a_dataset.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            {
                "title": "Example Title",
                "type": 1,
                "dataset_hash": "<dataset_hash>",
                "user_hash": "<user_hash>",
            }


Listing existing datasets
=========================

Using the :class:`.EncordUserClient`, you can easily query and list all the available datasets of a given user.
In the example below, a user authenticates with |company| and then fetches all datasets available.


.. autolink-concat:: section

.. autolink-preface::
    from encord.orm.dataset import DatasetInfo, DatasetUserRole, StorageLocation


.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/datasets/listing_existing_datasets.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            [
                {
                    "dataset": DatasetInfo(
                            dataset_hash="<dataset_hash>",
                            user_hash="<user_hash>",
                            title="Example title",
                            description="Example description ... ",
                            type=0,  # encord.orm.dataset.StorageLocation
                            created_at=datetime.datetime(...),
                            last_edited_at=datetime.datetime(...)
                        ),
                    "user_role": DatasetUserRole.ADMIN
                },
                # ...
            ]

*Note:* the ``type`` attribute in the output refers to the :class:`.StorageLocation` used when :ref:`tutorials/datasets:Creating a dataset`.

.. note::

    :meth:`.EncordUserClient.get_datasets` has multiple optional arguments that allow you to query datasets with specific characteristics.

    For example, if you only want datasets with titles starting with "Validation", you could use :meth:`user_client.get_datasets(title_like="Validation%") <.EncordUserClient.get_datasets>`.
    Other keyword arguments such as :meth:`created_before  <.EncordUserClient.get_datasets>` or :meth:`edited_after <.EncordUserClient.get_datasets>` may also be of interest.


Managing a dataset
==================
Your default choice for interacting with a dataset is via the :ref:`authentication:User authentication`.


.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/datasets/creating_a_dataset_object.py
            :language: python


Data
====

Adding data
-----------

You can add data to datasets in multiple ways.
You can both use |company| storage, as described next, and you can :ref:`add data from a private cloud <tutorials/datasets:Adding data from a private cloud>` to integrate any pre-existing data.

.. note::
    The following examples assume that you have a :class:`~encord.dataset.Dataset` initialised as variable ``dataset`` and :ref:`authenticated <authentication:Resource authentication>`.

Adding data to Encord-hosted storage
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Uploading videos
""""""""""""""""

Use the method :meth:`upload_video() <encord.dataset.Dataset.upload_video>` to upload a video to a dataset using |company| storage.

..
    Note (FHV): Tried to add autolink section to enable links to, e.g., ``upload_video`` on code examples below without success.
            The autolink-preface works but typehints are not handled properly by the extension.
            I suspect the issue is that, e.g., ``user_client.get_project_client`` returns a ``Union[EncordClientProject, EncordClientDataset]`` and not just an ``EncordClientProject``, so the extension doesn't know which one it is.
            As a consequence, it cannot find the correct link.

            Adding, e.g., ``user_client.get_dataset("test")`` to one of the following code blocks yields links, so the preface it self works.

            In turn, I suffice with linking to the proper places in the prose surrounding the code examples.

        SOLUTION (FHV):
            To mitigate the issue I had to instantiate "dummy" objects in the preface of the correct type.



.. autolink-concat:: section

.. autolink-preface::

    from encord.client import Dataset
    dataset = Dataset()  #  user_client.get_dataset("<dataset_hash>")


.. code-block:: python

    dataset.upload_video("path/to/your/video.mp4")


This will upload the given video file to the dataset associated with the :class:`dataset <encord.dataset.Dataset>`.

Uploading images
""""""""""""""""

Use the method :meth:`create_image_group() <encord.dataset.Dataset.create_image_group>` to upload images and create an image group using |company| storage.

.. autolink-concat:: section

.. autolink-preface::

    from encord.client import Dataset
    dataset = Dataset()  #  user_client.get_dataset("<dataset_hash>")

.. code-block:: python

    dataset.create_image_group(
        [
            "path/to/your/img1.jpeg",
            "path/to/your/img2.jpeg",
        ]
    )

This will upload the given list of images to the dataset associated with the :class:`dataset <encord.dataset.Dataset>` and create an image group.

.. note::

    Image groups are images of the same resolution, so if ``img1.jpeg`` and ``img2.jpeg`` from the example above are of shape ``[1920, 1080]`` and ``[1280, 720]``, respectively, they will end up in each of their own image group.


.. note::

    Images in an image group will be assigned a ``data_sequence`` number, which is based on the order or the files listed in the argument to :meth:`create_image_group <encord.dataset.Dataset.create_image_group>` above.
    If the ordering is important, make sure to provide a list with filenames in the correct order.


Adding data from a private cloud
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#.  Use :meth:`user_client.get_cloud_integrations() <.EncordUserClient.get_cloud_integrations>` method to retrieve a list of available Cloud Integrations
#.  Grab the id from the integration of your choice and call :meth:`dataset.add_private_data_to_dataset() <encord.dataset.Dataset.add_private_data_to_dataset>` on the ``dataset`` with either the absolute path to a json file or a python dictionary in the format specified in the :xref:`private_cloud_section` of the |platform| datasets documentation

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/datasets/add_private_data.py
            :language: python


..
    TODO: Some things are missing here:
        1. A link to where cloud integrations are enabled on the web-app
        2. A way to enable cloud integrations from the SDK?
        3. Sample outputs of the given script

.. note::

    We strongly encourage you to follow and adapt the below script for an idiomatic way to upload data to your dataset.

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/datasets/add_private_data_with_safe_retries.py
            :language: python


Reading and updating data
-------------------------
To inspect data within a dataset you can use the :meth:`Dataset.data_rows <encord.dataset.Dataset.data_rows>` method.
You will get a list of :class:`DataRows <encord.orm.dataset.DataRow>`.
Check the auto-generated documentation for the :class:`DataRow <encord.orm.dataset.DataRow>` class for more information on
which fields you can access and update.

Deleting data
-------------

You can remove both videos and image group from datasets created using both the |platform| and the |sdk|.
Use the method :meth:`dataset.delete_data() <encord.dataset.Dataset.delete_data>` to delete from a dataset.

.. autolink-concat:: section

.. autolink-preface::

    from encord.client import Dataset
    dataset = Dataset()

.. code-block:: python

    dataset.delete_data(
        [
            "<video1_data_hash>",
            "<image_group1_data_hash>",
        ]
    )


In case the video or image group belongs to |company|-hosted storage, the corresponding file will be removed from the Encord-hosted storage.

Please ensure that the list contains videos/image groups from the same dataset which is used to initialise the :class:`dataset <encord.dataset.Dataset>`.
Any videos or image groups which do not belong to the dataset used for initialisation will be ignored.


Re-encoding videos
------------------

As videos come in various formats, frame rates, etc., one may - in rare cases - experience some frame-syncing issues on the |platform|.
For example, it might be the case that, e.g., frame 100 on the |platform| does not correspond to the hundredth frame that you load with python.
We provide a browser test in the |platform| that can tell you if you are at risk of experiencing this issue.

.. TODO: we desperately need a link to documentation here ^

To mitigate such issues, you can re-encode your videos to get a new version of your videos that do not exhibit these issues.

Trigger a re-encoding task
^^^^^^^^^^^^^^^^^^^^^^^^^^

You re-encode a list of videos by triggering a task for the same using the |sdk|.
Use the method :meth:`dataset.re_encode_data() <.Dataset.re_encode_data()>` to re-encode the list of videos specified

.. tabs::

    .. tab:: Code

        .. code-block:: python

            task_id = dataset.re_encode_data(
                [
                    "video1_data_hash",
                    "video2_data_hash",
                ]
            )
            print(task_id)

    .. tab:: Output example

        .. code-block:: python

            1337   # Some integer


On completion, a ``task_id`` is returned which can be used for monitoring the progress of the task.

Please ensure that the list contains videos from the same dataset that was used to initialise the :class:`.EncordClient`.
Any videos which do not belong to the dataset used for initialisation will be ignored.


Check the status of a re-encoding task
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the method :meth:`dataset.re_encode_data_status(task_id) <.encord.dataset.Dataset.re_encode_data_status>` to get the status of an existing re-encoding task.

.. tabs::

    .. tab:: Code

        .. code-block:: python

            from encord.orm.dataset import ReEncodeVideoTask
            task: ReEncodeVideoTask = (
                dataset.re_encode_data_status(task_id)
            )
            print(task)


    .. tab:: Example output

        .. code-block::

            ReEncodeVideoTask(
                status="DONE",
                result=[
                    ReEncodeVideoTaskResult(
                        data_hash="<data_hash>",
                        signed_url="<signed_url>",
                        bucket_path="<bucket_path>",
                    ),
                    ...
                ]
            )


The :class:`.ReEncodeVideoTask` contains a field called ``status`` which can take the values

#. ``"SUBMITTED"``: the task is currently in progress and the status should be checked back again later
#. ``"DONE"``: the task has been completed successfully and the field 'result' would contain metadata about the re-encoded video
#. ``"ERROR"``: the task has failed and could not complete the re-encoding


API keys
========
We recommend using a :class:`~encord.dataset.Dataset` as described in :ref:`tutorials/datasets:Managing a dataset`.
This will be simpler than dealing with the soon to be deprecated API keys which should only be used under specific circumstances as described in :ref:`authentication:Resource authentication`.

Creating a master API key with full rights
------------------------------------------

It is also possible to create or get a master API key with both read and write access (both values of :class:`.DatasetScope`).
The following example show how to get hold of this key:

.. autolink-concat:: section

.. autolink-preface::
    from encord.orm.dataset_api_keys import DatasetAPIKey
    from encord.orm.dataset import DatasetScope

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/datasets/creating_a_master_api_key.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            DatasetAPIKey(
              dataset_hash="<dataset_hash>",
              api_key="<api_key>",
              title="",
              scopes=[
                  DatasetScope.READ,
                  DatasetScope.WRITE,
              ]
            )

Creating a dataset API key with specific rights
-----------------------------------------------

:ref:`authentication:Resource authentication` using an API key allows you to control which capabilities the dataset client will have.
This can be useful if you, for example, want to share read-only access with some third-party.
You need to provide the ``<dataset_hash>``, which uniquely identifies a dataset (see, for example, the :ref:`tutorials/datasets:Listing existing datasets` to get such hash).
If you haven't created a dataset already, you can have a look at :ref:`tutorials/datasets:Creating a Dataset`.

.. autolink-concat:: section

.. autolink-preface::
    from encord.orm.dataset_api_keys import DatasetAPIKey
    from encord.orm.dataset import DatasetScope


.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/datasets/creating_a_dataset_api_key.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            DatasetAPIKey(
              dataset_hash="<dataset_hash>",
              api_key="<api_key>",
              title="Example api key title",
              scopes=[
                  DatasetScope.READ,
                  DatasetScope.WRITE,
              ]
            )


.. note::

    This capability is only available to an admin of a dataset.


With the API key in hand, you can now use :ref:`authentication:Resource authentication`.


Fetching dataset API keys
-------------------------

To get a list of all API keys of a dataset, you need to provide the ``<dataset_hash>`` which uniquely identifies the dataset (see, for example, the :ref:`tutorials/datasets:Listing existing datasets` to get such hash).
If you haven't created a dataset already, you can have a look at :ref:`tutorials/datasets:Creating a Dataset`.


.. autolink-concat:: section

.. autolink-preface::
    from encord.orm.dataset_api_keys import DatasetAPIKey
    from encord.orm.dataset import DatasetScope


.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/datasets/fetching_dataset_api_keys.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            [
                DatasetAPIKey(
                  dataset_hash="<dataset_hash>",
                  api_key="<dataset_api_key>",
                  title="Full Access API Key",
                  scopes=[
                      DatasetScope.READ,
                      DatasetScope.WRITE,
                  ]
                ),
                # ...
            ]

You can now use this API key for :ref:`authentication:Resource authentication`.
