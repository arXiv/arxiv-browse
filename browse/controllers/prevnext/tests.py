"""Tests for prevnext controller, :mod:`browse.controllers.prevnext`."""

# mypy: ignore-errors

from unittest import TestCase, mock
from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import BadRequest
from browse.controllers import prevnext


class TestPrevNextController(TestCase):
    """Tests for :func:`.get_prevnext`."""

    def test_missing_parameters(self) -> None:
        """Test request with missing parameters."""
        request_data = MultiDict()
        with self.assertRaises(BadRequest):
            prevnext.get_prevnext(request_data)

        request_data = MultiDict({
            'id': '1801.00001'
        })
        with self.assertRaises(BadRequest):
            prevnext.get_prevnext(request_data)

        request_data = MultiDict({
            'id': '1801.00001',
            'function': 'next'
        })
        with self.assertRaises(BadRequest):
            prevnext.get_prevnext(request_data)

        request_data = MultiDict({
            'id': '1801.00001',
            'context': 'cs'
        })
        with self.assertRaises(BadRequest):
            prevnext.get_prevnext(request_data)

        request_data = MultiDict({
            'function': 'prev',
            'context': 'cs'
        })
        with self.assertRaises(BadRequest):
            prevnext.get_prevnext(request_data)

    def test_bad_parameters(self) -> None:
        """Test parameters with bad values."""
        request_data = MultiDict({
            'id': 'foo',  # invalid
            'function': 'prev',  # valid
            'context': 'cs.AI'  # valid
        })
        with self.assertRaises(BadRequest):
            prevnext.get_prevnext(request_data)

        request_data = MultiDict({
            'id': 'cs/0001001',  # valid
            'function': 'bar',  # invalid
            'context': 'cs'  # valid
        })
        with self.assertRaises(BadRequest):
            prevnext.get_prevnext(request_data)

        request_data = MultiDict({
            'id': 'cs/0001001',  # valid
            'function': 'next',  # valid
            'context': 'baz'  # invalid
        })
        with self.assertRaises(BadRequest):
            prevnext.get_prevnext(request_data)

    @mock.patch('browse.controllers.prevnext.get_sequential_id')
    @mock.patch('browse.controllers.prevnext.url_for')
    def test_good_parameters(self, mock_url_for, mock_get_sequential_id) -> None:  # type: ignore
        """Test parameters with good values."""
        request_data = MultiDict({
            'id': '1801.00001',
            'function': 'next',
            'context': 'all'
        })
        mock_get_sequential_id.return_value = '1801.00002'
        _, status, headers = prevnext.get_prevnext(request_data)
        self.assertEqual(status, 301)

        request_data = MultiDict({
            'id': '1801.00002',
            'function': 'prev',
            'context': 'cs.AI'
        })
        mock_get_sequential_id.return_value = '1801.00001'
        _, status, headers = prevnext.get_prevnext(request_data)
        self.assertEqual(status, 301)

        request_data = MultiDict({
            'id': '1701.00002',
            'function': 'next',
            'context': 'physics.gen-ph'
        })
        mock_get_sequential_id.return_value = None
        with self.assertRaises(BadRequest):
            prevnext.get_prevnext(request_data)
        mock_get_sequential_id.return_value = ''
        with self.assertRaises(BadRequest):
            prevnext.get_prevnext(request_data)
