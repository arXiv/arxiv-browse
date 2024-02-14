"""Test when page is modified and not modified for 200 and 304"""

from datetime import timedelta

from dateutil import parser

from browse.controllers.response_headers import mime_header_date


def test_modified(client_with_test_fs):
    """Test"""
    rv = client_with_test_fs.get('/abs/0704.0600')
    assert rv.status_code == 200

    last_mod = rv.headers['Etag']

    rv = client_with_test_fs.get('/abs/0704.0600',
                         headers={'If-None-Match': last_mod})
    assert rv.status_code == 304

    rv = client_with_test_fs.get('/abs/0704.0600',
                         headers={'if-none-match': last_mod})
    assert rv.status_code == 304

    rv = client_with_test_fs.get('/abs/0704.0600',
                         headers={'IF-NONE-MATCH': last_mod})
    assert rv.status_code == 304

    rv = client_with_test_fs.get('/abs/0704.0600',
                         headers={'If-NoNe-MaTcH': last_mod})
    assert rv.status_code == 304


def test_etag(client_with_test_fs):
    """Test when pages is not modified"""

    rv = client_with_test_fs.get('/abs/0704.0600')
    assert rv.status_code == 200

    etag =rv.headers['ETag']

    rv = client_with_test_fs.get('/abs/0704.0600',
                         headers={'If-None-Match': etag})
    assert rv.status_code == 304

    rv = client_with_test_fs.get('/abs/0704.0600',
                         headers={'If-None-Match': "bogus"+etag})
    assert rv.status_code == 200

    rv = client_with_test_fs.get('/abs/0704.0600',
                         headers={'If-None-Match': '"should-never-match"'})
    assert rv.status_code == 200
