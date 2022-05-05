.. include:: ../../substitutes.rst

**************************
Creating a project API key
**************************

Creating a project API key with specific rights
===============================================

Via the |product|, you can create a project API key through :meth:`create_project_api_key() <.EncordUserClient.create_project_api_key>`, which is required to interact with a project.

The method takes three arguments:

* ``project_id``: is the ``<project_hash>`` of your project, e.g., obtained by :ref:`tutorials/projects/creating_a_project:Creating a project` or :ref:`tutorials/projects/listing_existing_projects:Listing existing projects`
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


You use the ``<project_id>`` and ``<project_api_key>`` to obtain a :ref:`authentication:API key authentication` which is specific to the project with the specified permissions.

.. note::
    This capability is available to only the admin of the project.

Creating a maser API key with full rights
=========================================

It is also possible to create or get a master API key with full access to *all* :class:`.APIKeyScopes.
The following example show how to get hold of this key:

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/creating_a_master_api_key.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            # the <project_api_key>
            "0-1aABCDE_aFGcdeHIfJ2KfLMgNO3PQh4RST5UV6W_X"

