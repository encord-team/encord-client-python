from copy import deepcopy
from typing import Dict
from unittest.mock import MagicMock, patch

import pytest

from encord import Project
from encord.client import EncordClientProject
from encord.objects import Classification, LabelRowV2
from encord.ontology import Ontology
from encord.orm.label_row import LabelRow, LabelRowMetadata
from tests.objects.data.data_group.scene import SCENE_METADATA, SCENE_NO_LABELS
from tests.test_data.label_rows_metadata_blurb import (
    LABEL_ROW_BLURB,
    LABEL_ROW_METADATA_BLURB,
)


def remove_label_hash(obj: Dict) -> Dict:
    obj = deepcopy(obj)
    del obj["label_hash"]
    return obj


def get_response_by_data_hash(data_hash: str):
    for r in LABEL_ROW_BLURB:
        if r["data_hash"] == data_hash:
            return r
    assert False


def get_valid_label_rows(project: Project):
    label_rows = []
    for r in LABEL_ROW_METADATA_BLURB:
        label_rows.append(LabelRowV2(LabelRowMetadata.from_dict(r), project._client, project._ontology))

    for r, v in zip(label_rows, LABEL_ROW_BLURB):
        assert r.data_hash == v["data_hash"]
        r.from_labels_dict(v)

    return label_rows


@patch.object(EncordClientProject, "get_label_rows")
@patch.object(EncordClientProject, "create_label_rows")
@patch.object(EncordClientProject, "list_label_rows")
def test_bundled_label_initialise_create(
    list_label_rows_mock: MagicMock, create_label_rows_mock: MagicMock, get_label_rows_mock: MagicMock, project: Project
):
    list_label_rows_mock.return_value = [
        LabelRowMetadata.from_dict(remove_label_hash(row)) for row in LABEL_ROW_METADATA_BLURB
    ]
    create_label_rows_mock.return_value = [LabelRow(row) for row in LABEL_ROW_BLURB]

    rows = project.list_label_rows_v2()

    bundle = project.create_bundle()
    for row in rows:
        row.initialise_labels(bundle=bundle)

    # making sure not calls were made at this point
    get_label_rows_mock.assert_not_called()

    bundle.execute()

    create_label_rows_mock.assert_called_once()
    get_label_rows_mock.assert_not_called()

    args = create_label_rows_mock.call_args[1]
    assert args is not None
    assert len(args["uids"]) == 3, "Expected 3 requests bundled"

    for row in rows:
        assert row.is_labelling_initialised, "Expect all rows to be intitialised"


@patch.object(EncordClientProject, "get_label_rows")
@patch.object(EncordClientProject, "create_label_rows")
@patch.object(EncordClientProject, "list_label_rows")
def test_bundled_label_initialise_get(
    list_label_rows_mock: MagicMock, create_label_rows_mock: MagicMock, get_label_rows_mock: MagicMock, project: Project
):
    list_label_rows_mock.return_value = [LabelRowMetadata.from_dict(row) for row in LABEL_ROW_METADATA_BLURB]
    get_label_rows_mock.return_value = [LabelRow(row) for row in LABEL_ROW_BLURB]

    rows = project.list_label_rows_v2()

    bundle = project.create_bundle()
    for row in rows:
        row.initialise_labels(bundle=bundle)

    # making sure not calls were made at this point
    get_label_rows_mock.assert_not_called()

    bundle.execute()

    create_label_rows_mock.assert_not_called()
    get_label_rows_mock.assert_called_once()

    args = get_label_rows_mock.call_args[1]
    assert args is not None
    assert len(args["uids"]) == 3, "Expected 3 requests bundled"

    for row in rows:
        assert row.is_labelling_initialised, "Expect all rows to be initialized"


@patch.object(EncordClientProject, "get_label_rows")
@patch.object(EncordClientProject, "create_label_rows")
@patch.object(EncordClientProject, "list_label_rows")
def test_bundled_label_initialise_mix_get_create(
    list_label_rows_mock: MagicMock, create_label_rows_mock: MagicMock, get_label_rows_mock: MagicMock, project: Project
):
    responses = [
        get_response_by_data_hash(data_hash) for data_hash in [row["data_hash"] for row in LABEL_ROW_METADATA_BLURB]
    ]

    rows_metadata_mix = LABEL_ROW_METADATA_BLURB[:2] + [remove_label_hash(row) for row in LABEL_ROW_METADATA_BLURB[2:]]
    list_label_rows_mock.return_value = [LabelRowMetadata.from_dict(row) for row in rows_metadata_mix]

    get_label_rows_mock.return_value = [LabelRow(row) for row in responses[:2]]
    create_label_rows_mock.return_value = [LabelRow(row) for row in responses[2:]]

    rows = project.list_label_rows_v2()

    bundle = project.create_bundle()
    for row in rows:
        row.initialise_labels(bundle=bundle)

    # making sure not calls were made at this point
    get_label_rows_mock.assert_not_called()

    bundle.execute()

    create_label_rows_mock.assert_called_once()
    get_label_rows_mock.assert_called_once()

    for row in rows:
        assert row.is_labelling_initialised, "Expect all rows to be intitialised"


