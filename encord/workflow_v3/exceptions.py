"""Errors specific to native workflow operations."""

from encord.exceptions import EncordException


class StaleTaskError(EncordException):
    """A requested task is no longer live, missing or belongs to another project.

    This does not confirm that an earlier submission succeeded.
    """
