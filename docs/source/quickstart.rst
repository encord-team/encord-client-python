.. include:: ./substitutes.rst

**********
Quickstart
**********

To get you started quickly, let's see an example of how to fetch some labels.

To use the |sdk| to fetch your labels, you first :ref:`install the SDK <installation:Installation>` and :xref:`add_your_public_ssh_key` to the |platform|. The following script then fetches the labels from a given project:

.. tabs::

    .. tab:: Code

        .. literalinclude:: code_examples/quickstart.py
            :language: python

    .. tab:: Example output

        .. literalinclude:: json_blurps/video_label_row.py
            :language: python

Of course, many details are not expanded upon here. We encourage you to keep reading at the :ref:`general_concepts:General Concepts` page.
