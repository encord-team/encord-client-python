.. include:: ../../substitutes.rst

******************
Creating a Project
******************

You can create a project via the |product|.
First, you need to create a :xref:`public-private_key_pair` for |company|.


:meth:`create_project() <.EncordUserClient.create_project>` takes three parameters:

* :meth:`project_title <.EncordUserClient.create_project>` - the title of the project as a string

* :meth:`dataset_ids <.EncordUserClient.create_project>` - a list of ``dataset_hash`` strings for the datasets to add to the project.
  For more details on creating datasets, see :ref:`tutorials/datasets/creating_a_dataset:Creating a dataset`.
  This can be set to an empty list

* :meth:`project_description <.EncordClientProject.create_project>` - the description of the project as a string.
  This parameter is optional

:meth:`create_project() <.EncordUserClient.create_project>` will return the ``project_hash`` of the created project.
Whoever calls this method will become the admin of the project.
The following shows the general structure for creating a project.

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/creating_a_project.py
            :language: python

    .. tab:: Example output

        .. code-block::

            "aaaaaaaa-bbbb-cccc-eeee-ffffffffffff"  # the dataset_hash


