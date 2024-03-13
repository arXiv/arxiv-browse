import unittest
import json
from subscribe_submissions import submission_message_to_payloads
from unittest.mock import MagicMock
from google.cloud.pubsub_v1.subscriber.message import Message


def create_mock_message(data, attributes=None):
    """
    Create a mock Message object.

    Parameters:
    - data (str): The message data as a string.
    - attributes (dict): Optional. A dictionary of attributes for the message.

    Returns:
    - A mock Message object with the specified data and attributes.
    """
    data_bytes = data.encode("utf-8")
    mock_message = MagicMock(spec=Message)
    mock_message.data = data_bytes
    mock_message.attributes = attributes or {}
    return mock_message


class TestSubscribeSumissions(unittest.TestCase):

    def test_submission_message_to_payloads(self):
        message = create_mock_message(json.dumps({"type": "rep", "paper_id": "physics/0106051", "version": 5, "src_ext": ".gz"}))
        _xid, payloads = submission_message_to_payloads(message, {}, testing=True)
        self.assertEqual([('/data/ftp/physics/papers/0106/0106051.abs', 'ftp/physics/papers/0106/0106051.abs'),
                         ('/data/ftp/physics/papers/0106/0106051.gz', 'ftp/physics/papers/0106/0106051.gz'),
                         ('/data/orig/physics/papers/0106/0106051v4.abs', 'orig/physics/papers/0106/0106051v4.abs'),
                         ('/data/orig/physics/papers/0106/0106051v4.gz', 'orig/physics/papers/0106/0106051v4.gz')], payloads)

        message = create_mock_message(json.dumps({"type": "rep", "paper_id": "2403.07874", "version": 3, "src_ext": ".tar.gz"}))
        _xid, payloads = submission_message_to_payloads(message, {}, testing=True)
        self.assertEqual([('/data/ftp/arxiv/papers/2403/2403.07874.abs', 'ftp/arxiv/papers/2403/2403.07874.abs'),
                          ('/data/ftp/arxiv/papers/2403/2403.07874.tar.gz', 'ftp/arxiv/papers/2403/2403.07874.tar.gz'),
                          ('/data/orig/arxiv/papers/2403/2403.07874v2.abs', 'orig/arxiv/papers/2403/2403.07874v2.abs'),
                          ('/data/orig/arxiv/papers/2403/2403.07874v2.tar.gz', 'orig/arxiv/papers/2403/2403.07874v2.tar.gz')], payloads)

