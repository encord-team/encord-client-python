import functools
import inspect
import warnings


def deprecated(version, alternative=None):
    def decorator(obj):
        message = f"{obj.__name__} is deprecated"
        if version:
            message += f" since version {version}"
        if alternative:
            message += f", use {alternative} instead"

        if inspect.isclass(obj):
            # Handle class
            original_init = obj.__init__

            @functools.wraps(original_init)
            def new_init(self, *args, **kwargs):
                warnings.warn(message, category=DeprecationWarning, stacklevel=2)
                original_init(self, *args, **kwargs)

            obj.__init__ = new_init
            return obj
        else:
            # Handle function
            @functools.wraps(obj)
            def new_func(*args, **kwargs):
                warnings.warn(message, category=DeprecationWarning, stacklevel=2)
                return obj(*args, **kwargs)

            return new_func

    return decorator
