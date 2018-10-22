"""Tests exception handling in :mod:`arxiv.base.exceptions`."""

from unittest import TestCase, mock

from arxiv import status
from browse.factory import create_web_app
from browse.services.document.metadata import AbsException


class TestExceptionHandling(TestCase):
    """HTTPExceptions should be handled with custom templates."""

    def setUp(self):
        """Initialize an app and install :class:`.Base`."""

        """Disable logging to avoid messy output during testing"""
        import logging
        wlog = logging.getLogger('werkzeug')
        wlog.disabled = True

        self.app = create_web_app()
        self.client = self.app.test_client()

    def test_404(self):
        """A 404 response should be returned."""
        for path in ('/foo', '/abs', '/abs/'):
            response = self.client.get(path)
            self.assertEqual(response.status_code,
                             status.HTTP_404_NOT_FOUND,
                             f'should get 404 for {path}')
            self.assertIn('text/html', response.content_type)

        response = self.client.get('/abs/1307.0001v999')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND,
                         f'should get 404 for known paper ID with '
                         'nonexistent version')
        response = self.client.get('/abs/alg-geom/07059999')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND,
                         f'should get 404 for valid old paper ID '
                         'with nonexistent paper number affix')
        response = self.client.get('/abs/astro-ph/0110242')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND,
                         f'should get 404 for known deleted paper')
        response = self.client.get('/abs/foo-bar/11223344')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND,
                         f'should get 404 for bad paper ID')

    @mock.patch('browse.controllers.abs_page.get_abs_page')
    def test_500(self, mock_abs):
        """A 500 response should be returned."""
        # Raise a general exception from the get_abs_page controller.
        mock_abs.side_effect = AbsException

        """Disable logging to avoid messy output during testing"""
        self.app.logger.disabled = True

        response = self.client.get('/abs/1234.5678')
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('text/html', response.content_type)
