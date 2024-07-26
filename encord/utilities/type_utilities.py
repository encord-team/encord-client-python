from typing import Never


def exhaustive_guard(value: Never, message: str | None = None) -> Never:
    # This also works in runtime as well:
    error_message = message if message is not None else f"This code should never be reached, got: [{value}]"
    raise TypeError(error_message)
