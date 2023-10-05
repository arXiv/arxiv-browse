import pytest


def test_fmt_txt_2112(dbclient, client_with_test_fs):
        """Test abs/nnn?fmt=txt."""
        fsclient = client_with_test_fs
        assert fsclient.get('/abs/0906.2112?fmt=txt').data.decode('utf-8') == \
            dbclient.get('/abs/0906.2112?fmt=txt').data.decode('utf-8')


def test_fmt_txt_5132(dbclient, client_with_test_fs):
    """Test abs/nnn?fmt=txt."""
    fsclient = client_with_test_fs
    assert fsclient.get('/abs/0906.5132?fmt=txt').data.decode('utf-8') == \
           dbclient.get('/abs/0906.5132?fmt=txt').data.decode('utf-8')


