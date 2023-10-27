import logging
from io import BytesIO
from typing import Generator

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

def process_file(input_stream: BytesIO, processing_func) -> Generator[BytesIO, None, None]:
    for line in input_stream:
        yield processing_func(line)