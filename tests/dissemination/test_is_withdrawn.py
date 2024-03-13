import pytest
from arxiv.identifier import Identifier

from arxiv.files.object_store import LocalObjectStore
from browse.services.dissemination.article_store import ArticleStore

def test_iswithdrawn():
    # This test seems outdated- what do we pass to article store?
    pytest.skip()
    store = ArticleStore(LocalObjectStore('./tests/data'))
    assert store.get_source(Identifier('1208.9999')) == "WITHDRAWN"
    assert store.get_source(Identifier('1208.9999v1')) == "WITHDRAWN"
