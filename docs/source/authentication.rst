.. include:: ./substitutes.rst

**************
Authentication
**************

Types of authentication
========================
You can authenticate with |company| on a user basis by registering an :xref:`ssh_public_key_authentication` (i.e. "public key" in this document), or on a specific project or dataset basis by using an |company|-generated API key tied to that resource.

User authentication via public key (**recommended**)
------------------------------------------------------------------------
Public key authentication gives you full access to all the capabilities of the SDK.
**This is our recommended default authentication method.**

Public key authentication is required to use the :class:`.EncordUserClient`.

You can use the client to interact with a :ref:`general_concepts:Dataset` or a :ref:`general_concepts:Project` assuming you are either of the following:

* An organisation admin of the organisation this project or dataset is part of
* A project admin or project manager of the project that is being accessed
* A dataset admin of the dataset that is being accessed

.. note::

    To setup public key authentication, follow these instructions in the :ref:`authentication:User authentication` section below.

Resource authentication via API key (supports legacy flows)
------------------------------------------------------------------
You can access a specific project or dataset via API key authentication.
An individual API key is always tied to one specific project or dataset.
**This is an authentication flow that will be deprecated in the future in favour of public key authentication.**

We only recommend you to use this authentication if

* You do not have user access rights for a project or dataset
* You want to access a project or dataset as part of an automated pipeline without using a specific user account

.. note::

    To setup resource authentication, follow these instructions in the :ref:`authentication:Resource authentication` section below.


User authentication
==========================

Set up authentication keys - user authentication
--------------------------------------------------------------------
Public keys are tied to the user so need to be added to your profile.
To register a public key, please follow the instructions in :xref:`public_keys` of the |platform| documentation.


Authenticate with |company| - user authentication
--------------------------------------------------------------------

After registering your public key, authenticate with |company| by passing the corresponding :xref:`private_key` to an :class:`.EncordUserClient`.
Once you have an :class:`.EncordUserClient`, you can use it to create new projects and datasets, or interact with existing ones by creating separate :class:`~encord.project.Project` or :class:`~encord.dataset.Dataset` objects tied to them

.. literalinclude:: code_examples/authenticate_ssh.py
    :language: python


Resource authentication
=======================
This is an authentication flow that will be deprecated in the future in favour of public key authentication.

Set up authentication keys - resource authentication
--------------------------------------------------------------------
API keys are tied to specific projects or datasets.
You can generate multiple keys for each project or dataset.

To create an API key use the |platform|:

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

Authenticate with |company| - resource authentication
--------------------------------------------------------------------
If you are using API key authentication, authenticate with |company| by passing the resource ID (project or dataset ID) and associated API key to an :class:`.EncordClient`.
This will directly create an :class:`.EncordClient` to interact with a specific project or dataset.

.. literalinclude:: code_examples/authenticate_api_key.py
    :language: python

.. note::
    The :class:`encord.client.EncordClientProject` is functionally equivalent to the :class:`~encord.project.Project`, and the recomended interface going forward.
    The :class:`encord.client.EncordClientDataset` is functionally equivalent to the :class:`~encord.dataset.Dataset`, and the recomended interface going forward.
