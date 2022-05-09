.. include:: ../../substitutes.rst

*****************
Copying a project
*****************

You can copy a project over via the |sdk|.
This will create another project with the same ontology and settings [#F1]_.
You can decide whether this new project also copies over the same users, datasets and models - which aren't copied over by default.

The :meth:`copy_project() <.EncordClientProject>` method takes the following parameters, all of which are optional:

* ``copy_datasets`` (default ``False``) when set to ``True``, the datasets from the original project will be copied over, and new tasks will be created from them
* ``copy_collaborators`` (default ``False``) when set to ``True``, the collaborators from the original project will be copied over with their existing roles
* ``copy_models`` (default ``False``) when set to ``True``, the models and their training data from the original project will be copied over

The parameters above are set to ``False`` by default, meaning you do not need to include any of them if you
do not want to copy that feature into your new project.

:meth:`copy_project <.EncordClientProject.copy_project>` returns the ``<project_hash>`` of the new project.

The following example showcases an example of copying a project.

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/copying_a_project.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            "00000000-bbbb-cccc-eeee-ffffffffffff"  # the <project_hash>


.. rubric:: Footnotes

.. [#f1] If you do not copy over the collaborators, then the reviewer and label mapping settings won't be copied over.
