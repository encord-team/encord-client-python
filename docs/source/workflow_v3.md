# Workflow V3

`project.workflow_v3` lets you interact with the workflow of a project, including inspecting
the workflow and retrieving and submitting tasks. Availability depends on the project;
check `project.has_workflow_v3` before using it. The older workflow interface is
available through `project.workflow`.

A **stage** is a step in the workflow; **pathways** connect stages. A **task**
represents one visit to a stage, and its **target** identifies the data being
worked on. The same target can have several tasks, each with a different task ID.
Typically, one is active and the others represent historical visits.

## Find and process work

Start with an authenticated [`user_client`](../../README.md#getting-started).

This example retrieves tasks from an External stage, runs your own processing function
(`process_data`), and then submits them down a given pathway:

```python
from encord.workflow_v3 import DataUnitTarget, ExternalStage, TaskStatus

project = user_client.get_project("YOUR_PROJECT_ID")
if not project.has_workflow_v3:
    raise ValueError("Workflow V3 is not available for this project.")

workflow = project.workflow_v3
external = workflow.get_stage(name="External processing", type_=ExternalStage)

for task in external.get_tasks(statuses=[TaskStatus.ENTERED]):
    if isinstance(task.target, DataUnitTarget):
        process_data(task.target.data_hash)
        task.submit(pathway_name="Continue")
```

External submission requires project management access. Reading a task doesn't
necessarily mean you can submit it.

Select a pathway by exact, case-sensitive `pathway_name` or by `pathway_id`,
not both. Use an ID if pathway names are duplicated. You can omit both when the
stage has exactly one outgoing pathway. Adding another pathway will then cause
submissions without an explicit pathway to fail.

### Inspect the workflow and find tasks

`workflow.stages` includes every stage in the current workflow, including Start,
routers, and terminals. Each stage's `pathways` lists the routes out of that stage,
and `settings` lets you read the configuration exposed by the SDK.
`workflow.pathways` contains all connections.

The workflow is loaded with the project. If it changes in Encord, call
`project.refetch_data()` and read `project.workflow_v3` again to see the changes.

`stage.get_tasks()` returns the current work you are allowed to see, including
tasks still entering a stage, failed tasks, and work that has reached a terminal
stage. Tasks are fetched as you iterate; reading them does not assign them.
The queue can change while you read it, so a returned task may already
have finished. Use `statuses` and `sort` to filter and order tasks; terminal
stages accept neither. Use `workflow.get_task(id=task_id)` to fetch one task,
including a past visit to a stage.

A task's target can also be a slice, dataset, or subset. Check its type before
using `data_hash`, because not every target has one. Retrieve labels, media,
and subset contents separately; they are not included with the task.

## Annotation and Review work

Annotation and Review tasks support assignment by email, release, and submission.
Use `AnnotationStage` or `ReviewStage` to select the stage. The example below
handles whole data units and assumes project management access:

```python
from encord.workflow_v3 import AnnotationStage

annotation = workflow.get_stage(name="Annotate", type_=AnnotationStage)
task = next(annotation.get_tasks(statuses=[TaskStatus.ENTERED]), None)
if task is not None and isinstance(task.target, DataUnitTarget):
    task.assign("annotator@example.com")
    save_labels(task.target)
    task.submit(pathway_name="Send to review", comment="Annotation complete")
```

In this example, `save_labels(target)` is your own function using the label APIs.
Submitting the task does not save its labels. Submitting a Review task chooses
where work goes next without approving or rejecting individual labels. The
pathway's rules can prevent submission until required reviews are complete.

Without project management access, you can assign tasks only to yourself and
must hold the assignment before submitting. The assigned user must be eligible
to work on the target.

`task.release()` releases the current assignment without moving the
task. It requires project management access and acts on whoever is assigned when
the request is processed. The assignment's `assigned_to` and `assigned_by` fields
contain user IDs, not emails; `assign()` accepts an eligible user's email.

## Batches and outcomes

Use `stage.submit_tasks(prepared_tasks, pathway_name="Continue")` to submit
prepared tasks from the same stage through one pathway. Use
`workflow.release_tasks(manual_tasks)` to release Annotation and Review tasks
across stages in the same project. If any task fails, the whole batch is rejected.
Empty batches raise `ValueError`; batches exceeding the server's size limit raise
`InvalidArgumentsError`.

Actions return `None` and do not update the task objects you already have. Fetch
the task again with `workflow.get_task(id=task.id)` to see its latest state.

If a task is no longer available for an action, you may receive `StaleTaskError`.
Permission, validation, and not-found failures use the standard SDK exceptions.
The SDK does not automatically retry actions after sending them. If the response
is lost, the action may still have succeeded: check the task before deciding
whether to retry. A stale-task error alone does not prove that an earlier action
succeeded.
