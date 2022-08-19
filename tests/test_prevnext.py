"""Tests for prevnext controller, :mod:`browse.controllers.prevnext`."""

# mypy: ignore-errors

from unittest import TestCase, mock

from werkzeug.exceptions import BadRequest

from browse.controllers import prevnext
from browse.factory import create_web_app

class TestPrevNextController(TestCase):
    """Tests for :func:`.get_prevnext`."""

    def setUp(self):
        self.app = create_web_app()
        self.app.testing = True
        self.app.config['APPLICATION_ROOT'] = ''

    def test_missing_parameters(self) -> None:
        """Test request with missing parameters."""
        with self.app.app_context():
            with self.app.test_request_context():
                with self.assertRaises(BadRequest):
                    prevnext.get_prevnext("", "", "")
                with self.assertRaises(BadRequest):
                    prevnext.get_prevnext("1801.00001", "", "")
                with self.assertRaises(BadRequest):
                    prevnext.get_prevnext("1801.00001", "next", "")
                with self.assertRaises(BadRequest):
                    prevnext.get_prevnext("1801.00001", "", "cs")
                with self.assertRaises(BadRequest):
                    prevnext.get_prevnext("", "prev", "cs")

    def test_bad_parameters(self) -> None:
        """Test parameters with bad values."""
        with self.app.app_context():
            with self.app.test_request_context():
                with self.assertRaises(BadRequest):
                    prevnext.get_prevnext("foo", "prev", "cs.AI")  # invalid  # valid  # valid
                with self.assertRaises(BadRequest):
                    prevnext.get_prevnext(
                        "cs/0001001", "bar", "cs"  # valid  # invalid
                    )  # valid
                with self.assertRaises(BadRequest):
                    prevnext.get_prevnext(
                        "cs/0001001", "next", "baz"  # valid  # valid
                    )  # invalid

    @mock.patch("browse.controllers.prevnext.get_sequential_id")
    def test_good_parameters(self, mock_get_sequential_id) -> None:  # type: ignore
        """Test parameters with good values."""
        with self.app.app_context():
            with self.app.test_request_context():
                mock_get_sequential_id.return_value = "1801.00002"
                _, status, _ = prevnext.get_prevnext("1801.00001", "next", "all")
                self.assertEqual(status, 301)

                mock_get_sequential_id.return_value = "1801.00001"
                _, status, _ = prevnext.get_prevnext("1801.00002", "prev", "cs.AI")
                self.assertEqual(status, 301)

                mock_get_sequential_id.return_value = None
                with self.assertRaises(BadRequest):
                    prevnext.get_prevnext("1701.00002", "next", "physics.gen-ph")
                mock_get_sequential_id.return_value = ""
                with self.assertRaises(BadRequest):
                    prevnext.get_prevnext("1701.00002", "next", "physics.gen-ph")
