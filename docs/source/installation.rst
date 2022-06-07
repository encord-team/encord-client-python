.. include:: ./substitutes.rst

************
Installation
************

The |sdk| is available through ``pypi`` and is installed with the following command:

.. code-block:: shell

    > python3 -m pip install encord


.. note::
    A note about upgrading from ``cord-client-python`` to ``encord``.
    The Encord Python API client was previously published under the package name ``cord-python-client`` until version ``0.1.34``.
    From version ``0.1.35`` onward, all future updates will be available via the ``encord`` package.

    If you have been using the previous package up until now, upgrading is as simple as installing the new package and referencing any desired classes or methods from the new modules.
    For your convenience, we will be maintaining backwards compatibility with the old modules and names for the foreseeable future, but advise |sdk| users to update their applications to the ``encord`` namespace at their earliest convenience.

    Please contact us if you have any difficulties with the migration.

When you have successfully installed the |sdk|, you can go to the :ref:`authentication:Authentication` page to learn how to use authentication to interact with the |sdk|.

