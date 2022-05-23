"""
Reading project labels
======================

This example shows you how to read labels from your project.

.. raw:: html

   <details>
   <summary><a>Utility code</a></summary>
"""
# sphinx_gallery_thumbnail_path = 'images/end-to-end-thumbs/product-data.svg'
import uuid
from datetime import datetime

import pytz

GMT_TIMEZONE = pytz.timezone("GMT")
DATETIME_STRING_FORMAT = "%a, %d %b %Y %H:%M:%S %Z"


# === UTILITIES === #
def __get_timestamp():
    now = datetime.now()
    new_timezone_timestamp = now.astimezone(GMT_TIMEZONE)
    return new_timezone_timestamp.strftime(DATETIME_STRING_FORMAT)


def __lower_snake_case(s: str):
    return "_".join(s.lower().split())


def make_object_dict(ont_obj, point=None, polygon=None, object_hash=None):
    if object_hash is None:
        object_hash = str(uuid.uuid4())[:8]

    timestamp = __get_timestamp()
    object_dict = {
        "name": ont_obj.get("name"),
        "color": ont_obj.get("color"),
        "value": __lower_snake_case(ont_obj.get("name")),
        "createdAt": timestamp,
        "createdBy": "robot@cord.tech",
        "confidence": 1,
        "objectHash": object_hash,
        "featureHash": ont_obj["featureNodeHash"],
        "lastEditedAt": timestamp,
        "lastEditedBy": "robot@cord.tech",
        "manualAnnotation": False,
        "reviews": [],
    }
    if polygon:
        object_dict["shape"] = "polygon"
        object_dict["polygon"] = {
            str(i): {"x": round(polygon[i, 0], 4), "y": round(polygon[i, 1], 4)} for i in range(polygon.shape[0])
        }

    if point:
        object_dict["shape"] = "point"
        object_dict["point"] = {"0": {"x": round(point[0], 4), "y": round(point[1], 4)}}

    return object_dict


#%%
#
# .. raw:: html
#
#    </details>
