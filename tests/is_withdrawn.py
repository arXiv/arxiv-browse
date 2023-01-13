
from arxiv.identifier import Identifier

from arxiv_dissemination.services.object_store_local import LocalObjectStore
from arxiv_dissemination.services.article_store import ArticleStore

def test_iswithdrawn():
    store = ArticleStore(LocalObjectStore('./tests/data'))
    assert store.is_withdrawn(Identifier(1208.9999)) == False
    assert store.is_withdrawn(Identifier(1208.9999v1)) == False
