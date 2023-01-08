"""
Deidentify dicom files
======================

Use this script to deidentify dicom files in external storage.
"""

from pathlib import Path
from typing import List

from encord import EncordUserClient


def deidentify(
    integration_title: str,
    dicom_urls: List[str],
) -> List[str]:
    # Authentication: adapt the following line to your private key path
    private_key_path = Path.home() / ".ssh" / "id_ed25519"

    with private_key_path.open() as f:
        private_key = f.read()

    user_client = EncordUserClient.create_with_ssh_private_key(private_key)

    integration_hash = None

    # Find integration_hash for requested integration_title
    for integration in user_client.get_cloud_integrations():
        if integration.title == integration_title:
            integration_hash = integration.id

    if not integration_hash:
        raise Exception(
            f"Intgration with integration_title={integration_title} not found"
        )

    deidentified_dicom_urls = []

    for dicom_url in dicom_urls:
        # requesting deidentification with batch == 1
        deidentified_dicom_url = user_client.deidentify_dicom_files(
            dicom_urls=[dicom_url],
            integration_hash=integration_hash,
        )[0]
        print(f"Deidentified url: {deidentified_dicom_url}")
        deidentified_dicom_urls.append(deidentified_dicom_url)

    return deidentified_dicom_urls


_integration_title = "deid-demo-0dae9c7b-integration"
_dicom_urls = [
    "s3://deid-demo-0dae9c7b/dicom_0.dcm",
    "s3://deid-demo-0dae9c7b/dicom_1.dcm",
]
_deidentified_dicom_urls = deidentify(_integration_title, _dicom_urls)
