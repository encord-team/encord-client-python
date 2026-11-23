# Copy projects

Use `project.copy_project_start(...).wait_for_project()` to copy a project and
wait for the new project to be ready.

Asynchronous copying is not available for all projects.

## Start a copy

Start with an authenticated [`user_client`](../../README.md#getting-started).

This example attaches all the source project's datasets to a new project:

```python
from encord.project_copy import AllDatasets

project = user_client.get_project("YOUR_PROJECT_ID")
new_project = project.copy_project_start(title="Project copy", data=AllDatasets()).wait_for_project()
```

Add `copy_labels=True` to copy labels across all branches, and
`copy_collaborators=True` to copy collaborators and their roles.

`wait_for_project()` returns the new project when the copy succeeds. It waits for
up to an hour by default; pass `timeout_seconds=None` to wait indefinitely. If the
wait times out, the copy continues running.

## Choose which data to include

Use `SelectedDatasets` to attach specific existing datasets, or `SelectedFiles`
to copy data units into a new dataset:

```python
from encord.project_copy import ProjectCopyFile, SelectedDatasets, SelectedFiles

selected_datasets = SelectedDatasets(dataset_ids=[dataset.dataset_hash])
selected_files = SelectedFiles(
    files=[ProjectCopyFile(dataset_id=dataset.dataset_hash, data_id=data_row.data_hash)],
    dataset_title="Selected files",
)
```

Pass either selection as `data`. Use `SelectedDatasets(dataset_ids=[])` to copy
without data. Copying selected files does not duplicate the underlying files.

## Check or resume later

To start a copy without waiting, keep the job handle. Save `str(job.job_id)` to
follow it later; the copy continues if your Python process exits:

```python
job = project.copy_project_start(data=AllDatasets())
saved_job_id = str(job.job_id)
print(job.get_status().status)

# Later, using a session authenticated as the same user:
job = user_client.get_project_copy_job(saved_job_id)
new_project = job.wait_for_project()
```

`get_status()` checks once without waiting. To wait for a result without loading
the project, use `job.get_status(timeout_seconds=60)`.
