import pytest
from arxiv.identifier import Identifier

from browse.services.dissemination.object_store_local import LocalObjectStore
from browse.services.dissemination.article_store import ArticleStore

def test_is_not_withdrawn(storage_prefix):
    """Tests some cases where the articles are not withdrawn"""
    store = ArticleStore(LocalObjectStore(storage_prefix), lambda a, b: False, lambda _: False)

    assert store.is_withdrawn(Identifier('cs/0011004v1')) == False
    assert store.is_withdrawn(Identifier('cs/0011004')) == False


def test_is_not_withdrawn_missing(storage_prefix):
    """Tests some cases where the articles are not withdrawn"""
    store = ArticleStore(LocalObjectStore(storage_prefix), lambda a, b: False, lambda _: False)

    assert store.is_withdrawn(Identifier('1208.9999v1')) == False
    assert store.is_withdrawn(Identifier('1208.9999')) == False
