ENCORD_CONTACT_SUPPORT_EMAIL = "support@encord.com"


def _get_dict_without_none_keys(d: dict) -> dict:
    """Remove keys with value None from a dictionary. Does not change the dict in place."""
    return {k: v for k, v in d.items() if v is not None}
