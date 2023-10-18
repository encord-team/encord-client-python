.. include:: ./substitutes.rst

****************
General Concepts
****************
The |sdk| revolves around three major concepts:

User
====
The user authenticated to interact with the |company| platform.
The user has access to the resources and capabilities that are also available on the |platform|.
For a |platform| specific description of capabilities, please refer to the :xref:`docs_main_entry`.

> 👍 Tip
>For collaborative teams using our SDK, we recommend creating shared service accounts and creating SSH keys for those shared accounts. For example, to have several people create ontologies, datasets, and projects programatically, create an email account for use with Encord (for example, encord-admins@mycompany.com) and generate an SSH for that email account.

Dataset
=======
The space where the data itself lives.
Datasets can be reused across multiple projects and contain no labels or annotations themselves.
For a |platform| specific introduction, please refer to the |platform| :xref:`dataset` page.

Project
=======
The space where labels, annotations, and reviews live.
Projects can be linked to multiple datasets.
For a |platform| specific introduction, please refer to the |platform| :xref:`project` page.

For each of the concepts, you find a class that allows you to interact with their specific attributes.
For example, the *Project* has an associated :class:`~encord.project.Project` class and the *Dataset* has an associated :class:`~encord.dataset.Dataset` class.


If you haven't already, you can go ahead and install the SDK by following the :ref:`installation:Installation` guide or skip directly to the :ref:`authentication:Authentication` page to get started with the |sdk|.
