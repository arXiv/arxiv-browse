"""Tests for /login hostname config via env vars"""
import importlib
from _pytest import monkeypatch
import pytest

from flask import url_for

AUTH_SERVER_VALUE="auth.example.com"


@pytest.fixture
def app_with_envvars(monkeypatch):
    monkeypatch.setenv("AUTH_SERVER", AUTH_SERVER_VALUE)
    monkeypatch.setenv("CLASSIC_DB_URI", "sqlite:///:memory:")
    monkeypatch.setenv("LATEXL_DB_URI", "sqlite:///:memory:")
    monkeypatch.setenv("APPLICATION_ROOT", "")

    import os
    assert os.environ.get("AUTH_SERVER") == AUTH_SERVER_VALUE

    import arxiv.config
    importlib.reload(arxiv.config)
    import browse.config
    importlib.reload(browse.config)

    from browse.factory import create_web_app
    app = create_web_app()
    return app


def test_monkeypatch_set_envvars(app_with_envvars):
    with app_with_envvars.test_request_context('/home', method='GET'):
        import os
        assert os.environ.get("AUTH_SERVER") == AUTH_SERVER_VALUE


def test_settings_gets_envvar(app_with_envvars):
    with app_with_envvars.test_request_context('/home', method='GET'):
        import arxiv.config
        importlib.reload(arxiv.config)
        from arxiv.config import settings
        assert settings.AUTH_SERVER == AUTH_SERVER_VALUE


def test_auth_server_in_login_url(app_with_envvars):
    with app_with_envvars.test_request_context('/home', method='GET'):
        assert "https://" + AUTH_SERVER_VALUE + '/login' == url_for('login')
