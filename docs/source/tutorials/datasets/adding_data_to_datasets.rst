.. include:: ../../substitutes.rst

***********
Adding data
***********

You can add data to datasets in multiple ways.
You can both use |company| storage, as described next, and you can :ref:`add data from a private cloud <adding_data_to_datasets:Adding data from private cloud>` to retain complete control of the data.

.. note::
    The following examples assume that you have an :class:`.EncordClientDataset` initialised as variable ``dataset_client`` and :ref:`authenticated <authentication:Authenticate with Encord>`.

Adding data to Encord-hosted storage
====================================

Uploading videos
----------------

Use the method :meth:`upload_video() <.EncordClientDataset.upload_video>` to upload a video to a dataset using |company| storage.

..
    Note (FHV): Tried to add autolink section to enable links to, e.g., ``upload_video`` on code examples below without success.
            The autolink-preface works but typehints are not handled properly by the extension.
            I suspect the issue is that, e.g., ``user_client.get_project_client`` returns a ``Union[EncordClientProject, EncordClientDataset]`` and not just an ``EncordClientProject``, so the extension doesn't know which one it is.
            As a consequence, it cannot find the correct link.

            Adding, e.g., ``user_client.get_dataset_client("test")`` to one of the following code blocks yields links, so the preface it self works.

            In turn, I suffice with linking to the proper places in the prose surrounding the code examples.

        SOLUTION:
            To mitigate the issue I had to instantiate "dummy" objects in the preface of the correct type.



.. autolink-concat:: section

.. autolink-preface::

    from encord.client import EncordClientDataset
    dataset_client = EncordClientDataset()  #  user_client.get_dataset_client("<dataset_hash>")


.. code-block:: python

    dataset_client.upload_video("path/to/your/video.mp4")


This will upload the given video file to the dataset associated to the :class:`dataset_client <.EncordClientDataset>`.

Creating image groups
---------------------

Use the method :meth:`create_image_group() <.EncordClientDataset.create_image_group>` to upload images and create an image group using |company| storage.

.. autolink-concat:: section

.. autolink-preface::

    from encord.client import EncordClientDataset
    dataset_client = EncordClientDataset()  #  user_client.get_dataset_client("<dataset_hash>")

.. code-block:: python

    dataset_client.create_image_group(
        [
            "path/to/your/img1.jpeg",
            "path/to/your/img2.jpeg",
        ]
    )

This will upload the given list of images to the dataset associated with the :class:`dataset_client <.EncordClientDataset>` and create an image group.

.. note::

    Image groups are images of the same resolution, so if ``img1.jpeg`` and ``img2.jpeg`` from the example above are of shape ``[1920, 1080]`` and ``[1280, 720]``, respectively, they will end up in each of their own image group.


.. note::

    Images in an image group will be assigned a ``data_sequence`` number, which is based on the order or the files listed in the argument to :meth:`create_image_group <.EncordClientDataset.create_image_group>` above.
    If the ordering is important, make sure to provide a list with filenames in the correct order.


Adding data from private cloud
==============================

#.  Use :meth:`user_client.get_cloud_integrations() <.EncordUserClient.get_cloud_integrations>` method to retrieve a list of available Cloud Integrations
#.  Grab the id from the integration of your choice and call :meth:`dataset_client.add_private_data_to_dataset() <.EncordClientDataset.add_private_data_to_dataset>` on the ``dataset_client`` with either the absolute path to a json file or a python dictionary in the format specified in the :xref:`private_cloud_section` of the |platform| datasets documentation

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/datasets/add_private_data.py
            :language: python


..
    TODO: Some things are missing here:
        1. A link to where cloud integrations are enabled on the web-app
        2. A way to enable cloud integrations from the SDK?
        3. Sample outputs of the given script