.. include:: ../../substitutes.rst

Creating a dataset API key
==========================

Via the |product| you can create a dataset API key.
The API is one way to :ref:`authentication:Authenticate with Encord`.
You need to provide the ``dataset_hash`` which uniquely identifies a dataset (see, e.g., the :ref:`tutorials/datasets/listing_existing_datasets:Listing existing datasets` to get such hash).
This capability is available to only the Admin of a dataset.
If you haven't created a dataset already, you can have a look at :ref:`tutorials/datasets/creating_a_dataset:Creating a Dataset`.


.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/datasets/creating_a_dataset_api_key.py
            :language: python

    .. tab:: Example output

        .. code-block::

            DatasetAPIKey(
              dataset_hash="<dataaset_hash>",
              api_key="<api_key>",
              title="Example api key title",
              scopes=[
                  <DatasetScope.READ: "dataset.read">,
                  <DatasetScope.WRITE: "dataset.write">
              ]
            )


