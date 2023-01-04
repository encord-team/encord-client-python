import datetime
from typing import Any

import dateutil

ENCORD_CONTACT_SUPPORT_EMAIL = "support@encord.com"


def convert_str_date_to_datetime(data):
    data["created_at"] = dateutil.parser.isoparse(data["created_at"])
    data["last_edited_at"] = dateutil.parser.isoparse(data["last_edited_at"])
    return data
