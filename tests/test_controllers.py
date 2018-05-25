"""Tests for abs controller, :mod:`browse.controllers.abs.get_abs_page`."""

from unittest import TestCase, mock

from arxiv import status

from browse.controllers import abs


class GetAbsPageController(TestCase):
    """Tests for :func:`.abs.get_abs_page`."""

    @mock.patch('browse.controllers.abs.metadata')
    def test_good_arxiv_id(self, mock_metadata):
        """Query parameter contains a valid arXiv ID."""
        response_data, code, headers = abs.get_abs_page(
            arxiv_id='1805.00001', request_params={})

        self.assertEqual(mock_metadata.get_abs.call_count, 1,
                         "Attempt to get abs metadata")

    @mock.patch('browse.controllers.abs.metadata')
    def test_bad_arxiv_id(self, mock_metadata):
        """Query parameter contains an invalid arXiv ID."""
        response_data, code, headers = abs.get_abs_page(
            arxiv_id='foo', request_params={})
        self.assertEqual(code, status.HTTP_404_NOT_FOUND,
                         "Response should be not found.")
        self.assertEqual(mock_metadata.get_abs.call_count, 0,
                         "No attempt to get abs metadata")

    # @mock.patch('browse.controllers.abs.metadata')
    # def test_slightly_bad_arxiv_id(self, mock_metadata):
    #     """Query parameter contains an valid arXiv ID, but not strictly so."""
    #     response_data, code, headers = abs.get_abs_page(
    #         arxiv_id='1805.0001', request_params={})
    #     self.assertEqual(code, status.HTTP_301HTTP_301_MOVED_PERMANENTLY,
    #                      "Response should redirect.")
    #     self.assertEqual(mock_metadata.get_abs.call_count, 0,
    #                      "No attempt to get abs metadata")
