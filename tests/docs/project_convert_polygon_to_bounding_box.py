"""
Code Block Name: Polygons to Bounding Boxes
"""

import logging
import time
from pathlib import Path
from typing import cast

import typer
from tqdm import tqdm, trange
from typing_extensions import Annotated

from encord import EncordUserClient, Project
from encord.objects import LabelRowV2, Object, Shape
from encord.objects.coordinates import BoundingBoxCoordinates, PolygonCoordinates

MAX_NUM_EXECUTION_ATTEMPTS = 10


def try_execute(func, kwargs=None):
    for n in range(MAX_NUM_EXECUTION_ATTEMPTS):
        try:
            if kwargs:
                return func(**kwargs)
            else:
                return func()
        except Exception as e:
            logging.warning(
                f"Handling {e} when executing {func} with args {kwargs}.\n" f" Trying again, attempt number {n + 1}."
            )
            time.sleep(0.5 * MAX_NUM_EXECUTION_ATTEMPTS)  # Linear backoff
    raise Exception("Reached maximum number of execution attempts.")


def initialize_label_rows(project: Project, batch_size: int = 200, include_unlabeled: bool = False) -> list[LabelRowV2]:
    label_rows = [lr for lr in project.list_label_rows_v2() if include_unlabeled or lr.label_hash is not None]
    for start in trange(
        0,
        len(label_rows),
        batch_size,
        desc=f"Initializing label rows [{project.title}]",
    ):
        bundle = project.create_bundle()
        for lr in label_rows[start : start + batch_size]:
            lr.initialise_labels(bundle=bundle)
        try_execute(bundle.execute)
    return label_rows


def populate_ontology_of_target_project(
    client: EncordUserClient, source: Project, target: Project
) -> dict[str, Object]:
    # Update the target ontology with potentially missing items
    source_ontology = source.ontology_structure
    target_ontology = client.get_ontology(target.ontology_hash)

    ontology_lookup: dict[str, Object] = {}
    for obj in source_ontology.objects:
        if obj.shape != Shape.POLYGON:
            continue

        # Find the bounding box object in the target ontology with the same name
        match = None
        for tobj in target_ontology.structure.objects:
            if tobj.shape != Shape.BOUNDING_BOX or tobj.name != obj.name:
                continue
            match = tobj
            break

        if match is None:
            match = target_ontology.structure.add_object(obj.name, Shape.BOUNDING_BOX)
        ontology_lookup[obj.name] = match

    target_ontology.save()
    return ontology_lookup


def convert_labels(
    keyfile: Annotated[
        Path,
        typer.Option(
            help="Path to private SSH key associated with Encord",
            prompt="Where is your SSH-key file stored?",
        ),
    ],
    source_project_hash: Annotated[
        str,
        typer.Option(
            help="Hash of the project from which annotations and classifications will be copied",
            prompt="What's the project hash of the SOURCE project?",
        ),
    ],
    target_project_hash: Annotated[
        str,
        typer.Option(
            help="Hash of the project where the bounding boxes will be added",
            prompt="What's the project hash of the TARGET project?",
        ),
    ],
):
    keyfile = keyfile.expanduser().resolve()

    # create a connection
    user_client = EncordUserClient.create_with_ssh_private_key(keyfile.expanduser().read_text())

    # Initialize projects
    target_project = user_client.get_project(target_project_hash)
    source_project = user_client.get_project(source_project_hash)

    # Set up the ontology for the target project if not filled already.
    ontology_lookup = populate_ontology_of_target_project(user_client, source_project, target_project)
    target_project.refetch_ontology()

    # Initialize labels
    source_project_label_rows = initialize_label_rows(source_project)
    target_project_label_rows = initialize_label_rows(
        target_project,
        include_unlabeled=True,
    )

    # Lookup for reading labels from the source project
    source_project_label_rows_by_data_hash = {lr.data_hash: lr for lr in source_project_label_rows}

    bundle = target_project.create_bundle()
    bundle_size = 0

    # Perform the conversion from polygons to bounding boxes and upload.
    for target_lr in tqdm(target_project_label_rows, desc="Migrating labels"):
        source_lr = source_project_label_rows_by_data_hash.get(target_lr.data_hash)
        if source_lr is None:
            # No labels in source project for the given data point.
            continue

        should_save = False
        for obj in source_lr.get_object_instances():
            if obj.ontology_item.shape != Shape.POLYGON or obj.object_name not in ontology_lookup:
                continue

            new_instance = ontology_lookup[obj.object_name].create_instance()
            has_annotations = False
            for annotation in obj.get_annotations():
                has_annotations = True

                coords = cast(PolygonCoordinates, annotation.coordinates)
                xs, ys = zip(*((point.x, point.y) for point in coords.values))

                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)

                target_coordinates = BoundingBoxCoordinates(
                    height=max_y - min_y,
                    width=max_x - min_x,
                    top_left_x=min_x,
                    top_left_y=min_y,
                )
                new_instance.set_for_frames(coordinates=target_coordinates, frames=annotation.frame)

            if has_annotations:
                should_save = True
                target_lr.add_object_instance(new_instance)

        if should_save:
            bundle_size += 1
            target_lr.save(bundle=bundle)

        if bundle_size >= 200:
            try_execute(bundle.execute)
            bundle = target_project.create_bundle()
            bundle_size = 0

        try_execute(target_lr.save)

    if bundle_size > 0:
        try_execute(bundle.execute)

    print("Done!")


if __name__ == "__main__":
    typer.run(convert_labels)
