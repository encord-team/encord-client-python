
import logging
import magic
import os.path
import requests

from tqdm import tqdm


def read_in_chunks(file_path, blocksize=1024, chunks=-1):
    """ Splitting the file into chunks. """
    with open(file_path, 'rb') as file_object:
        size = os.path.getsize(file_path)
        pbar = tqdm(total=100)
        current = 0
        while chunks:
            data = file_object.read(blocksize)
            if not data:
                break
            yield data
            chunks -= 1
            step = round(blocksize / size * 100, 1)
            current = min(100, current + step)
            pbar.update(min(100 - current, step))
        pbar.update(100 - current)
        pbar.close()


def upload_to_signed_url(file_path, signed_url, querier, orm_class):
    res_upload = requests.put(
        signed_url.get('signed_url'),
        data=read_in_chunks(file_path),
        headers={'Content-Type': 'application/octet-stream'}
    )
    res = None
    if res_upload.status_code == 200:
        data_hash = signed_url.get('data_hash')

        res = querier.basic_put(
            orm_class,
            uid=data_hash,
            payload=signed_url
        )

        if orm_class(res):
            logging.info("Successfully uploaded: %s",
                         signed_url.get('title', ''))
        else:
            logging.info("Error uploading: %s",
                         signed_url.get('title', ''))

    else:
        logging.info("Error generating signed url for: %s",
                     signed_url.get('title', ''))

    return orm_class(res)


def upload_to_signed_url_list(file_paths, signed_urls, querier, orm_class):
    assert len(file_paths) == len(signed_urls),\
        'Error getting the correct number of signed urls'
    data_uid_list = []
    mime = magic.Magic(mime=True)
    for i in range(len(file_paths)):
        file_path = file_paths[i]
        file_name = os.path.basename(file_path)
        mime_type = mime.from_file(file_path)
        url = signed_urls[i]
        assert url.get('title', '') == file_name, 'Ordering issue'
        res_upload = requests.put(
            url.get('signed_url'),
            data=read_in_chunks(file_path),
            headers={'Content-Type': mime_type}
        )
        if res_upload.status_code == 200:
            data_hash = url.get('data_hash')
            res = querier.basic_put(
                orm_class,
                uid=data_hash,
                payload=url
            )
            if res:
                logging.info("Successfully uploaded: %s",
                             url.get('title', ''))
                data_uid_list.append(url.get('data_hash'))
            else:
                logging.info("Error uploading: %s",
                             url.get('title', ''))
                raise Exception('Could not save information into database')
        else:
            raise Exception('Bad request')

    return data_uid_list


