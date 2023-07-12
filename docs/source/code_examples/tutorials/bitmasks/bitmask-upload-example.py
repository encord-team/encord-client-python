import numpy as np

from encord import EncordUserClient
from encord.objects import Object, OntologyStructure
from encord.objects.coordinates import BitmaskCoordinates

# Firstly, we need to prepare the mask itself.
# For simplicity, we can just mask the whole image
# Note, that the size of the mask must be identical to the size of the image
numpy_coordinates = np.ones((512, 512))

# we also need to make sure that the image is in boolean format
numpy_coordinates = numpy_coordinates.astype(bool)

# Now we can upload it with the following steps

# Instantiate Encord client and get a project using project hash
user_client = EncordUserClient.create_with_ssh_private_key("<your_private_key>")
project = user_client.get_project("<project_hash>")

# Obtain labels for the media of interest
# In this case, just a first image of the project
label_row = project.list_label_rows_v2()[0]
label_row.initialise_labels()

# Find a bitmask annotation object in the project ontology
ontology_structure: OntologyStructure = label_row.ontology_structure
bitmask_ontology_object: Object = ontology_structure.get_child_by_title(
    title="My bitmask feature", type_=Object
)

# Create the instance of this object - actual annotation
bitmask_ontology_object_instance = bitmask_ontology_object.create_instance()

# Set the bitmask as coordinates for the annotation
bitmask_ontology_object_instance.set_for_frames(
    # Create coordinates from provided numpy bitmask
    coordinates=BitmaskCoordinates(numpy_coordinates),
    # Add the bounding box to the first frame
    frames=0,
    # There are multiple additional fields that can be set optionally:
    manual_annotation=True,
)

# And assign the object instance to the label row
label_row.add_object_instance(bitmask_ontology_object_instance)

label_row.save()
