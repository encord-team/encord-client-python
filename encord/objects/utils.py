def _decode_nested_uid(nested_uid: list) -> str:
    return ".".join([str(uid) for uid in nested_uid])
