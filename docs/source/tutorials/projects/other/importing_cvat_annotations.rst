.. include:: ../../../substitutes.rst

.. note::
    This page is undergoing a reconstruction [Monday, May 9th 2022].

****************
CVAT Integration
****************

If you are currently using :xref:`cvat` for image and video annotations, we have made it easy to import your entire project or single tasks to |company|.
This will create the ontology and import all labels and classifications.

Exporting Your CVAT Work
========================
You can either export an entire project or an individual task.
Keep in mind that every new export will create an entirely new project.

Exporting from the CVAT UI
--------------------------

For project exports:
.. figure:: /images/cvat_project_export.png

    Export Project.

Or for task exports:
.. figure:: /images/cvat_task_export.png

    Export Task.

Then in the popup, please ensure that images are saved too:

.. figure:: /images/cvat_project_export_popup.png

    Export Project.


.. note::
    Choose the "CVAT for images 1.1" export format for images and the "CVAT for video 1.1" export format for videos.

    If your project contains videos and images, you can only choose the "CVAT for images 1.1" in which case you will loose interpolation information across video frames.


Once this is downloaded, you can unzip the file to create the directory which contains all your images/videos and also the `annotations.xml` file which contains your CVAT ontology, CVAT labels, and CVAT tags (which are the equivalent of Encord Classifications for entire images/frames).

Importing with our Python SDK
=============================

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
=============================================================================================

We encourage you to inspect the returned :class:`Issues <.client_utilities.Issues>` object closely.
This will inform you about possible limitations during the project/task import.

For example, within CVAT the same label in the ontology can be used for different shapes.
Within Encord, a label in the ontology is bound to a specific shape.
During import, the importer will detect whether the same CVAT label was used for multiple shapes and create different Encord ontology items for each of them.

There are other limitations which are documented in the :class:`Issues <.client_utilities.Issues>` object.
Please reach out to the Encord team if those need clarification.
