.. include:: ./substitutes.rst

**********
|sdk| frequently asked questions (FAQ)
**********

:meth:`encord.project.Project.get_label_rows` times out
=================
Label rows can be larger than expected, sometimes containing hundreds of thousands of annotations. When using the bulk
retrieve method it is easy to request more labels than would be practical to process, resulting in a slow response and eventually
the request timing out.

If you see this method timing out, try reducing the number of labels requested at once.