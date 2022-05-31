.. include:: ./substitutes.rst

**************
Authentication
**************

Types of authentication
========================
You can authenticate with |company| on a user basis by registering an :xref:`ssh_public_key_authentication` (i.e. "public key" in this document), or on a specific project or dataset basis by using an |company|-generated API key tied to that resource.

Public key authentication
----------------------------
Using the public key authentication will give you full access to all the capabilities of the SDK.

You will need to choose this authentication method to interact with the :class:`EncordUserClient <encord.EncordUserClient>`.

This authentication method will also allow you to interact with a :ref:`general_concepts:Dataset` or a :ref:`general_concepts:Project` assuming you are either of the following:

* An organisation admin of the organisation this project or dataset is part of
* A project admin or project manager of the project that is being accessed
* A dataset admin of the dataset that is being accessed

API key authentication
----------------------
You can additionally access a specific project or dataset via the API key authentication.
An individual API key is always tied to one specific project or dataset.

We only recommend you to use this authentication if

* You do not have the access rights to access a project or dataset
* You want to access a project or dataset as part of an automated pipeline without using a user access


Set up authentication keys
==========================

Register a public key
---------------------
Public keys are tied to the user so need to be added to your profile.
To register a public key, please follow the instructions in :xref:`public_keys` of the |sdk| documentation.

Create an API key
-----------------

API keys are tied to specific projects or datasets.
You can generate multiple keys for each project or dataset.

To create an API key you can use the |platform|:

#. Log in to your account on :xref:`login_url`
#. Navigate to the :xref:`project` or :xref:`dataset` tab in the :xref:`navigation_bar`
#. Select a project or dataset
#. Navigate to the 'Settings' tab and select the 'API access' pane on the left
#. Click on the *+ New API key* button, select relevant scopes and click the *Create* button
#. Copy your API key and make a note of the project or dataset ID. The API key is only displayed once. Example code is also displayed

.. figure:: images/api-key.png

    Getting an API key from the |platform|.

You can additionally create them programmatically as you can see in these guides:

* Create :ref:`tutorials/projects:API keys` for projects
* Create :ref:`tutorials/datasets:API keys` for datasets


Authenticate with |company|
===========================

Once you have registered a public key or created an API key, you can authenticate your SDK client with |company| and get started with the SDK.


Public key authentication with the SDK
--------------------------------------------------

If you are using public key authentication, authenticate with |company| by passing the corresponding private key to an :class:`.EncordUserClient`.
Once you have an :class:`.EncordUserClient`, you can use it to create new projects and datasets, or interact with existing ones by creating separate :class:`encord.ProjectManager` or :class:`encord.DatasetManager` objects tied to them

.. literalinclude:: code_examples/authenticate_ssh.py
    :language: python



API key authentication with the SDK
--------------------------------------------

If you are using API key authentication, authenticate with |company| by passing the resource ID (project or dataset ID) and associated API key to an :class:`.EncordClient`.
This will directly create an :class:`.EncordClient` to interact with a specific project or dataset

.. literalinclude:: code_examples/authenticate_api_key.py
    :language: python
