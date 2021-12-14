import os
import subprocess
import time
from typing import List

import pytest

from cord.client import CordClient
from cord.orm.dataset import DatasetType, DatasetAPIKey, DatasetScope, Dataset, ImageGroupOCR
from cord.user_client import CordUserClient
from PIL import Image

from sdk_tests.test_data.dataset_tests_constants import GCP_INTEGRATION_TITLE, \
    AWS_INTEGRATION_TITLE, GCP_TEST_VIDEOS_LINKS, GCP_TEST_IMAGE_GROUPS_LINKS, AWS_TEST_VIDEOS_LINKS, \
    AWS_TEST_IMAGE_GROUPS_LINKS, GCP_TEXT_IMAGE_GROUP_LINKS, TEXT_IMAGES_DATASET_RESOURCE_DATASET_HASH_STAGING, \
    TEXT_IMAGES_DATASET_RESOURCE_DATASET_HASH_DEV

DEFAULT_DATASET_TITLE = "test_dataset"
VIDEO_1 = "test_video1.mp4"
VIDEO_2 = "test_video2.mp4"
VIDEO_3 = "test_video3.mp4"
IMAGE_1 = "test_image1.png"
IMAGE_2 = "test_image2.png"
IMAGE_3 = "test_image3.png"


@pytest.fixture
def keys():
    private_key = os.environ.get("PRIVATE_KEY")
    env = os.environ.get("ENV")

    if env == "STAGING":
        cord_domain = 'https://staging.api.cord.tech'

    elif env == "DEV":
        cord_domain = 'https://dev.api.cord.tech'

    else:
        cord_domain = 'http://127.0.0.1:8000'

    return private_key, cord_domain, env


def create_dataset_client_from_dataset_hash(private_key: str,
                                            domain: str,
                                            dataset_hash: str):
    user_client = CordUserClient.create_with_ssh_private_key(private_key, domain=domain)
    api_key = user_client.create_dataset_api_key(dataset_hash, "test api key", [scope for scope in DatasetScope])
    client = CordClient.initialise(dataset_hash, api_key.api_key, domain=domain)
    return client

def create_template_dataset(private_key: str,
                            domain: str,
                            title: str = DEFAULT_DATASET_TITLE,
                            type: DatasetType = DatasetType.CORD_STORAGE):
    user_client = CordUserClient.create_with_ssh_private_key(private_key, domain=domain)
    dataset = user_client.create_dataset(title, type)
    dataset_hash = dataset["dataset_hash"]
    api_key = user_client.create_dataset_api_key(dataset_hash, "test api key", [scope for scope in DatasetScope])
    client = CordClient.initialise(dataset_hash, api_key.api_key, domain=domain)
    return dataset, client


def create_mp4_file(filenames: List[str]):
    for filename in filenames:
        # returns path to mp4 file
        command = f'ffmpeg -y -f lavfi -i testsrc=size=1920x1080:rate=1 -vf hue=s=0 -vcodec libx264 -preset superfast -tune zerolatency -pix_fmt yuv420p -t 100 -movflags +faststart {filename}'
        subprocess.run(command, shell=True)


def create_image_file(filenames: List[str]):
    for filename in filenames:
        img = Image.new("RGB", (800, 1280), (255, 255, 255))
        img.save(filename, "PNG")


def delete_files(filenames: List[str]):
    for filename in filenames:
        os.remove(filename)


def construct_cloud_integration_query(video_links: List[str], image_groups_links: List[List[str]], cloud_name: str):
    videos = []
    image_groups = []
    for video_link in video_links:
        videos.append({"objectUrl": video_link})

    for (image_group_no, image_group) in enumerate(image_groups_links, 1):
        image_group_dict = {"title": f"{cloud_name} image group {image_group_no}"}
        for (image_no, image_link) in enumerate(image_group):
            key = f"objectUrl_{image_no}"
            image_group_dict[key] = image_link
        image_groups.append(image_group_dict)

    return {"videos": videos, "image_groups": image_groups}


def get_gcp_integration_id(client):
    integrations = client.get_cloud_integrations()

    if integrations[0].title == GCP_INTEGRATION_TITLE:
        return integrations[0].id
    elif integrations[1].title == GCP_INTEGRATION_TITLE:
        return integrations[1].id
    else:
        raise RuntimeError("Could not obtain GCP integration ID")


