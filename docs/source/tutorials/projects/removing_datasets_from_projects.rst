.. include:: ../../substitutes.rst

********************************
Removing datasets from a project
********************************

You can remove existing datasets from a project, using the dataset ``<dataset_hash>`` for every dataset which needs to be removed.
To get those hashes, you can follow the :ref:`tutorials/datasets/listing_existing_datasets:Listing existing datasets`.

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/removing_datasets_from_projects.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            True  # False if unsuccessful



.. note::
    You need to be the Admin of the datasets that you want to add to the project.

.. note::
    :meth:`remove_datasets() <.EncordClientProject.remove_datasets>` throws errors when not able to remove datasets from projects.
    See the doc-string documentation for further details.
