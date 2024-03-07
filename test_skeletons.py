# %%
%load_ext autoreload
%autoreload 2
import os
import encord
from encord import EncordUserClient
from encord.utilities.project_user import ProjectUserRole
from encord.orm.skeleton_template import SkeletonTemplateORM, SkeletonTemplatesORM
from encord.objects.coordinates import SkeletonCoordinate
# %%
client = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=os.environ["ENCORD_DEV_SSH_KEY"], domain="http://localhost:6969"
)
client.get_projects()
SKELETON_PROJECT_HASH = "2a757614-52ce-4153-ab38-85f85b00df7f"
project = client.get_project("2a757614-52ce-4153-ab38-85f85b00df7f")
# %%
ontology = client.get_ontology("44c2969f-b8e3-4fd9-8801-a1e4df38cc27")
# %%
skeleton_templates = ontology._get_skeleton_templates()
# %%
skeleton_template = skeleton_templates[0]
# %%
coords = [SkeletonCoordinate(
                x=0,
                y=0,
                name="point_0",
                value="point_0",
                color="#000000",
                featureHash="",
            ),
            SkeletonCoordinate(
                x=0,
                y=0.5,
                name="point_1",
                value="point_1",
                color="#000000",
                featureHash="",
            ),
            SkeletonCoordinate(
                x=0.25,
                y=0.25,
                name="point_2",
                value="point_2",
                color="#000000",
                featureHash=""
            )]
# %%
instance = skeleton_template.create_instance(coords)
instance
# %%
from encord.objects.skeleton_template import SkeletonTemplate
# %%
template = SkeletonTemplate(
    name="Jim",
    width=100,
    height=100,
    skeleton={"0": SkeletonCoordinate(x=0,y=0,name="point_0"), "1": SkeletonCoordinate(x=1,y=1,name="point_1")},
    skeletonEdges={"0":{"1": {"color": "#00000"}}},
)
# %%
from encord.objects.ontology_structure import OntologyStructure
from encord.objects.ontology_object import Object
from encord.objects.common import Shape
# %%
ont_structure = OntologyStructure()
ont_structure.add_object(name="Jim", shape=Shape.SKELETON)
# %%
ontology = client.create_ontology(title="Jim", structure=ont_structure, skeleton_templates=[template])
# %%
from encord.ontology import Ontology
client.querier.basic_delete(Ontology, uid=ontology.ontology_hash)
# %%
