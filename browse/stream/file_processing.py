import logging
from io import BytesIO, StringIO
from typing import Generator, Union

from browse.services.object_store.fileobj import FileObj, UngzippedFileObj

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

def process_file(file: UngzippedFileObj, processing_func) -> Generator[Union[BytesIO, StringIO], None, None]:
    with file.open('rb') as f:
        for line in f:
            yield processing_func(line)