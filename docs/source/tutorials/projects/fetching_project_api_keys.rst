.. include:: ../../substitutes.rst

*************************
Fetching project API keys
*************************

All API keys for an existing project can be obtained via the |product|.
You need to provide the ``<project_hash>`` which uniquely identifies a project.
Before you can fetch API keys, you need to i) :ref:`create a project <tutorials/projects/creating_a_project:Creating a project>` and ii) :ref:`add API keys <tutorials/projects/creating_a_project_api_key:Creating a project api key>`.

.. autolink-concat:: section

.. autolink-preface::
    from encord.orm.project_api_key import ProjectAPIKey, APIKeyScopes


.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/fetching_project_api_keys.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            [
                ProjectAPIKey(
                    api_key="0-1aABCDE_aFGcdeHIfJ2KfLMgNO3PQh4RST5UV6W_X",
                    title="Example title",
                    scopes=[
                        APIKeyScopes.LABEL_READ,
                        APIKeyScopes.LABEL_WRITE,
                    ]
                ),
                # ...
            ]




.. note::
    This capability is available to only the Admin of a project.
