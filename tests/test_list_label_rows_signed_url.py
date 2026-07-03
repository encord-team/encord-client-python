from copy import deepcopy
from unittest.mock import patch

import encord.client as client_module
from encord import Project
from encord.orm.label_row import (
    LabelRowMetadata,
    LabelRowMetadataWithClientMetadataSignedUrl,
)
from tests.test_data.label_rows_metadata_blurb import LABEL_ROW_METADATA_BLURB


def _wrapper_rows_with_urls():
    rows = []
    for i, blob in enumerate(LABEL_ROW_METADATA_BLURB):
        b = deepcopy(blob)
        b["client_metadata"] = {}
        b["client_metadata_signed_url"] = f"https://bucket/cm-{i}.json"
        rows.append(LabelRowMetadataWithClientMetadataSignedUrl.from_dict(b))
    return rows


def test_v2_resolves_client_metadata_via_signed_url(project: Project):
    wrapper_rows = _wrapper_rows_with_urls()
    resolved = {f"https://bucket/cm-{i}.json": {"idx": i} for i in range(len(wrapper_rows))}

    with (
        patch.object(project._client._querier, "get_multiple", return_value=wrapper_rows) as get_multiple_mock,
        patch.object(client_module, "download_signed_urls_as_json", return_value=resolved) as download_mock,
    ):
        label_rows = project.list_label_rows_v2(
            include_client_metadata=True,
            resolve_client_metadata_locally=True,
        )

    # Each LabelRowV2 exposes the resolved (downloaded + inlined) client_metadata.
    for i, lr in enumerate(label_rows):
        assert lr.client_metadata == {"idx": i}

    # The querier parsed into the signed-URL subclass while routing to the base handler.
    call = get_multiple_mock.call_args
    assert call.args[0] is LabelRowMetadataWithClientMetadataSignedUrl
    assert call.kwargs["query_type"] is LabelRowMetadata

    # All signed URLs were handed to the downloader.
    download_mock.assert_called_once()
    (urls_arg,) = download_mock.call_args.args
    assert sorted(urls_arg) == sorted(resolved.keys())


def test_v2_without_flag_uses_base_type_and_skips_resolution(project: Project):
    base_rows = [LabelRowMetadata.from_dict(blob) for blob in LABEL_ROW_METADATA_BLURB]

    with (
        patch.object(project._client._querier, "get_multiple", return_value=base_rows) as get_multiple_mock,
        patch.object(client_module, "download_signed_urls_as_json") as download_mock,
    ):
        project.list_label_rows_v2(include_client_metadata=True)
        download_mock.assert_not_called()

    # Default path parses into the base type and sends no routing override.
    call = get_multiple_mock.call_args
    assert call.args[0] is LabelRowMetadata
    assert call.kwargs.get("query_type") is None


def test_resolution_leaves_rows_without_urls_untouched(project: Project):
    # Mix: first row has a resolvable URL, second has an empty URL (no bucket blob).
    rows = [
        LabelRowMetadataWithClientMetadataSignedUrl.from_dict(
            {
                **LABEL_ROW_METADATA_BLURB[0],
                "client_metadata": {},
                "client_metadata_signed_url": "https://bucket/cm.json",
            }
        ),
        LabelRowMetadataWithClientMetadataSignedUrl.from_dict(
            {**LABEL_ROW_METADATA_BLURB[1], "client_metadata": {"inline": True}, "client_metadata_signed_url": ""}
        ),
    ]
    resolved = {rows[0].client_metadata_signed_url: {"fetched": True}}

    with (
        patch.object(project._client._querier, "get_multiple", return_value=rows),
        patch.object(client_module, "download_signed_urls_as_json", return_value=resolved),
    ):
        label_rows = project.list_label_rows_v2(
            include_client_metadata=True,
            resolve_client_metadata_locally=True,
        )

    assert label_rows[0].client_metadata == {"fetched": True}
    # The row without a URL keeps whatever client_metadata it already had.
    assert label_rows[1].client_metadata == {"inline": True}
