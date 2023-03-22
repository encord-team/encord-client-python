try:
    # For Python 3.8 and later
    import importlib.metadata as importlib_metadata
except ImportError:
    # For everyone else
    import importlib_metadata

__version__ = importlib_metadata.version("encord")
