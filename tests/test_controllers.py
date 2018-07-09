# """Tests for abs controller, :mod:`browse.controllers.abs_page.get_abs_page`."""
#
# from unittest import TestCase, mock
#
# from arxiv import status
# from browse.exceptions import AbsNotFound
# from browse.controllers.abs_page import get_abs_page
#
#
# class TestAbsPageController(TestCase):
#     """Tests for :func:`.abs_page.get_abs_page`."""
#
#     @mock.patch('browse.controllers.abs_page.metadata')
#     def test_good_arxiv_id(self, mock_meta):
#         """Query parameter contains a valid arXiv ID."""
#
#         get_abs_page(
#             arxiv_id='1605.09669', request_params={})
#         self.assertEqual(mock_meta.get_abs.call_count, 1,
#                          "Attempt to get abs metadata")
#
#     @mock.patch('browse.controllers.abs_page.metadata')
#     def test_slightly_malformed_arxiv_id(self, mock_meta):
#         """Query parameter contains an valid arXiv ID, but not strictly so."""
#         get_abs_page(
#             arxiv_id='1805.0001', request_params={})
#         # self.assertEqual(code, status.HTTP_301_MOVED_PERMANENTLY,
#         #                  "Response should redirect.")
#         self.assertEqual(mock_meta.get_abs.call_count, 0,
#                          "No attempt to get abs metadata")
