import logging
from io import BytesIO

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)


def process_file(input_stream: BytesIO, processing_func) -> BytesIO:
    output_stream= BytesIO()
    for line in input_stream:
        output_stream.write(processing_func(line))
    return output_stream