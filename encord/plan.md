- We have a project where we have cuboids and point cloud segmentations.
- I need to write a script that
  1. Takes in the list of cuboids in a Scene (on all its frames)
  2. Gets the cuboid positions
  3. Gets the point cloud segmentations for each frame
  4. Determines which points are "inside" the cuboid for each frame
  5. Use this to create a segmentation right where the cuboid is located.

- As a first step, we don't need to worry about object instances (e.g. a cuboid being on many frames), we can just deal with a single cuboid to see if the coordinates are correct.

- This is not possible yet because:
  - We don't have access to the point cloud urls in the SDK. We need signed URLs, and also some libraries to parse the point clouds.
  - We don't have access to all the FORs (Frame of references) needed to convert between coordinate systems. The cuboids are in
    world coordinates, the the point clouds will be in sensor/lidar coordinates. We need to be able to convert between these.

  Therefore, we need to start designing a "Scene" SDK. Some of the elements we need are:
  - Ability to download all the files in a scene via the signed urls
  - Ability to access the point clouds as numpy arrays (we can only handle .pcd files for now)
  - Ability to see the "Graph" of the scenes, where the root is the origin, and the nodes can be FORs
  - Ability to get the FORs as numpy transformation matrices
  - Ability to "traverse" the graph to get the FORs we need to convert between coordinate systems

For now, we don't need to include everything from the model into the SDK. the main concerns are the point clouds and the FORs.

The first step will be to include a public endpoint to call `get_signed_scene_from_storage`, which will return the scene inforamtion with signed urls. That new endpoint should be in /Users/arthur/repos/backend/backend1/projects/api-server/src/cord/apiserver/public_api_v2/routers/storage.py. The client side (e.g. in /Users/arthur/repos/encord-client-python/encord/storage.py) will need to be updated to call this new endpoint.

Then, the new class "Scene" in the SDK can be created from the response.
You can use this JSON file: /Users/arthur/repos/encord-client-python/encord/nuscenes.json as a `Scene` example. The URLs are signed. You should use this to write unit tests, it should be a good starting point.


Relevant Scene information:

- /Users/arthur/repos/backend/backend1/projects/api-server/src/cord/apiserver/business_logic/modalities/scenes: this is the main folder where you can find the Scene model in the backend. The main internal scene representation is "Scene", which is then located in the database in`scenes.scene`.
- /Users/arthur/repos/frontend/frontend-1/packages/three-dee/lib/scene: contains a lot of FE side logic. This is the application that visualises and annotates the scenes in 3D.
- in the BE repository, you can look at the diff in the `ov/al/spike/1` branch. It contains some code that contains some of what we want to do, including making a scene graph, parsing the files, etc.
