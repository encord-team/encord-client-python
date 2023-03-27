from typing import List

from encord import Dataset, EncordUserClient
from encord.orm.cloud_integration import CloudIntegration
from encord.orm.dataset import (
    AddPrivateDataResponse,
    DatasetDataLongPolling,
    LongPollingStatus,
)

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)
dataset: Dataset = user_client.get_dataset("<dataset_hash>")

# Choose integration
integrations: List[CloudIntegration] = user_client.get_cloud_integrations()
print("Integration Options:")
print(integrations)

integration_idx: int = [i.title for i in integrations].index("AWS")
integration: str = integrations[integration_idx].id

use_simple_api: bool = True

# Check our documentation here: https://docs.encord.com/datasets/private-cloud-integration/#json-format
# to make sure you upload your data in the correct format

if use_simple_api:
    # using add_private_data_to_dataset will start upload job and await for it to finish,
    # then raise exception in case errors occur
    response: AddPrivateDataResponse = dataset.add_private_data_to_dataset(
        integration, "path/to/json/file.json"
    )
else:
    # using add_private_data_to_dataset_start will only initialize job
    upload_job_id: str = dataset.add_private_data_to_dataset_start(
        integration, "path/to/json/file.json"
    )

    # at this point user can save upload_job_id externally, exit python process and
    # check for status with add_private_data_to_dataset_get_result at any point in the future

    # one can get job status without awaiting the final response, with timeout_seconds=0
    # this will perform one quick call to encord backend for status check
    print(
        dataset.add_private_data_to_dataset_get_result(
            upload_job_id,
            timeout_seconds=0,
        )
    )

    # using add_private_data_to_dataset_get_result without
    # timeout_seconds will await for job to finish
    res = dataset.add_private_data_to_dataset_get_result(upload_job_id)

    if res.status == LongPollingStatus.DONE:
        response: AddPrivateDataResponse = AddPrivateDataResponse(
            dataset_data_list=res.data_hashes_with_titles
        )
    if res.status == LongPollingStatus.ERROR:
        raise Exception(res.errors)  # one can specify custom error handling
    else:
        raise ValueError(f"res.status={res.status}, this should never happen")

print(response.dataset_data_list)
