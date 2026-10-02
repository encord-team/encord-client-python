"""Tests for adding Collection items by Data Title.

Resolution happens server-side, so the caller never handles storage item UUIDs. The
operation is synchronous and returns counts, which is what lets a caller batching across
several requests verify that the whole set landed.
"""

import uuid
from unittest.mock import MagicMock

import pytest

from encord.collection import Collection, _batch_titles, _title_cost
from encord.http.v2.api_client import ApiClient
from encord.orm.collection import (
    MAX_DATA_TITLE_BYTES_PER_REQUEST,
    MAX_DATA_TITLE_ITEMS_PER_REQUEST,
    CollectionDataTitleRequest,
    CollectionDataTitleResponse,
)
from encord.orm.collection import Collection as OrmCollection

COLLECTION_UUID = uuid.UUID("8c1d0e2f-4a5b-6c7d-8e9f-0a1b2c3d4e5f")
FOLDER_UUID = uuid.UUID("1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d")

DATA_TITLES = ["scene_001.mp4", "scene_002.mp4"]


def make_collection() -> tuple[Collection, MagicMock]:
    client = MagicMock(spec=ApiClient)
    orm = OrmCollection(
        uuid=COLLECTION_UUID,
        topLevelFolderUuid=FOLDER_UUID,
        name="my-collection",
        description="",
    )
    return Collection(client, orm), client


def test_add_items_by_title_posts_expected_request():
    collection, client = make_collection()

    collection.add_items_by_title(DATA_TITLES)

    client.post.assert_called_once()
    args, kwargs = client.post.call_args
    assert args[0] == f"index/collections/{COLLECTION_UUID}/add-data-title-items"
    assert kwargs["payload"] == CollectionDataTitleRequest(data_titles=DATA_TITLES)
    assert kwargs["result_type"] is CollectionDataTitleResponse


def test_add_items_by_title_accepts_any_sequence():
    """Callers often hold a tuple or generator result; the payload must still be a list."""
    collection, client = make_collection()

    collection.add_items_by_title(tuple(DATA_TITLES))

    _, kwargs = client.post.call_args
    assert kwargs["payload"].data_titles == DATA_TITLES


def test_add_items_by_title_returns_counts():
    collection, client = make_collection()
    client.post.return_value = CollectionDataTitleResponse(
        requested=2,
        matched_titles=1,
        items_added=1,
        ambiguous_titles=["ambiguous.mp4"],
        unmatched_titles=[],
        failed_items=[],
    )

    result = collection.add_items_by_title(DATA_TITLES)

    assert result.items_added == 1
    assert result.ambiguous_titles == ["ambiguous.mp4"]


def _response(**overrides) -> CollectionDataTitleResponse:
    base = dict(
        requested=0,
        matched_titles=0,
        items_added=0,
        ambiguous_titles=[],
        unmatched_titles=[],
        failed_items=[],
    )
    base.update(overrides)
    return CollectionDataTitleResponse(**base)


def test_input_under_the_cap_is_sent_as_one_request():
    collection, client = make_collection()
    client.post.return_value = _response()

    collection.add_items_by_title(["a.mp4"])

    assert client.post.call_count == 1


def test_input_over_the_cap_is_batched():
    collection, client = make_collection()
    client.post.return_value = _response()
    titles = [f"scene_{i}.mp4" for i in range(2500)]

    collection.add_items_by_title(titles)

    assert client.post.call_count == 3
    sizes = [len(call.kwargs["payload"].data_titles) for call in client.post.call_args_list]
    assert sizes == [1000, 1000, 500]


def test_counts_are_summed_across_batches():
    collection, client = make_collection()
    client.post.side_effect = [
        _response(
            requested=1000,
            matched_titles=990,
            items_added=990,
            ambiguous_titles=["amb.mp4"] * 9,
            unmatched_titles=["x.mp4"],
        ),
        _response(requested=500, matched_titles=500, items_added=500),
    ]

    result = collection.add_items_by_title([f"s{i}.mp4" for i in range(1500)])

    assert result.requested == 1500
    assert result.matched_titles == 1490
    assert result.items_added == 1490
    assert result.ambiguous_titles == ["amb.mp4"] * 9
    assert result.unmatched_titles == ["x.mp4"]


def test_duplicate_titles_are_sent_once():
    collection, client = make_collection()
    client.post.return_value = _response()

    collection.add_items_by_title(["a.mp4", "b.mp4", "a.mp4"])

    _, kwargs = client.post.call_args
    assert kwargs["payload"].data_titles == ["a.mp4", "b.mp4"]


