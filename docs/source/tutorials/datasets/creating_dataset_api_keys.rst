.. include:: ../../substitutes.rst

Creating a dataset API key
==========================

Via the |product| you can create a dataset API key.
The API is one way to :ref:`authentication:Authenticate with Encord`.
You also need to provide the ``resource_id`` which uniquely identifies a dataset.
This capability is available to only the Admin of a dataset.
If you haven't created a dataset already, you can have a look at :ref:`tutorials/datasets/creating_a_dataset:Creating a Dataset`.


.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/datasets/creating_a_dataset_api_key.py
            :language: python

    .. tab:: Output

        .. code-block::

            DatasetAPIKey(
              dataset_hash='aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
              api_key='lCuoabcdefabcdefabcdefabcdefabcdefabc-jlan8',
              title='Full Access API Key',
              scopes=[
                  <DatasetScope.READ: 'dataset.read'>,
                  <DatasetScope.WRITE: 'dataset.write'>
              ]
            )

You use the :class:`.DatasetAPIKey` for interactiong with the dataset. TODO add link and more text.