def get_aws_integration_id(client):
    integrations = client.get_cloud_integrations()

    if integrations[0].title == AWS_INTEGRATION_TITLE:
        return integrations[0].id
    elif integrations[1].title == AWS_INTEGRATION_TITLE:
        return integrations[1].id
    else:
        raise RuntimeError("Could not obtain GCP integration ID")


def assert_image_ocr_contains_text(image_ocr: ImageGroupOCR):
    ocr_texts = image_ocr.processed_texts["ocr_texts"]

    assert len(ocr_texts) > 0

    for ocr_text in ocr_texts:
        text = ocr_text["text"]
        assert isinstance(text, str)

        bounding_box = ocr_text["boundingBox"]
        assert isinstance(bounding_box["h"], float)
        assert isinstance(bounding_box["w"], float)
        assert isinstance(bounding_box["x"], float)
        assert isinstance(bounding_box["y"], float)



def get_text_images_dataset_hash(env):
    if env == "STAGING":
        return TEXT_IMAGES_DATASET_RESOURCE_DATASET_HASH_STAGING

    return TEXT_IMAGES_DATASET_RESOURCE_DATASET_HASH_DEV


def test_create_dataset(keys):
    private_key = keys[0]
    cord_domain = keys[1]
    dataset_title = "test dataset"
    user_client = CordUserClient.create_with_ssh_private_key(private_key, domain=cord_domain)
    dataset = user_client.create_dataset(dataset_title, DatasetType.CORD_STORAGE)

    assert isinstance(dataset, dict)
    assert dataset["title"] == dataset_title
    assert dataset["type"] == DatasetType.CORD_STORAGE
    assert isinstance(dataset["dataset_hash"], str)


def test_create_dataset_api_key(keys):
    private_key = keys[0]
    cord_domain = keys[1]
    user_client = CordUserClient.create_with_ssh_private_key(private_key, domain=cord_domain)
    dataset = user_client.create_dataset("test dataset", DatasetType.CORD_STORAGE)
    dataset_hash = dataset["dataset_hash"]

    api_key = user_client.create_dataset_api_key(dataset_hash, "test api key", [scope for scope in DatasetScope])

    assert isinstance(api_key, DatasetAPIKey)
    assert isinstance(api_key.api_key, str)


def test_get_dataset_api_keys(keys):
    private_key = keys[0]
    cord_domain = keys[1]
    user_client = CordUserClient.create_with_ssh_private_key(private_key, domain=cord_domain)
    dataset = user_client.create_dataset("test dataset", DatasetType.CORD_STORAGE)
    dataset_hash = dataset["dataset_hash"]
    api_key_1 = user_client.create_dataset_api_key(dataset_hash, "test api key", [DatasetScope.READ])
    api_key_2 = user_client.create_dataset_api_key(dataset_hash, "test api key", [DatasetScope.WRITE])

    all_api_keys = user_client.get_dataset_api_keys(dataset_hash)

    assert api_key_1 in all_api_keys
    assert api_key_2 in all_api_keys


def test_get_dataset(keys):
    private_key = keys[0]
    cord_domain = keys[1]
    user_client = CordUserClient.create_with_ssh_private_key(private_key, domain=cord_domain)
    dataset = user_client.create_dataset(DEFAULT_DATASET_TITLE, DatasetType.CORD_STORAGE)
    dataset_hash = dataset["dataset_hash"]
    api_key = user_client.create_dataset_api_key(dataset_hash, "test api key", [scope for scope in DatasetScope])
    client = CordClient.initialise(dataset_hash, api_key.api_key, domain=cord_domain)

    dataset = client.get_dataset()

    assert isinstance(dataset, Dataset)
    assert dataset["title"] == DEFAULT_DATASET_TITLE
    assert dataset["dataset_type"] == DatasetType.CORD_STORAGE.name


def test_upload_video(keys):
    private_key = keys[0]
    cord_domain = keys[1]
    dataset, client = create_template_dataset(private_key, cord_domain)
    create_mp4_file([VIDEO_1])

    upload_video = client.upload_video(VIDEO_1)
    dataset = client.get_dataset()

    data_rows = dataset["data_rows"][0]
    assert isinstance(data_rows["data_hash"], str)
    assert data_rows["data_title"] == VIDEO_1
    assert data_rows["data_type"] == 'VIDEO'
    assert upload_video

    delete_files([VIDEO_1])


