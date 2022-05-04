.. include:: ../../substitutes.rst

*************************
Listing existing projects
*************************

Via the :class:`.EncordUserClient`, you can query and list all the available projects of a given user.
In the example below, a user authenticates with |company| and then fetches all projects available.

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/listing_existing_projects.py
            :language: python

    .. tab:: Example output

        .. code-block::

            [
                {
                    'project': {
                        'created_at': datetime.datetime(...),
                        'description': 'Example description',
                        'last_edited_at': datetime.datetime(...),
                        'project_hash': '<project_hash>',
                        'title': 'Example title'
                    },
                    'user_role': <ProjectUserRole.ADMIN: 0>
                },
                ...
            ]


.. note::

    :meth:`.EncordUserClient.get_projects` has multiple optional arguments that allow you to query projects with specific characteristics.

    For example, if you only want projects with titles starting with "Validation", you could use ``user_client.get_projects(title_like="Validation%")``.
    Other keyword arguments such as :meth:`created_before  <.EncordUserClient.get_datasets>` or :meth:`edited_after <.EncordUserClient.get_datasets>` may also be of interest.
