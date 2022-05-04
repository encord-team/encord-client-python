.. include:: ../../substitutes.rst

****************************
Adding datasets to a project
****************************

You can add existing datasets to a project.
The ``dataset_hash`` for every dataset is needed for this functionality.
Such hash can, e.g., be found by :ref:`tutorials/datasets/listing_existing_datasets:Listing existing datasets`.
Similarly, a ``project_hash`` is needed to authenticate a project client.
The hash can, e.g., be obtained by :ref:`tutorials/projects/listing_existing_projects:Listing existing projects`.

This is an example of adding datasets to a project.

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/adding_datasets_to_projects.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            True  # False if unsuccessful

.. note::
    You need to be the Admin of the datasets that you want to add to the project.

.. note::
    :meth:`add_datasets() <.EncordClientProject.add_datasets>` throws errors when not able to add datasets to projects.
    See the doc-string documentation for further details.