def test_upload_multiple_videos(keys):
    private_key = keys[0]
    cord_domain = keys[1]
    dataset, client = create_template_dataset(private_key, cord_domain)
    create_mp4_file([VIDEO_1, VIDEO_2, VIDEO_3])

    upload_video1 = client.upload_video(VIDEO_1)
    upload_video2 = client.upload_video(VIDEO_2)
    upload_video3 = client.upload_video(VIDEO_3)
    dataset = client.get_dataset()

    assert upload_video1
    assert upload_video2
    assert upload_video3
    data_rows = dataset["data_rows"]
    assert len(data_rows) == 3
    video_titles = (data_rows[0]["data_title"], data_rows[1]["data_title"], data_rows[2]["data_title"])
    assert VIDEO_1 in video_titles and VIDEO_2 in video_titles and VIDEO_3 in video_titles
    for video_info in data_rows:
        assert isinstance(video_info["data_hash"], str)
        assert video_info["data_type"] == 'VIDEO'

    delete_files([VIDEO_1, VIDEO_2, VIDEO_3])


def test_create_image_group(keys):
    private_key = keys[0]
    cord_domain = keys[1]
    dataset, client = create_template_dataset(private_key, cord_domain)
    create_image_file([IMAGE_1, IMAGE_2, IMAGE_3])

    image_group = client.create_image_group([IMAGE_1, IMAGE_2, IMAGE_3])
    dataset = client.get_dataset()

    data_rows = dataset["data_rows"][0]
    assert isinstance(image_group[0], dict)
    image_group = image_group[0]
    assert isinstance(image_group["data_hash"], str)
    assert isinstance(image_group["title"], str)
    assert isinstance(data_rows["data_hash"], str)
    assert isinstance(data_rows["data_title"], str)
    assert data_rows["data_type"] == 'IMG_GROUP'
    assert data_rows["data_hash"] == image_group["data_hash"]
    assert data_rows["data_title"] == image_group["title"]

    delete_files([IMAGE_1, IMAGE_2, IMAGE_3])


def test_delete_image_group_from_dataset(keys):
    private_key = keys[0]
    cord_domain = keys[1]
    dataset, client = create_template_dataset(private_key, cord_domain)
    create_image_file([IMAGE_1, IMAGE_2, IMAGE_3])
    image_group = client.create_image_group([IMAGE_1, IMAGE_2, IMAGE_3])
    image_group = image_group[0]
    data_hash = image_group["data_hash"]
    dataset_before_delete = client.get_dataset()

    client.delete_image_group(data_hash)

    dataset_after_delete = client.get_dataset()
    assert len(dataset_before_delete["data_rows"]) == 1
    assert len(dataset_after_delete["data_rows"]) == 0

    delete_files([IMAGE_1, IMAGE_2, IMAGE_3])


def test_delete_video_from_dataset(keys):
    private_key = keys[0]
    cord_domain = keys[1]
    dataset, client = create_template_dataset(private_key, cord_domain)
    create_mp4_file([VIDEO_1])
    client.upload_video(VIDEO_1)
    dataset_before_delete = client.get_dataset()
    data_hash = dataset_before_delete["data_rows"][0]["data_hash"]

    client.delete_data([data_hash])

    dataset_after_delete = client.get_dataset()
    assert len(dataset_before_delete["data_rows"]) == 1
    assert len(dataset_after_delete["data_rows"]) == 0

    delete_files([VIDEO_1])


def test_delete_multiple_videos_from_dataset(keys):
    private_key = keys[0]
    cord_domain = keys[1]
    dataset, client = create_template_dataset(private_key, cord_domain)
    create_mp4_file([VIDEO_1, VIDEO_2, VIDEO_3])
    client.upload_video(VIDEO_1)
    client.upload_video(VIDEO_2)
    client.upload_video(VIDEO_3)
    dataset_before_delete = client.get_dataset()
    data_hash1 = dataset_before_delete["data_rows"][0]["data_hash"]
    data_hash2 = dataset_before_delete["data_rows"][1]["data_hash"]

    client.delete_data([data_hash1, data_hash2])

    dataset_after_delete = client.get_dataset()
    assert len(dataset_before_delete["data_rows"]) == 3
    assert len(dataset_after_delete["data_rows"]) == 1

    delete_files([VIDEO_1, VIDEO_2, VIDEO_3])


