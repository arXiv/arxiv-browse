
from arxiv.identifier import Identifier

from browse.services.object_store.object_store_local import LocalObjectStore
from browse.services.dissemination.article_store import ArticleStore

def test_iswithdrawn():
    store = ArticleStore(LocalObjectStore('./tests/data'))
    assert store.is_withdrawn(Identifier(1208.9999)) == False
    assert store.is_withdrawn(Identifier(1208.9999v1)) == False
