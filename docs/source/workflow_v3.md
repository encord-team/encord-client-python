# Project workflow inspection (`workflow_v3`)

This beta interface is available from `encord.beta.workflow_v3` and may change before it becomes stable.

`project.workflow_v3` provides read-only access to a supported project's complete workflow
graph, including stages, pathways and selected settings. It also supports retrieving
tasks, assigning manual work and submitting Annotation, Review and External work.
Reads never claim or advance work.

This interface is not available for every project. After loading a project with
`user_client.get_project()` or `user_client.list_projects()`, check `project.has_workflow_v3`
before accessing it. Accessing an unavailable interface raises `EncordException`.

The existing `project.workflow` interface remains available for projects that support it;
check `project.has_workflow` independently. The two interfaces expose different models
and are not interchangeable.

Stages represent steps in a workflow. Pathways connect stages and define where work
can move next. Together, they form the workflow graph, loaded as a snapshot with the project.
A task is the work on one target at one stage. Each time a target enters a stage, a new task is created.
Task reads and actions make separate API requests. Task classes such as `AnnotationTask` are
distinct from the `encord.workflow` classes of the same name.

## Inspecting a workflow

Load the graph with `user_client.get_project()` or `user_client.list_projects()`.
Use an authenticated [`user_client`](../../README.md#getting-started), your project ID
as `project_hash`, and your stage names in the examples.

```python
from encord.beta.workflow_v3 import ExternalStage

project = user_client.get_project(project_hash)
if not project.has_workflow_v3:
    raise ValueError("Workflow inspection through workflow_v3 is not available for this project.")

workflow = project.workflow_v3
external = workflow.get_stage(name="External processing", type_=ExternalStage)

for pathway in external.pathways:
    destination = workflow.get_stage(id=pathway.destination_stage_id)
    print(pathway.name, destination.name)
```

The older `project.get_project()` and `user_client.get_projects()` methods do not load the graph.

`workflow.stages` includes Start, routers, manual stages, External and every terminal
outcome. `get_stage()` accepts exactly one of `name` or `id` (a `UUID` or UUID string).
Names match exactly; duplicates require an ID. `type_` checks the class and narrows
the return type.

`workflow.pathways` contains all connections; `stage.pathways` contains outgoing ones.
Workflow, stage and pathway IDs are `UUID`s. Pathways expose `source_stage_id`,
`destination_stage_id`, `verdict` and an optional, non-unique `name`.

## Settings

Read configuration through `stage.settings`. Settings classes are available from
`encord.beta.workflow_v3.settings`; an empty settings object does not mean the stage has no configuration.
Settings contracts start at version 1, with classes such as `ReviewStageSettingsV1`.
Inspect `settings.version` to identify the contract.

| Stage | Available settings |
| --- | --- |
| Percentage Router | Pathway probabilities |
| Start, Annotation, Review, External, Collaborator Router, Complete, Archive, Skip | No settings exposed |

Worker restrictions and collaborator-router rules are not exposed by this interface.

### Pathway probabilities

`pathway_probabilities` is a read-only mapping from pathway UUIDs to fractions summing
to one: `0.25` means 25%.

```python
from encord.beta.workflow_v3 import PercentageRouterStage
from encord.beta.workflow_v3.settings import PercentageRouterStageSettingsV1

router = workflow.get_stage(name="Routing", type_=PercentageRouterStage)
if not isinstance(router.settings, PercentageRouterStageSettingsV1):
    raise ValueError("Upgrade the SDK to interpret this router's settings.")
for pathway in router.pathways:
    print(pathway.name, router.settings.pathway_probabilities[pathway.id])
```

## Snapshots and exports

Discovery and settings access make no additional HTTP requests. To refresh, call
`project.refetch_data()` and read `project.workflow_v3` again. Previously returned
objects keep their original values.

Settings and pathways have `to_dict()` for a JSON-safe copy using Python field names.
Changing that copy does not change the graph; it is not an editing request.

Unfamiliar stages load as `UnknownStage`; inspect their configuration with `settings.to_dict()`.
Unrecognized enum values become `UNKNOWN`, not a default or valid filter value.
An SDK upgrade may be needed to use these capabilities.

## Task retrieval

`stage.get_tasks()` returns current work the caller may see, including entering,
entered, processing, failed and resting terminal work. Historical tasks are not selected.
Start may have a backlog; synchronous routers normally return no current work.
A returned task is not necessarily actionable.
Work can finish or change assignment between selection and fetching its details; the
iterator returns its latest state, so an item may already be historical or no longer
available to the caller.

Tasks include a task ID, typed `target`, status, priority, timestamps and optional
`assignment`. Repeated stage entries have different task IDs. Assignment is separate from
status; its user IDs are opaque strings, not emails.

The response's `stage_type` determines the task class: `ExternalTask`,
`AnnotationTask` or `ReviewTask` for those stages, and `Task` otherwise.
Stage-specific retrieval has matching return types; `workflow.get_task()` returns
the same specialized objects through the common `Task` interface. Construction
uses the task's recorded stage type, not the loaded graph, including for historical tasks.
Class membership describes applicable operations, not current permissions or readiness.

```python
from encord.beta.workflow_v3 import DataUnitTarget, TaskSort, TaskStatus

for task in external.get_tasks():
    print(task.id, task.status)
    if isinstance(task.target, DataUnitTarget):
        print(task.target.data_hash, task.target.dataset_hash)

for task in external.get_tasks(
    statuses=[TaskStatus.PROCESSING_FAILED],
    sort=TaskSort.CREATED_AT,
):
    print(task.id, task.status)
```

Arguments are validated when `get_tasks()` is called. Requests start on iteration
and pages load automatically; backend and network errors surface during iteration.
The queue can change between pages; it is not a fixed snapshot. There are no per-item
detail requests.

Live work defaults to descending priority, then ascending creation time and ID.
`TaskSort.CREATED_AT` selects oldest first. Terminal stages use newest-arrival
ordering and reject `statuses` and `sort` arguments.

Targets represent data units, slices, datasets, data-group subsets or dataset subsets.
`DataUnitTarget` exposes `data_hash` and `dataset_hash`; not every target has a data hash.
Responses exclude labels, media and subset contents. This interface does not support
subset membership or slice-range retrieval.

Fetch a fresh snapshot by task UUID:

```python
detail = workflow.get_task(id=task_id)
```

This can retrieve current or historical tasks. Current-work permissions match
listing; historical access has separate rules. State and permissions can change
between requests.

## Unfamiliar types

Unfamiliar stage and target types load as `UnknownStage` and `UnknownTarget`. Inspect
their original types through `raw_stage_type` and `raw_target_type`. Unfamiliar
settings versions load as `UnknownStageSettings`, without changing the stage's type
or identity; inspect their configuration with `to_dict()`.
Unrecognized enum values become `UNKNOWN`, not a known default or valid status filter.
Specialized functionality may require an SDK upgrade.
Tasks with unfamiliar stage types remain generic `Task` objects, with
`stage_type=StageType.UNKNOWN` and the original value in `raw_stage_type`.

## Assigning and releasing manual work

Annotation and Review tasks support assignment and release:

```python
from encord.beta.workflow_v3 import AnnotationStage

annotation = workflow.get_stage(name="Annotate", type_=AnnotationStage)
for task in annotation.get_tasks():
    task.assign("alice@example.com")
    task.release()
    break
```

`assign("alice@example.com")` assigns to an eligible user by email, subject to permissions.
Both actions return `None` and leave existing snapshots unchanged. Use
`workflow.get_task(id=task.id)` to fetch updated metadata.

`release()` requires project management access and releases the current assignment,
not necessarily the holder in your snapshot.
It returns `None` without submitting or moving work.
Releasing an already-unassigned task succeeds and clears any claim. Backend permissions apply.

A stale task raises `encord.beta.workflow_v3.StaleTaskError`.

Use `workflow.release_tasks(tasks)` to release up to 1,000 tasks in one request.
It returns `None` on success, including for already-unassigned tasks. If any task is
unavailable, it raises `StaleTaskError` and no assignments or claims are released.
Sent requests are not replayed automatically.

## Submitting Annotation work

Save labels separately before calling `AnnotationTask.submit()`. For a `DataUnitTarget`,
find its label row with `project.list_label_rows_v2(data_hashes=[task.target.data_hash])`,
initialize and edit its labels, then call the label row's `save()`.

```python
task.assign("alice@example.com")
task.submit(pathway_name="Ready for review", comment="Annotation complete")
```

Select a pathway by `pathway_id` or exact, case-sensitive `pathway_name`, not both.
Omit both to use the sole outgoing pathway; missing or ambiguous selection is rejected.
Annotators must hold the assignment before submitting; project managers can submit without assigning themselves.
Submission comments are supported only for data-unit targets and may contain up to 50,000 characters.
Success returns `None` and leaves the snapshot unchanged.

Invalid pathways and failed validation rules raise `encord.exceptions.InvalidArgumentsError`
with the backend's message. Stale tasks raise `encord.beta.workflow_v3.StaleTaskError`.

### Submitting Annotation batches

Use `AnnotationStage.submit_tasks()` for up to 100 tasks at the same stage,
with one shared pathway and optional comment. It accepts the same arguments as `submit()`.
To send tasks down different pathways, submit one batch per pathway.

```python
annotation.submit_tasks(annotated_tasks, pathway_name="Ready for review", comment="Annotation complete")
```

Submission is all-or-nothing: if any task fails permissions, validation or routing,
the entire batch remains unchanged, including comments. Duplicate UUIDs are processed once.
Empty batches or batches exceeding 100 items raise `ValueError` before sending a request.
Success returns `None` and leaves the snapshots unchanged.

## Submitting Review work

Use `ReviewTask.submit()` or `ReviewStage.submit_tasks()` with the same selectors,
optional comment and 100-task atomic batch limit as Annotation submission.

```python
from encord.beta.workflow_v3 import ReviewStage, TaskStatus

review = workflow.get_stage(name="Review", type_=ReviewStage)
task = next(review.get_tasks(statuses=[TaskStatus.ENTERED]))
task.assign("reviewer@example.com")
task.submit(pathway_name="Approve", comment="Review complete")
```

Reviewers must hold the assignment; project managers may submit without assigning themselves.
Submission routes the task but does not change individual label decisions.
The selected pathway's rules determine whether pending, rejected or missing labels prevent submission.
If auto-submit has already moved the task, explicit submission raises `StaleTaskError`.

## Submitting External work

Call `ExternalTask.submit()` after processing a target outside Encord.
`ExternalStage.get_tasks()` returns these objects; use `isinstance(task, ExternalTask)`
to narrow a result from `workflow.get_task()`. Only live, entered
tasks at External stages are eligible. The caller needs the project's Admin or Team
Manager role. Without direct project membership, `ORGANISATION_PROJECTS_MANAGE_ALL`
for the project's organization grants management access; it does not override a lower project role.
Queue read access alone is not enough.

Replace `process_data()` with your own processing:

```python
from encord.beta.workflow_v3 import DataUnitTarget, ExternalStage, TaskStatus

external = workflow.get_stage(name="External processing", type_=ExternalStage)
for task in external.get_tasks(statuses=[TaskStatus.ENTERED]):
    if isinstance(task.target, DataUnitTarget):
        process_data(task.target.data_hash)
        task.submit()
```

Select an outgoing pathway with `task.submit(pathway_id=pathway.id)` (a `UUID`
or UUID string) or `task.submit(pathway_name="Continue")`, not both.
Names match exactly, including case. The backend resolves them against the current
stage configuration; missing or ambiguous names are rejected. Omit both arguments
when there is exactly one outgoing pathway. A stage with no outgoing pathways cannot advance work.

Success returns `None`: completion and onward routing are atomic. The task object
remains unchanged; use `workflow.get_task(id=task.id)` to refresh it.

Backend validation failures raise `encord.exceptions.InvalidArgumentsError`;
insufficient permissions raise `encord.exceptions.AuthorisationError`. A repeated or
stale action raises `encord.beta.workflow_v3.StaleTaskError`. Actions identify the
exact task and cannot advance a later task for the same target at the same stage.
Conflicting arguments, blank names and malformed UUID strings raise `ValueError` locally.

### Submitting External batches

Use `ExternalStage.submit_tasks()` for up to 100 tasks at the same stage,
with one shared pathway. It accepts the same arguments as `submit()`.

```python
external.submit_tasks(processed_tasks, pathway_name="Continue")
```

Submission is all-or-nothing: if any task is unavailable, ineligible or cannot be routed,
the entire batch remains unchanged. Duplicate UUIDs are processed once.
Empty batches or batches exceeding 100 items raise `ValueError` before sending a request.
Success returns `None` and leaves the snapshots unchanged.

Errors raise the same exceptions as `submit()`; a stale task fails the whole batch.
An unknown stage raises `encord.exceptions.ResourceNotFoundError` with the stage and project IDs.
As with `submit()`, sent requests are not retried automatically, and a lost response
can leave the outcome uncertain.

## Retrying actions

Sent mutations are not automatically retried, regardless of retry settings. Connection
retries can still occur before sending. A transport failure or gateway error can leave
the outcome uncertain: do not blindly retry; inspect the original task first. A stale
error does not prove that your request completed it.
