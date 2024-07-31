from copy import deepcopy
from typing import Dict
from unittest.mock import MagicMock, patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from encord import Project
from encord.client import EncordClientProject
from encord.objects import LabelRowV2
from encord.orm.label_row import LabelRow, LabelRowMetadata
from tests.fixtures import ontology, project, user_client
from tests.test_data.label_rows_metadata_blurb import (
    LABEL_ROW_BLURB,
    LABEL_ROW_METADATA_BLURB,
)

assert user_client and project and ontology

DUMMY_PRIVATE_KEY = (
    Ed25519PrivateKey.generate()
    .private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    )
    .decode("utf-8")
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
