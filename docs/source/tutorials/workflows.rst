********
Workflows
********

|Workflows| are a powerful tool to design and build your projects - letting you control how an |annotation task| moves through different stages of the project,
as well as determining how different stages are structured and interact with one another.

Please note that we are rolling this feature out into open availability in |Beta mode|. While it's already powerful and flexible, many features are still
in development and will be added progressively. 

1. Creating a |Workflows| project
==================

At the moment |Workflows| projects have to be created using the Encord web-app. 
Please see our tutorial on how to `create Workflows projects <https://docs.encord.com/projects/workflows/creating-and-configuring-workflows/>`_ to learn how this is done.

2. Methods for |Workflows| projects
==================

Please note that the methods outlined below can only be used when working with |Workflows| projects. 

Our SDK currently had two methods specific to working with |Workflows| projects:

- The :meth:`~encord.user_client.EncordUserClient.workflows_reopen()` method returns a label row to the first annotation stage for re-labeling. No data is lost during the call.

- The :meth:`~encord.user_client.EncordUserClient.workflow_node()` method returns the location of a task within the workflow in the form of a 'uuid' and a 'title'. 
The 'title' corresponds to the name of the current stage in the workflow.


3. Working with |Workflows| projects
==================

The example below returns all label rows in a project to the first annotation stage.

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/workflows/workflow_reopen-example.py
            :language: python


The example below shows how both methods can be used to revert tasks in "<review_stage_2>" back ot the first annotation stage of a workflow:

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/workflows/workflow_node-example.py
            :language: python