def test_a_bare_string_is_rejected():
    """A str is iterable, so without this it is taken apart into characters and sent.

    Worse than it sounds: dict.fromkeys also de-duplicates them, so "file.txt" became seven
    single-character "titles" with one silently dropped, and the request looked plausible.
    """
    collection, client = make_collection()

    with pytest.raises(TypeError) as excinfo:
        collection.add_items_by_title("file.txt")

    assert "file.txt" in str(excinfo.value), "the message should show how to pass one title"
    client.post.assert_not_called()


def test_bytes_are_rejected_too():
    collection, client = make_collection()

    with pytest.raises(TypeError):
        collection.add_items_by_title(b"file.txt")

    client.post.assert_not_called()


def test_empty_input_makes_no_request():
    collection, client = make_collection()

    result = collection.add_items_by_title([])

    client.post.assert_not_called()
    assert result.requested == 0


def test_response_parses_camel_case_from_api():
    """The API serialises with camelCase aliases; BaseDTO must accept them."""
    response = CollectionDataTitleResponse.from_dict(
        {
            "requested": 3,
            "matchedTitles": 2,
            "itemsAdded": 2,
            "ambiguousTitles": ["ambiguous.mp4"],
            "unmatchedTitles": ["missing.mp4"],
            "failedItems": [],
        }
    )

    assert response.matched_titles == 2
    assert response.ambiguous_titles == ["ambiguous.mp4"]
    assert response.unmatched_titles == ["missing.mp4"]


# --- batching by size -----------------------------------------------------------------------
#
# Requests are limited by total size as well as by the number of titles, so 1,000 long titles
# can be too big to send at once. Batches are therefore also capped by the size of their titles.


def _sent(client: MagicMock) -> list[list[str]]:
    return [call.kwargs["payload"].data_titles for call in client.post.call_args_list]


def test_long_titles_are_split_by_size_rather_than_failing():
    collection, client = make_collection()
    client.post.return_value = _response()
    titles = [f"long/{'x' * 300}-{i:04d}.jpg" for i in range(1000)]

    collection.add_items_by_title(titles)

    batches = _sent(client)
    assert len(batches) > 1, "1,000 titles of this length must not go in one request"
    assert all(sum(_title_cost(t) for t in batch) <= MAX_DATA_TITLE_BYTES_PER_REQUEST for batch in batches)
    assert [t for batch in batches for t in batch] == titles, "every title sent once, in order"


def test_a_batch_closes_when_the_next_title_would_overflow_it():
    # Each of these costs 5: two bytes of title plus the fixed per-title allowance of 3.
    assert list(_batch_titles(["aa", "bb", "cc"], max_items=10, max_bytes=10)) == [["aa", "bb"], ["cc"]]


def test_a_title_exactly_at_the_budget_fits_on_its_own():
    assert list(_batch_titles(["aaaaaaa"], max_items=10, max_bytes=10)) == [["aaaaaaa"]]


def test_both_limits_hold_on_mixed_input():
    titles = [("s" if i % 2 else "L" * 400) + str(i) for i in range(3000)]

    batches = list(_batch_titles(titles, MAX_DATA_TITLE_ITEMS_PER_REQUEST, MAX_DATA_TITLE_BYTES_PER_REQUEST))

    assert all(len(batch) <= MAX_DATA_TITLE_ITEMS_PER_REQUEST for batch in batches)
    assert all(sum(map(_title_cost, batch)) <= MAX_DATA_TITLE_BYTES_PER_REQUEST for batch in batches)
    assert [t for batch in batches for t in batch] == titles


def test_size_is_measured_in_utf8_bytes_not_characters():
    # Counting characters would underestimate anything outside ASCII by up to four times.
    assert _title_cost("a") == 1 + 3
    assert _title_cost("é") == 2 + 3
    assert _title_cost("文") == 3 + 3


def test_quotes_and_backslashes_cost_extra():
    assert _title_cost("it's") == 4 + 3 + 1
    assert _title_cost("a\\b") == 3 + 3 + 1


def test_a_title_too_long_to_send_is_rejected_before_anything_is_sent():
    collection, client = make_collection()
    too_long = "x" * MAX_DATA_TITLE_BYTES_PER_REQUEST

    with pytest.raises(ValueError, match="too long to send"):
        collection.add_items_by_title(["fine.mp4", too_long])

    client.post.assert_not_called()
