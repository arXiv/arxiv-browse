from datetime import date

from tests import TestLocalAbsAccessor, ABS_FILES
from arxiv.document.parse_abs import parse_abs_file_accessor
from arxiv.identifier import Identifier
from browse.formatting.external_refs_cits import include_inspire_link, \
    get_orig_publish_date


def test_abs_with_inspire(client_with_fake_listings):
    m = parse_abs_file_accessor(TestLocalAbsAccessor(Identifier('1108.5926'), latest=True))
    assert  m 
    assert  get_orig_publish_date(m.arxiv_identifier) == date(2011,8,1)
    assert  m.primary_category
    assert include_inspire_link( m )  # 1108.5926v1 should get Insire link

    rv = client_with_fake_listings.get('/abs/1108.5926v1')
    assert rv.status_code == 200
    assert  "INSPIRE HEP" in rv.data.decode('utf-8')  # 1108.5926 should get INSPIRE link

def test_abs_without_inspire(client_with_fake_listings):
    m = parse_abs_file_accessor(TestLocalAbsAccessor(Identifier('math/0202001'), latest=True))
    assert m
    assert not include_inspire_link( m )  # math/0202001 should NOT get Insire link

    rv = client_with_fake_listings.get('/abs/math/0202001')
    assert rv.status_code == 200
    assert  "INSPIRE HEP" not in rv.data.decode('utf-8')  # math/0202001 should NOT get INSPIRE link
