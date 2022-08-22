import json
import tempfile
from pathlib import Path

import pytest
import torch
import torchvision
from deepdiff import DeepDiff

from encord.objects.common import Shape
from encord.objects.ontology_object import Object
from encord.objects.ontology_structure import OntologyStructure
from encord.transformers.coco.coco_encoder import (
    CocoEncoder,
    EncodingError,
    download_file,
    extract_frames,
)
from tests.transformers.coco.data.project_1 import (
    cute_cat_mp4,
    existing_image_group,
    image_group_a2198,
    image_group_fded8,
    output_download_all_all_video_frames,
    output_download_all_no_videos,
    output_download_all_only_annotated_images,
    output_no_downloads_no_videos,
    output_no_downloads_with_annotated_videos,
    output_no_input_labels,
    project_1_ontology,
)

ENABLE_INTEGRATION_TESTS = False
ENABLE_MANUAL_TESTS = True


@pytest.mark.skipif(not ENABLE_INTEGRATION_TESTS, reason="Integration tests are currently not enabled.")
def test_coco_transcoder_all_downloads():
    labels = [image_group_a2198, existing_image_group, image_group_fded8, cute_cat_mp4]
    ontology = project_1_ontology

    with tempfile.TemporaryDirectory() as tmp_dir:
        coco_annotations = CocoEncoder(labels, ontology).encode(
            download_files=True,
            download_file_path=Path(tmp_dir),
            include_videos=True,
            include_unannotated_videos=False,
        )

    assert not DeepDiff(coco_annotations, output_download_all_only_annotated_images)


@pytest.mark.skipif(not ENABLE_INTEGRATION_TESTS, reason="Integration tests are currently not enabled.")
def test_coco_transcoder_all_downloads_with_videos():
    labels = [image_group_a2198, existing_image_group, image_group_fded8, cute_cat_mp4]
    ontology = project_1_ontology

    with tempfile.TemporaryDirectory() as tmp_dir:
        coco_annotations = CocoEncoder(labels, ontology).encode(
            download_files=True,
            download_file_path=Path(tmp_dir),
            include_videos=True,
            include_unannotated_videos=True,
        )

    assert not DeepDiff(coco_annotations, output_download_all_all_video_frames)


@pytest.mark.skipif(not ENABLE_INTEGRATION_TESTS, reason="Integration tests are currently not enabled.")
def test_coco_transcoder_all_downloads_no_videos():
    labels = [image_group_a2198, existing_image_group, image_group_fded8, cute_cat_mp4]
    ontology = project_1_ontology

    with tempfile.TemporaryDirectory() as tmp_dir:
        coco_annotations = CocoEncoder(labels, ontology).encode(
            download_files=True,
            download_file_path=Path(tmp_dir),
            include_videos=False,
            include_unannotated_videos=False,
        )

    assert not DeepDiff(coco_annotations, output_download_all_no_videos)


def test_coco_transcoder_no_downloads_e2e():
    labels = [image_group_a2198, existing_image_group, image_group_fded8, cute_cat_mp4]
    ontology = project_1_ontology

    coco_annotations = CocoEncoder(labels, ontology).encode(
        download_files=False,
        include_videos=False,
        include_unannotated_videos=False,
    )

    assert not DeepDiff(coco_annotations, output_no_downloads_no_videos)


# DENIS: TODO: next up with a mode where we include the videos, but they are not downloaded, just need
#   some made up format for that, possibly even exactly the same format as we have now, and scrap the image names.
#   that would also unblock Javi to not download files every time possibly.


def test_coco_transcoder_no_downloads_with_videos_annotated_only():
    labels = [image_group_a2198, existing_image_group, image_group_fded8, cute_cat_mp4]
    ontology = project_1_ontology

    coco_annotations = CocoEncoder(labels, ontology).encode(
        download_files=False,
        include_videos=True,
        include_unannotated_videos=False,
    )

    assert not DeepDiff(coco_annotations, output_no_downloads_with_annotated_videos)


def test_coco_transcoder_no_downloads_with_videos_all_videos():
    labels = [image_group_a2198, existing_image_group, image_group_fded8, cute_cat_mp4]
    ontology = project_1_ontology

    coco_annotations = CocoEncoder(labels, ontology).encode(
        download_files=False,
        download_file_path=Path("data/torch_test"),
        include_videos=True,
        include_unannotated_videos=True,
    )

    assert not DeepDiff(coco_annotations, output_download_all_all_video_frames)


