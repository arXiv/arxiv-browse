"""Tests for tb controllers, :mod:`browse.controllers.tb_page`."""

# mypy: ignore-errors

from unittest import TestCase, mock
from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import BadRequest
from arxiv import status
from browse.exceptions import TrackbackNotFound
from browse.controllers import tb_page


class TestTbPageController(TestCase):
    """Tests for :func:`.get_tb_page`."""

    @mock.patch('browse.controllers.tb_page.metadata')
    @mock.patch('browse.controllers.tb_page.get_paper_trackback_pings')
    # type: ignore
    def test_good_id_with_trackbacks(self, mock_get_paper_trackback_pings, mock_metadata) -> None:
        """Test requests with good arXiv identifiers known to the corpus."""
        mock_get_paper_trackback_pings.return_value = list()
        mock_metadata.get_abs.return_value = {}
        response_data, code, _ = tb_page.get_tb_page(arxiv_id='1901.99999')
        self.assertEqual(code, status.HTTP_200_OK, 'Response should be OK.')
        for key in ('arxiv_identifier', 'trackback_pings'):
            self.assertIn(key, response_data,
                          f"Response data should include '{key}'")
        for key in ('abs_meta', 'author_links'):
            self.assertNotIn(key, response_data,
                             f"Response data should not include '{key}'")

    def test_bad_or_unknown_id(self) -> None:
        """Test requests with bad arXiv identifiers."""
        with self.assertRaises(TrackbackNotFound):
            for bad_or_unknown_id in ('foo', '1901.99999'):
                tb_page.get_tb_page(arxiv_id=bad_or_unknown_id)


class TestRecentTbPageController(TestCase):
    """Tests for :func:`.get_recent_tb_page`."""

    @mock.patch('browse.controllers.tb_page.get_recent_trackback_pings')
    def test_form_data(self, mock_get_recent_trackback_pings) -> None:  # type: ignore
        """Test /tb/recent form data."""
        mock_get_recent_trackback_pings.return_value = list()

        form_data = MultiDict({
            'foo': 'bar'
        })
        with self.assertRaises(BadRequest):
            tb_page.get_recent_tb_page(form_data)

        form_data = MultiDict({
            'views': 'baz'
        })
        with self.assertRaises(BadRequest):
            tb_page.get_recent_tb_page(form_data)

        form_data = MultiDict({
            'views': '25'
        })
        response_data, code, _ = tb_page.get_recent_tb_page(form_data)
        self.assertEqual(code, status.HTTP_200_OK, 'Response should be OK.')
        self.assertIn('max_trackbacks', response_data,
                      "Response data should include 'max_trackbacks'")
        self.assertEqual(response_data['max_trackbacks'], 25,
                         "'max_trackbacks' should equal value from form")
        self.assertIn('recent_trackback_pings', response_data,
                      "Response data should include 'recent_trackback_pings'")
        self.assertIn('article_map', response_data,
                      "Response data should include 'article_map'")


class TestTbRedirect(TestCase):
    """Tests for :func:`.get_tb_redirect`."""

    @mock.patch('browse.controllers.tb_page.get_trackback_ping')
    def test_arguments(self, mock_trackback_ping) -> None:  # type: ignore
        """Test /tb/redirect arguments."""
        with self.assertRaises(TrackbackNotFound):
            # 'foo' is not an integer
            tb_page.get_tb_redirect(
                trackback_id='foo', hashed_document_id='feedface')

        with self.assertRaises(TrackbackNotFound):
            # 'baz' is not a hex string
            tb_page.get_tb_redirect(
                trackback_id='1', hashed_document_id='baz')

        mtb = mock.Mock(
            trackback_id=1,
            hashed_document_id='feaedface',
            url='https://example.org'
        )
        mock_trackback_ping.return_value = mtb
        with self.assertRaises(TrackbackNotFound):
            # parameters are OK, but hashed_document_id does not match
            response_data, code, headers = tb_page.get_tb_redirect(
                trackback_id='1', hashed_document_id='feedface')

        mtb = mock.Mock(
            trackback_id=2,
            hashed_document_id='f005ba11',
            url='https://example.com'
        )
        mock_trackback_ping.return_value = mtb

        _, code, headers = tb_page.get_tb_redirect(
            trackback_id='2', hashed_document_id='f005ba11')
        self.assertEqual(
            code, 301, 'Expect redirect for matching hashed_document_id')
        self.assertEqual(headers['Location'], mtb.url,
                         'Redirect location header matches trackback URL')
