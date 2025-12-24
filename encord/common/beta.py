import functools
import warnings


class BetaWarning(UserWarning):
    """Warning category for beta features."""

    pass


def beta(message: str = ""):
    """Decorator to mark functions/methods as beta features.

    Args:
        message: Optional additional message to include in the warning.

    Example:
        @beta("This API may change in future versions.")
        def experimental_feature(self):
            pass
    """

    def decorator(obj):
        warning_message = f"{obj.__name__} is a beta feature and may change in future versions."
        if message:
            warning_message += f" {message}"

        @functools.wraps(obj)
        def wrapper(*args, **kwargs):
            warnings.warn(warning_message, category=BetaWarning, stacklevel=2)
            return obj(*args, **kwargs)

        return wrapper

    return decorator
