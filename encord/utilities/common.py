ENCORD_CONTACT_SUPPORT_EMAIL = "support@encord.com"


def _remove_none_keys(d: dict) -> dict:
    """Remove keys with value None from a dictionary."""
    return {k: v for k, v in d.items() if v is not None}
