.. include:: ../../substitutes.rst

*************************
Listing existing datasets
*************************

Via the :class:`.EncordUserClient`, you can easily query and list all the available datasets of a given user.
In the example below, a user authenticates with |company| and then fetches all datasets available.


.. autolink-concat:: section

.. autolink-preface::
    from encord.orm.dataset import DatasetInfo, DatasetUserRole, StorageLocation


.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/datasets/listing_existing_datasets.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            [
                {
                    "dataset": DatasetInfo(
                            dataset_hash="<dataset_hash>", 
                            user_hash="<user_hash>", 
                            title="Example title", 
                            description="Example description ... ", 
                            type=0,  # encord.orm.dataset.StorageLocation
                            created_at=datetime.datetime(...), 
                            last_edited_at=datetime.datetime(...)
                        ), 
                    "user_role": DatasetUserRole.ADMIN
                },
                # ...
            ]

*Note:* the ``type`` attribute in the output refers to the :class:`.StorageLocation` used when :ref:`tutorials/datasets/creating_a_dataset:Creating a dataset`.

.. note::

    :meth:`.EncordUserClient.get_datasets` has multiple optional arguments that allow you to query datasets with specific characteristics.

    For example, if you only want datasets with titles starting with "Validation", you could use ``user_client.get_datasets(title_like="Validation%")``.
    Other keyword arguments such as :meth:`created_before  <.EncordUserClient.get_datasets>` or :meth:`edited_after <.EncordUserClient.get_datasets>` may also be of interest.