def test_coco_transcoder_no_labels():
    labels = []
    ontology = project_1_ontology

    coco_annotations = CocoEncoder(labels, ontology).encode(
        download_files=False,
        download_file_path=Path("data/torch_test"),
        include_videos=True,
        include_unannotated_videos=False,
    )

    assert not DeepDiff(coco_annotations, output_no_input_labels)


def test_coco_transcoder_wrong_ontology():
    labels = [image_group_a2198, existing_image_group, image_group_fded8, cute_cat_mp4]
    ontology = OntologyStructure()

    with pytest.raises(EncodingError):
        CocoEncoder(labels, ontology).encode(
            download_files=False,
            download_file_path=Path("data/torch_test"),
            include_videos=True,
            include_unannotated_videos=False,
        )


@pytest.mark.skipif(not ENABLE_MANUAL_TESTS, reason="This is a manual test")
def test_project_1_transcoders():
    labels = [image_group_a2198]
    ontology = project_1_ontology

    coco_format = CocoEncoder(labels, ontology).encode(
        download_files=True,
        download_file_path=Path("data/torch_test"),
        include_videos=True,
        include_unannotated_videos=False,
    )

    """
    CocoDecoder(coco_file, mappings)
    
    Notes with Eric
    * for imports, how does the mappings look? 
        * for example, we likely want to have image id to fields like "iscrowd" that do not make sense on our platform.
    * we can wait on skeleton and other "novel" types.
    * Have this within the export tab in the GUI. => so they can download the coco.json
    * Can we have some example datasets/projects with sample scripts? 
    """

    print(coco_format)
    with open("data/torch_test/coco.json", "w") as f:
        json.dump(coco_format, f)


@pytest.mark.skipif(not ENABLE_MANUAL_TESTS, reason="This is a manual test")
def test_run_torch():
    torch_output = torchvision.datasets.CocoDetection("data/torch_test", "data/torch_test/coco.json")
    print(len(torch_output))

    # img, target = next(iter(torch_output))
    # print("hello")
    import matplotlib.pyplot as pyplot_

    #
    # pyplot_.imshow(img)
    # torch_output.coco.showAnns(target)
    # pyplot_.show()
    # print("")
    for i in torch_output:
        img, target = i
        pyplot_.imshow(img)
        torch_output.coco.showAnns(target)
        pyplot_.show()


# torch_output.coco.showAnns()
# matplotlib.pyplot.figure.


@pytest.mark.skipif(not ENABLE_MANUAL_TESTS, reason="This is a manual test")
def test_download_video():
    # DENIS: first download into a temporary directory.
    # download_file(
    #     "https://storage.googleapis.com/encord-local-dev.appspot.com/cord-videos-dev/lFW59RQ9jcT4vHZeG14m8QWJKug1/afe598fa-4bc0-43b2-907e-260dcc8cae7a?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=firebase-adminsdk-efw44%40encord-local-dev.iam.gserviceaccount.com%2F20220728%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20220728T165718Z&X-Goog-Expires=604800&X-Goog-SignedHeaders=host&X-Goog-Signature=b05dc93dd2ebfd18b39e246fe0cd2d7201983822684ae577057a293884afe3de4a06b049acca0e85c553603c6e06e68e6eb71d846bb520860f909a6ab13ee08daf856e577730b9e823a74400e293683fa21df19d4f2b1b939ee68995170680ee6c1dc0b1dbd9a51ed7d92fd7e1deb8eda47a61ef06b45185f4058a510bffa813b58766de3f8b333a5e512fb7ab7623801b3588a97046606963d24ba44c33f13df62ccd06d2d3a114d2952fbd1d46344941bfae7b5ac287fe761bd07990c1c3d061005a268af8df04fad19dac85cdbf09b57e45eb20d2948cd2ab834e075ea47ef1f815e18d16cb8e3e31a0dbedf31a669cebcbf0ce169bcc62003b2fbfc40dd5",
    #     Path("cute-cat.mp4"),
    # )

    # DENIS: then extract frames
    extract_frames(Path("cute-cat.mp4"), Path("cute_cat_images"))

    # DENIS: create as many indexes as there are instances of this:
    print(len(list(Path("cute_cat_images").iterdir())))
