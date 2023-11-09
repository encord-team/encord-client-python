.. include:: ./substitutes.rst

**************************************
Frequently asked questions (FAQ)
**************************************

Why do my calls to ``get_label_rows()`` time out?
=======================================================

Label rows can be larger than expected, sometimes containing hundreds of thousands of annotations. When using the bulk
retrieve method :meth:`encord.project.Project.get_label_rows` it is easy to request more labels than would be practical to process, resulting in a slow response and eventually
the request timing out.

If you see this method timing out, try reducing the number of labels requested at once.


Why do I see an `AuthenticationError` when working with label hashes?
=======================================================================

An `AuthenticationError` can occur when no label hash is present in a label row. To fix this the :meth:`~encord.objects.LabelRowV2.initialise_labels`
method needs to be called before any operation using the label hash can be performed, such as in the example below.

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/faq.py
            :language: python
