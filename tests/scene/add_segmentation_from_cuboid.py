# %%

from dataclasses import dataclass

from encord.objects import Object
from encord.objects.coordinates import CuboidCoordinates
from encord.objects.frames import Range, frames_to_ranges
from encord.scene import points_in_cuboid_indices
from encord.user_client import EncordUserClient


@dataclass
class Config:
    folder_uuid: str  # folder containing the scene storage item
    project_hash: str
    data_hash: str

    # ontology
    cuboid_title: str
    segm_title: str

    # client
    domain: str
    ssh_key_path: str


dev_cgf = Config(
    folder_uuid="29b4cc53-6910-4fe9-88e4-61ca573ec9af",
    project_hash="8215d182-dce2-4296-b54a-c6bf062ac53d",
    data_hash="b29d5763-1fba-4047-80b6-1db919c2a8d7",
    # https://dev.encord.com/label_editor/8215d182-dce2-4296-b54a-c6bf062ac53d/b29d5763-1fba-4047-80b6-1db919c2a8d7/
    cuboid_title="Car",
    segm_title="Segmentation B",
    domain="http://localhost:6969",
    ssh_key_path="/users/arthur/.ssh/encord-dev-key",
)


prod_cfg = Config(
    project_hash="11c14a52-19a8-43c2-a60b-ac46a2c9c3f0",
    data_hash="4ed80d4a-cf86-4e0b-b17d-4e3fc86bfe88",
    # https://app.encord.com/label_editor/11c14a52-19a8-43c2-a60b-ac46a2c9c3f0/4ed80d4a-cf86-4e0b-b17d-4e3fc86bfe88?selectedStageUuid=1252fdb8-93cb-41a2-b341-b83ab97b5277&limit=10
    folder_uuid="d95331fa-2f40-4c5a-bded-0b9be2fbae6b",
    cuboid_title="Car",
    segm_title="Segmentation",
    domain="https://api.encord.com",
    ssh_key_path="/users/arthur/.ssh/encord-prod-key",
)


c = dev_cgf

client = EncordUserClient.create_with_ssh_private_key(domain=c.domain, ssh_private_key_path=c.ssh_key_path)
folder = client.get_storage_folder(c.folder_uuid)
items = list(folder.list_items())

# %%
project = client.get_project(c.project_hash)
row = project.list_label_rows_v2(data_hashes=[c.data_hash])[0]
item = [i for i in items if i.uuid == row.backing_item_uuid][0]
scene = item.get_scene()

cuboid_cls = row.ontology_structure.get_child_by_title(c.cuboid_title, type_=Object)
segm_cls = row.ontology_structure.get_child_by_title(c.segm_title, type_=Object)
row.initialise_labels()


# %%

# Get the LIDAR_TOP point cloud stream from the scene
pc_streams = scene.get_streams("point_cloud")
print(f"Found {len(pc_streams)} point cloud streams: {[s.stream_id for s in pc_streams]}")

pc_stream = next((s for s in pc_streams if s.stream_id == "LIDAR_TOP"), None)
assert pc_stream is not None, "LIDAR_TOP stream not found"
stream_id = pc_stream.stream_id

print(f"Using point cloud stream: {stream_id} with {pc_stream.num_events} events")

# Process each cuboid annotation
for obj in row.get_object_instances():
    for ann in obj.get_annotations():
        if isinstance(ann.coordinates, CuboidCoordinates):
            frame_idx = ann.frame
            cuboid = ann.coordinates
            print(f"Processing cuboid at frame {frame_idx}: pos={cuboid.position}, size={cuboid.size}")

            # Load point cloud in world coordinates (cuboids are in world/origin coords)
            point_cloud = scene.load_point_cloud_in_world_coordinates(stream_id, event_index=frame_idx)
            print(f"  Loaded {point_cloud.num_points} points (world coordinates)")


            # Find points inside the cuboid
            indices = points_in_cuboid_indices(point_cloud.points, cuboid)
            print(f"  Found {len(indices)} points inside cuboid")

            if len(indices) == 0:
                print("  Skipping - no points inside cuboid")
                continue

            # Convert indices to ranges for efficient storage
            ranges = frames_to_ranges(indices.tolist())
            print(f"  Compressed to {len(ranges)} ranges")

            # Create segmentation instance and add to the point cloud space
            segm_obj = segm_cls.create_instance()
            pcd_space = row.get_space(stream_id=stream_id, event_index=frame_idx, type_="point_cloud")
            pcd_space.put_object_instance(segm_obj, ranges)
            print(f"  Added segmentation annotation")

# Save the labels
row.save()
print("\nDone! Labels saved.")


# %%
