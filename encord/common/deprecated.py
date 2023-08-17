import functools
import warnings


def deprecated(version, alternative=None):
    def decorator(func):
        @functools.wraps(func)
        def new_func(*args, **kwargs):
            message = f"Function {func.__name__} is deprecated"
            if version:
                message += f" since version {version}"
            if alternative:
                message += f", use {alternative} instead"
            warnings.warn(message, category=DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return new_func

    return decorator
