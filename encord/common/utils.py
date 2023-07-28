from __future__ import annotations

import re


def snake_to_camel(snake_case_str: str) -> str:
    camel = re.sub("([0-9A-Za-z])_(?=[0-9A-Z])", lambda m: m.group(1), snake_case_str.title())
    return re.sub("(^_*[A-Z])", lambda m: m.group(1).lower(), camel)
