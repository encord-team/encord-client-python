.. include:: ../../substitutes.rst

Listing existing datasets
=========================

Via the :class:`.EncordUserClient`, you can easily query and list all the datasets that are available to a given user.
In the example below, a user authenticates with |company| and then fetches all datasets available.

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/datasets/listing_existing_datasets.py
            :language: python

    .. tab:: Example output

        .. code-block:: 

            [
                {
                    "dataset": DatasetInfo(
                            dataset_hash="<dataset_hash>", 
                            user_hash="<user_hash>", 
                            title="Coco Validation 2017", 
                            description="Example description ... ", 
                            type=0, 
                            created_at=datetime.datetime(...), 
                            last_edited_at=datetime.datetime(...)
                        ), 
                    "user_role": <DatasetUserRole.ADMIN: 0>
                },
                ...
            ]

Note, that the :meth:`.EncordUserClient.get_datasets` method has multiple optional arguments that allow you to query datasets with specific characteristics.
For example, if you only want datasets with titles starting with "Validation", you could use ``user_client.get_datasets(title_like="Validation%")``.
Other keyword arguments such as `created_before` or `edited_after` may also be of interest.
