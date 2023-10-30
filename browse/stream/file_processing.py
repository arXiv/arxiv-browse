import logging
from io import BytesIO, StringIO
from typing import Generator, Union

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

def process_file(input_stream: BytesIO, processing_func) -> Generator[Union[BytesIO, StringIO], None, None]:
    for line in input_stream:
        yield processing_func(line)