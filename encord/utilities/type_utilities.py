from typing import NoReturn, Optional


def exhaustive_guard(value: NoReturn, message: Optional[str]) -> NoReturn:
    # This also works in runtime as well:
    error_message = message if message is not None else f"This code should never be reached, got: [{value}]"
    raise TypeError(error_message)
