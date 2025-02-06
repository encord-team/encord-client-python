import contextlib

import pytest

from encord.common.utils import validate_user_agent_suffix

valid_examples = [
    "CERN-LineMode/2.15 libwww/2.17b3",
    "Mozilla/5.0",
    "Simple-Bot",
    "Product/1.0 AnotherProduct/2.0",
    "Chrome/91.0.4472.124 Safari/537.36",
]

invalid_examples = [
    "",  # Empty string
    "/",  # Just a slash
    "Invalid/Version/",  # Trailing slash
    "Product/1.0/",  # Trailing slash
    "Product//1.0",  # Double slash
    "/1.0",  # Missing product name
]


@pytest.mark.parametrize(
    ["user_agent_suffix", "should_raise"],
    [(example, False) for example in valid_examples] + [(example, True) for example in invalid_examples],
)
def test_user_agent_validate_happy(user_agent_suffix: str, should_raise: bool) -> None:
    context = pytest.raises(ValueError) if should_raise else contextlib.nullcontext()
    with context:
        validate_user_agent_suffix(user_agent_suffix)
