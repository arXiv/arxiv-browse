import pytest

from bs4 import BeautifulSoup

def test_should_be_db_abs(dbclient):
    from browse.services.documents import db_docs, get_doc_service
    assert dbclient and dbclient.application.config['DOCUMENT_ABSTRACT_SERVICE'] == db_docs
    assert 'db_abs' in str(get_doc_service())

def test_basic_db_abs(dbclient):
    rt = dbclient.get('/abs/0906.2112')
    assert rt.status_code == 200
    assert rt.headers.get('Expires') or rt.headers.get('Cache-Control')
    html = BeautifulSoup(rt.data.decode('utf-8'), 'html.parser')

    subjects = html.select_one('.subjects')
    assert subjects
    primary = subjects.select_one('.primary-subject')
    assert primary
    assert 'Algebraic Geometry' in primary.get_text()
    assert 'math.AG' in primary.get_text()

    assert 'Number Theory' in subjects.get_text()
    assert 'math.NT' in subjects.get_text()


def test_db_abs_history(dbclient):
    rt = dbclient.get('/abs/0906.2112')
    assert rt.status_code == 200
    html = BeautifulSoup(rt.data.decode('utf-8'), 'html.parser')
    history = html.select_one('.submission-history')
    assert history
    assert 'Thu, 11 Jun 2009 14:09:14 UTC' in history.get_text()
    assert 'Mon, 9 Aug 2010 13:12:58 UTC' in history.get_text()
    assert 'Wed, 28 Mar 2012 08:04:12 UTC' in history.get_text()

    dateline = html.select_one('.dateline')
    assert "11 Jun 2009" in dateline.get_text()
    assert "v1" in dateline.get_text()
    assert "revised 28 Mar 2012" in dateline.get_text()
    assert "this version, v3" in dateline.get_text()


def test_db_abs_comment(dbclient):
    rt = dbclient.get('/abs/0906.2112')
    assert rt.status_code == 200
    assert rt.headers.get('Expires') or rt.headers.get('Cache-Control')
    assert '21 pages' in rt.data.decode('utf-8')


def test_db_abs_small_source_size(dbclient):
    """Tests a paper where the arxiv_metadata.source_size is less than half of 1kb ARXIVCE-1053."""
    rt = dbclient.get('/abs/2310.08262')
    assert rt.status_code == 200

    html = BeautifulSoup(rt.data.decode('utf-8'), 'html.parser')
    download_button_html = html.select_one(".download-html")
    assert download_button_html
    download_button_pdf = html.select_one(".download-pdf")
    assert download_button_pdf is None # should not have a pdf download since it is a html source submission


def test_db_abs_null_source_size(dbclient):
    """Tests a paper where the arxiv_metadata.source_size is zero ARXIVCE-1050."""
    rt = dbclient.get('/abs/2305.11452')
    assert rt.status_code == 200
    html = BeautifulSoup(rt.data.decode('utf-8'), 'html.parser')
    download_button_pdf = html.select_one(".download-pdf")
    assert download_button_pdf is None
    download_button_html = html.select_one(".download-html")
    assert download_button_html is None
