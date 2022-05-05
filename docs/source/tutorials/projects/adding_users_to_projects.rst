.. include:: ../../substitutes.rst

************************
Adding users to projects
************************

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


