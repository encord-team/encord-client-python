
import os.path

from tqdm import tqdm


def read_in_chunks(file_path, blocksize=1024, chunks=-1):
    """ Splitting the file into chunks. """
    file_object = open(file_path, 'rb')
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
