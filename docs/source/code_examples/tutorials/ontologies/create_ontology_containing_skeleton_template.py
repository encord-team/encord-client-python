import os

from encord import EncordUserClient

from encord.objects.skeleton_template import SkeletonTemplate, SkeletonCoordinates, SkeletonTemplateCoordinate
from encord.objects.common import Shape
from encord.objects.ontology_structure import OntologyStructure
user_client = EncordUserClient.create_with_ssh_private_key(ssh_private_key_path=os.getenv("ENCORD_SSH_KEY"))

SKELETON_TEMPLATE_NAME = "Line"
coordinates = [
            SkeletonTemplateCoordinate(x=0, y=0, name="point_0"),
            SkeletonTemplateCoordinate(x=1, y=1, name="point_1"),
        ]
edges = {"0": {"1": {"color": "#00000"}}}
skeleton_template = SkeletonTemplate(
    name=SKELETON_TEMPLATE_NAME,
    width=100,
    height=100,
    skeleton={str(i): coord for (i, coord) in enumerate(coordinates)},
    skeleton_edges=edges,
)
#Make a structure, add the object and the template
ont_structure = OntologyStructure()
ont_structure.add_object(name=SKELETON_TEMPLATE_NAME, shape=Shape.SKELETON)
ont_structure.add_skeleton_template(skeleton_template)

#Upload ontology to platform
ontology = user_client.create_ontology(title="Skeleton Template Line Example", structure=ont_structure)