def test_get_cloud_integration_ids_for_aws_and_gcp(keys):
    private_key = keys[0]
    cord_domain = keys[1]
    dataset, client = create_template_dataset(private_key, cord_domain)

    integration = client.get_cloud_integrations()

    assert len(integration) == 2
    assert isinstance(integration[0].id, str)
    titles = (integration[0].title, integration[1].title)
    assert GCP_INTEGRATION_TITLE in titles
    assert AWS_INTEGRATION_TITLE in titles


def test_add_private_data_gcp_to_dataset(keys):
    private_key = keys[0]
    cord_domain = keys[1]
    dataset, client = create_template_dataset(private_key, cord_domain, "Test dataset gcp", DatasetType.GCP)
    integration_query = construct_cloud_integration_query(GCP_TEST_VIDEOS_LINKS, GCP_TEST_IMAGE_GROUPS_LINKS, "GCP")
    integration_id = get_gcp_integration_id(client)

    client.add_private_data_to_dataset(integration_id, integration_query)

    updated_dataset = client.get_dataset()
    assert len(updated_dataset["data_rows"]) == len(GCP_TEST_VIDEOS_LINKS) + len(GCP_TEST_IMAGE_GROUPS_LINKS)


def test_add_private_data_aws_to_dataset(keys):
    private_key = keys[0]
    cord_domain = keys[1]
    dataset, client = create_template_dataset(private_key, cord_domain, "Test dataset aws", DatasetType.AWS)
    integration_query = construct_cloud_integration_query(AWS_TEST_VIDEOS_LINKS, AWS_TEST_IMAGE_GROUPS_LINKS, "AWS")
    integration_id = get_aws_integration_id(client)

    client.add_private_data_to_dataset(integration_id, integration_query)

    updated_dataset = client.get_dataset()
    assert len(updated_dataset["data_rows"]) == len(AWS_TEST_VIDEOS_LINKS) + len(AWS_TEST_IMAGE_GROUPS_LINKS)


def test_re_encode_video(keys):
    private_key = keys[0]
    cord_domain = keys[1]
    dataset, client = create_template_dataset(private_key, cord_domain)
    create_mp4_file([VIDEO_1])
    client.upload_video(VIDEO_1)
    dataset = client.get_dataset()
    data_hash = dataset["data_rows"][0]["data_hash"]

    job_id = client.re_encode_data([data_hash])

    assert isinstance(job_id, int)
    delete_files([VIDEO_1])


def test_obtain_re_encode_video_status_and_re_encoded_link(keys):
    private_key = keys[0]
    cord_domain = keys[1]
    dataset, client = create_template_dataset(private_key, cord_domain)
    create_mp4_file([VIDEO_1])
    client.upload_video(VIDEO_1)
    dataset = client.get_dataset()
    data_hash = dataset["data_rows"][0]["data_hash"]
    job_id = client.re_encode_data([data_hash])

    re_encode_status = client.re_encode_data_status(job_id)
    assert re_encode_status.status == 'SUBMITTED'
    while re_encode_status.status == 'SUBMITTED':
        re_encode_status = client.re_encode_data_status(job_id)
        time.sleep(0.05)

    assert re_encode_status.status == 'DONE'
    result = re_encode_status.result
    assert len(result) == 1
    result = result[0]
    assert isinstance(result.data_hash, str)
    assert isinstance(result.signed_url, str)
    assert isinstance(result.bucket_path, str)

    delete_files([VIDEO_1])


def test_run_ocr(keys):
    private_key = keys[0]
    cord_domain = keys[1]
    env = keys[2]
    dataset_hash = get_text_images_dataset_hash(env)
    client = create_dataset_client_from_dataset_hash(private_key, cord_domain, dataset_hash)
    dataset = client.get_dataset()
    data_hash = dataset["data_rows"][0]["data_hash"]

    ocr_result = client.run_ocr(data_hash)

    assert len(ocr_result) > 0

    for image_ocr in ocr_result:
        assert_image_ocr_contains_text(image_ocr)

