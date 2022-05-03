.. include:: ../../substitutes.rst

******************
Re-encoding videos
******************

As videos come with various formats, frame rates, etc., one may in rare cases experience some frame-syncing issues on the |platform|.
Specifically, it can be the case that, e.g., frame 100 on the |platform| does not correspond to the hundredth frame that you load with python.
A browser test in the |platform| can tell you if you are at risk of experiencing this issue.

.. TODO: we desperately need a link to documentation here ^

To mitigate such issue, you can re-encode your videos to get a new version of your videos that do not exhibit such issue.

Trigger a re-encoding task
--------------------------

You re-encode a list of Videos by triggering a task for the same using the |product|.
Use the method :meth:`dataset_client.re_encode_data() <.EncordClientDataset.re_encode_data>` to re-encode the list of videos specified

.. tabs::

    .. tab:: Code

        .. code-block:: python

            task_id = dataset_client.re_encode_data(
                [
                    "video1_data_hash",
                    "video2_data_hash",
                ]
            )

    .. tab:: Output example

        .. code-block:: python

            1337   # Some integer


On completion a ``task_id`` is returned which can be used for monitoring the progress of the task.

Please ensure that the list contains Videos from the same dataset which is used to initialise the EncordClient. Any Videos which do not belong to the dataset used for initialisation would be ignored.


Check status of a re-encoding task
----------------------------------

You can monitor the status of an existing Re-encoding Task using this |product|.

Use the method :meth:`dataset_client.re_encode_data_status(task_id) <.EncordClientDataset.re_encode_data_status>` to get the status.

.. tabs::

    .. tab:: Code

        .. code-block:: python

            from encord.orm.dataset import ReEncodeVideoTask
            task: ReEncodeVideoTask = (
                dataset_client.re_encode_data_status(task_id)
            )
            print(task)


    .. tab:: Example output

        .. code-block::

            ReEncodeVideoTask(
                status="DONE",
                result=[
                    ReEncodeVideoTaskResult(
                        data_hash="<data_hash>",
                        signed_url="<signed_url>",
                        bucket_path="<bucket_path>",
                    ),
                    ...
                ]
            )


The ReEncodeVideoTask contains a field called ``status`` which can take the values

#. ``"SUBMITTED"`` means that the task is currently in progress and the status should be checked back again later.
#. ``"DONE"`` means that the task has completed successfully and the field 'result' would contain metadata about the re-encoded video.
#. ``"ERROR"`` signifies that the task has failed and could not complete the re-encoding.