@patch.object(EncordClientProject, "save_label_rows")
def test_bundled_label_save(save_label_rows_mock: MagicMock, project: Project):
    label_rows = get_valid_label_rows(project)

    bundle = project.create_bundle()
    for row in label_rows:
        row.save(bundle=bundle)

    save_label_rows_mock.assert_not_called()

    bundle.execute()

    save_label_rows_mock.assert_called_once()

    args = save_label_rows_mock.call_args[1]
    assert args is not None
    assert len(args["uids"]) == 3, "Expected 3 updates bundled"
    assert len(args["payload"]) == 3, "Expected 3 updates bundled"


@patch.object(EncordClientProject, "save_label_rows")
def test_bundled_label_save_with_explicit_bundle_size(save_label_rows_mock: MagicMock, project: Project):
    label_rows = get_valid_label_rows(project)
    assert len(label_rows) == 3

    bundle = project.create_bundle(bundle_size=2)
    for row in label_rows:
        row.save(bundle=bundle)

    save_label_rows_mock.assert_not_called()

    bundle.execute()

    assert save_label_rows_mock.call_count == 2

    args_0 = save_label_rows_mock.call_args_list[0][1]
    assert args_0 is not None
    assert len(args_0["uids"]) == 2, "Expected 2 updates bundled in the first bundle"
    assert len(args_0["payload"]) == 2, "Expected 2 updates bundled in the fist bundle"

    args_1 = save_label_rows_mock.call_args_list[1][1]
    assert args_1 is not None
    assert len(args_1["uids"]) == 1, "Expected 1 updates bundled in the first bundle"
    assert len(args_1["payload"]) == 1, "Expected 1 updates bundled in the fist bundle"


@pytest.mark.parametrize("bundled", [False, True], ids=["immediate", "bundled"])
@pytest.mark.parametrize("validate_before_saving", [False, True], ids=["no-validation", "validation"])
def test_save_compact_payload_at_transport_boundary(
    project: Project, all_types_ontology: Ontology, bundled: bool, validate_before_saving: bool
):
    row = LabelRowV2(SCENE_METADATA, project._client, all_types_ontology)
    row.from_labels_dict(SCENE_NO_LABELS)
    space = row.get_space(id="path/to/image1.jpg", type_="image")
    classification = all_types_ontology.structure.get_child_by_hash("jPOcEsbw", Classification).create_instance()
    classification.set_answer("Saved scene answer")
    space.put_classification_instance(classification, created_by="creator@example.com", confidence=0.75)
    expected_row = row.to_encord_dict()
    bundle = project.create_bundle() if bundled else None

    with patch.object(project._client._querier, "basic_setter") as setter:
        row.save(bundle=bundle, validate_before_saving=validate_before_saving)
        if bundle is not None:
            setter.assert_not_called()
            bundle.execute()

    setter.assert_called_once_with(
        LabelRow,
        uid=[row.label_hash],
        payload={
            "multi_request": True,
            "labels": [expected_row],
            "validate_before_saving": validate_before_saving,
        },
        retryable=True,
    )
    saved_row = setter.call_args.kwargs["payload"]["labels"][0]
    assert saved_row["data_units"][row.data_hash]["labels"] == {}
    assert saved_row["spaces"][space.space_id]["labels"] == {"objects": [], "classifications": []}
    answers = saved_row["classification_answers"]
    assert set(answers) == {classification.classification_hash}
    answer = answers[classification.classification_hash]
    assert answer["classifications"][0]["answers"] == "Saved scene answer"
    assert answer["range"] == []
    assert answer["spaces"] == {space.space_id: {"range": [[0, 0]], "type": "frame"}}
    assert answer["createdBy"] == "creator@example.com"
    assert answer["confidence"] == 0.75
