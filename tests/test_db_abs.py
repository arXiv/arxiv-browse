import pytest

from bs4 import BeautifulSoup

def test_should_be_db_abs(dbclient):
    from browse.services.documents import db_docs, get_doc_service
    assert dbclient and dbclient.application.config['DOCUMENT_ABSTRACT_SERVICE'] == db_docs
    assert 'db_abs' in str(get_doc_service())

def test_basic_db_abs(dbclient):
    rt = dbclient.get('/abs/0906.2112')
    assert rt.status_code == 200
    assert rt.headers.get('Surrogate-Control')
    html = BeautifulSoup(rt.data.decode('utf-8'), 'html.parser')

    subjects = html.select_one('.subjects')
    assert subjects
    primary = subjects.select_one('.primary-subject')
    assert primary
    assert 'Algebraic Geometry' in primary.get_text()
    assert 'math.AG' in primary.get_text()

    assert 'Number Theory' in subjects.get_text()
    assert 'math.NT' in subjects.get_text()

def test_abs_head(dbclient):
    rt = dbclient.get('/abs/0906.2112')
    assert rt.status_code == 200

    html = BeautifulSoup(rt.data.decode('utf-8'), 'html.parser')
    head = html.head
    canonical_link = head.find('link', {'rel': 'canonical'})
    assert canonical_link is not None
    assert canonical_link['href'] == "https://arxiv.org/abs/0906.2112"

    meta_description = head.find('meta', {'name': 'description'})
    assert meta_description is not None
    assert meta_description['content'] == "Abstract page for arXiv paper 0906.2112: Symmetric roots and admissible pairing"


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
    assert rt.headers.get('Surrogate-Control')
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


def test_db_abs_pdf_only(dbclient):
    """Tests a paper where the arxiv_metadata.source_format is pdf ARXIVCE-1745."""
    rt = dbclient.get('/abs/0904.2711')
    assert rt.status_code == 200
    html = BeautifulSoup(rt.data.decode('utf-8'), 'html.parser')
    download_button_pdf = html.select_one(".download-pdf")
    assert download_button_pdf
    download_button_html = html.select_one(".download-html")
    assert download_button_html is None
    assert html.select_one(".download-eprint") is None


def test_html_conversion_dissemination (dbclient):
    rt = dbclient.get('/abs/0906.2112')

    assert rt.status_code == 200

    assert rt.headers['Last-Modified'] == 'Mon, 01 Jan 2024 00:00:00 GMT'

    html = BeautifulSoup(rt.data.decode('utf-8'), 'html.parser')
    atag = html.select_one('.extra-services').find('a', {'id': 'latexml-download-link'})

    assert atag and atag.text == "HTML (experimental)"

def test_last_modified_old_html_conversion (dbclient):
    rt = dbclient.get('/abs/2310.08262')

    assert rt.status_code == 200

    assert rt.headers['Last-Modified'].startswith('Fri, 13 Oct 2023')

    html = BeautifulSoup(rt.data.decode('utf-8'), 'html.parser')
    atag = html.select_one('.extra-services').find('a', {'id': 'latexml-download-link'})

    assert atag and atag.text == "HTML (experimental)"

def test_last_modified_no_publish_dt (dbclient):
    rt = dbclient.get('/abs/0906.5132')

    assert rt.status_code == 200

    assert rt.headers['Last-Modified'].startswith('Wed, 14 Oct 2009 20:23:18 GMT')

    html = BeautifulSoup(rt.data.decode('utf-8'), 'html.parser')
    atag = html.select_one('.extra-services').find('a', {'id': 'latexml-download-link'})

    assert atag and atag.text == "HTML (experimental)"

def test_last_modified_no_html (dbclient):
    rt = dbclient.get('/abs/0906.5504')
    
    assert rt.status_code == 200

    assert rt.headers['Last-Modified'].startswith('Tue, 13 Oct 2009')

    html = BeautifulSoup(rt.data.decode('utf-8'), 'html.parser')
    atag = html.select_one('.extra-services').find('a', {'id': 'latexml-download-link'})

    assert atag is None

def test_abs_surrogate_keys(dbclient):
    rv=dbclient.get('/abs/0906.5504')
    assert "abs" in rv.headers['Surrogate-Key']
    assert "abs-0906.5504" in rv.headers['Surrogate-Key']
    assert "paper-id-0906.5504" in rv.headers['Surrogate-Key']

    rv=dbclient.get('/abs/0704.0046v1')
    assert "abs-0704.0046" in rv.headers['Surrogate-Key']
    assert "paper-id-0704.0046" in rv.headers['Surrogate-Key']


def test_guess_DOI(dbclient):
    #if no DOI in table, should still guess and display DOI value
    rt = dbclient.get('/abs/0906.2112')
    assert rt.status_code == 200
    assert rt.headers.get('Surrogate-Control')
    html = BeautifulSoup(rt.data.decode('utf-8'), 'html.parser')

    metatable = html.select_one('.metatable')
    assert metatable
    text= metatable.get_text()
    assert 'https://doi.org/10.48550/arXiv.' in text
    assert 'arXiv-issued DOI via DataCite' in text
    assert 'arXiv-issued DOI via DataCite (pending registration)' in text

    atag=metatable.find('a', {'id': 'arxiv-doi-link'})
    assert atag
    assert atag.text=='https://doi.org/10.48550/arXiv.0906.2112'
    assert atag.get('href')=='https://doi.org/10.48550/arXiv.0906.2112' 

    #proper format for old ids
    rt = dbclient.get('/abs/math/0510544')
    assert rt.status_code == 200
    assert rt.headers.get('Surrogate-Control')
    html = BeautifulSoup(rt.data.decode('utf-8'), 'html.parser')

    metatable = html.select_one('.metatable')
    assert metatable
    text= metatable.get_text()
    assert 'arXiv-issued DOI via DataCite (pending registration)' in text

    atag=metatable.find('a', {'id': 'arxiv-doi-link'})
    assert atag
    assert atag.text=='https://doi.org/10.48550/arXiv.math/0510544'
    assert atag.get('href')=='https://doi.org/10.48550/arXiv.math/0510544' 
