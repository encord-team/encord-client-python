.. include:: ./substitutes.rst

Quickstart
==========

To use the |product| to fetch your labels, you first :ref:`install the SDK <installation:Installation>` and :xref:`add_your_public_ssh_key` to the |platform|. Successively, you write a script as the following to fetch labels.

.. tabs::

    .. tab:: Code

        .. code-block:: python

            from encord.user_client import EncordUserClient

            user_client = EncordUserClient.create_with_ssh_private_key(
                "<your_private_key_content>",
                password="<your_private_key_password_if_necessary>"
            )

            project_hash = next((
                p['project']['project_hash']
                for p in user_client.get_projects()
            ))

            project_client = user_client.get_project_client(project_hash)
            label_hash = next((
                lr['label_hash']
                for lr in project_client.get_project().label_rows
                if lr['label_hash'] is not None
            ))
            labels = project_client.get_label_row(label_hash)
            print(labels)

    .. tab:: Example output

        .. literalinclude:: json_blurps/video_label_row.json
            :language: json

Obviously, many details are hidden here. We encourage you to keep reading at the :ref:`general_concepts:General Concepts` page.
