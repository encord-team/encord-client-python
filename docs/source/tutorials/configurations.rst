.. include:: ../substitutes.rst

****************
Configurations
****************

There are some configurations that you can set for working with the |sdk|.


Network configurations
========================
If you have an unstable connection, sometimes you might want to overwrite the defaults of the :class:`RequestsSettings <encord.http.constants.RequestsSettings>`.
These settings will propagate to the :class:`~encord.project.Project` and :class:`~encord.dataset.Dataset` objects that are created from this :class:`.EncordUserClient`.

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/configurations/set_requests_settings.py
            :language: python


You can also overwrite the **timeouts** for reads and writes.
To overwrite the read, write, and connect timeout you can do the following:

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/configurations/overwrite_timeouts.py
            :language: python

