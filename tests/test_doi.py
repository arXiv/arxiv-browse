import os
import unittest
from urllib.parse import parse_qs, unquote, urlparse

from bs4 import BeautifulSoup

from app import app
from arxiv.license import ASSUMED_LICENSE_URI


def test_doi_9503001(client_with_test_fs):
    # test for ARXIVNG-1201, messed up doi text and href
    rv = client_with_test_fs.get('/abs/ao-sci/9503001')
    #self.assertEqual(rv.status_code, 200)
    assert rv.status_code == 200
    html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')

    doi_a = html.find('td', 'doi').find('a')
    assert doi_a and (doi_a.text ==
                     '10.1175/1520-0469(1996)053<0946:ASTFHH>2.0.CO;2',
                     'DOI links should deal with strange characters with no problems')

    assert doi_a['href']
    parsed_url = urlparse(doi_a['href'])

    assert parsed_url.netloc == 'doi.org' # decoded URL from CT should have DOI resolver hostname
    assert unquote(parsed_url.path) == '/10.1175/1520-0469(1996)053<0946:ASTFHH>2.0.CO;2' # path of doi.org URL should be to expected DOI
