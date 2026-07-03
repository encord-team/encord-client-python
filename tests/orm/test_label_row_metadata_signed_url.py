from copy import deepcopy

from encord.orm.label_row import (
    LabelRowMetadata,
    LabelRowMetadataWithClientMetadataSignedUrl,
)
from tests.test_data.label_rows_metadata_blurb import LABEL_ROW_METADATA_BLURB


def _blob_with_signed_url(url):
    blob = deepcopy(LABEL_ROW_METADATA_BLURB[0])
    blob["client_metadata"] = {}
    blob["client_metadata_signed_url"] = url
    return blob


def test_wrapper_captures_signed_url_field():
    row = LabelRowMetadataWithClientMetadataSignedUrl.from_dict(_blob_with_signed_url("https://bucket/cm.json"))
    assert row.client_metadata_signed_url == "https://bucket/cm.json"


def test_wrapper_copies_all_base_fields():
    blob = _blob_with_signed_url("https://bucket/cm.json")
    base = LabelRowMetadata.from_dict(blob)
    wrapped = LabelRowMetadataWithClientMetadataSignedUrl.from_dict(blob)
    # Every base field is parsed identically; the wrapper only adds the extra field.
    assert wrapped.data_hash == base.data_hash
    assert wrapped.data_title == base.data_title
    assert wrapped.label_status == base.label_status
    assert wrapped.number_of_frames == base.number_of_frames
    assert wrapped.client_metadata == base.client_metadata


def test_signed_url_defaults_to_none_when_absent():
    blob = deepcopy(LABEL_ROW_METADATA_BLURB[0])
    blob.pop("client_metadata_signed_url", None)
    row = LabelRowMetadataWithClientMetadataSignedUrl.from_dict(blob)
    assert row.client_metadata_signed_url is None


def test_base_from_dict_ignores_signed_url_so_return_type_is_unaffected():
    # The deprecated API returns plain LabelRowMetadata; it must never surface the extra field.
    base = LabelRowMetadata.from_dict(_blob_with_signed_url("https://bucket/cm.json"))
    assert not hasattr(base, "client_metadata_signed_url")
    assert "client_metadata_signed_url" not in base.to_dict()
