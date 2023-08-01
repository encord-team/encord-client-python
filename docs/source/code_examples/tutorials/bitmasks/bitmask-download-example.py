import cv2
import numpy as np

from encord import EncordUserClient

# Instantiate Encord client and get a project using project hash
user_client = EncordUserClient.create_with_ssh_private_key("<your_private_key>")
project = user_client.get_project("<project_hash>")

# Obtain labels for the media of interest
label_row = project.list_label_rows_v2()[0]
label_row.initialise_labels()

# Find annotation
# In this example, it is just a first object on a first frame
object_with_bitmask_annotation = label_row.get_frame_views()[
    0
].get_object_instances()[0]

# Get a bitmask annotation
# In this example, it is a first annotation on the object
bitmask_annotation = object_with_bitmask_annotation.get_annotations()[0]

# Convert bitmask to a numpy array
bitmask_annotation_array = bitmask_annotation.coordinates.to_numpy_array()

# Obtained array is a binary mask, so to work with it as an image,
# it is necessary to convert it to a different datatype and scale

numpy_coordinates_to_write = bitmask_annotation_array.astype(np.uint8)
numpy_coordinates_to_write[numpy_coordinates_to_write == 1] = 255

# And now we can save the mask as a grayscale image
cv2.imwrite("./mask_as_an_image.png", numpy_coordinates_to_write)
