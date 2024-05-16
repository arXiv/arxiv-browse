import pytest
from invalidator import _paperid, _purge_urls


@pytest.mark.parametrize("key, paperid", [
    ("/ps_cache/arxiv/pdf/0701/0712.0830v1.pdf", "0712.0830v1"),
    ("/ps_cache/arxiv/pdf/2401/2401.08337v2.pdf", "2401.08337v2"),
    ("/arxiv-production-data/ps_cache/hep-ph/pdf/0511/0511005v2.pdf", "hep-ph/0511005v2"),
])
def test_paperid(key, paperid):
    aid = _paperid(key)
    assert aid and aid.idv == paperid

@pytest.mark.parametrize("key, urls", [
("/ps_cache/arxiv/pdf/0701/0712.0830v1.pdf", ['arxiv.org/pdf/0712.0830v1','arxiv.org/pdf/0712.0830']),
("/ps_cache/arxiv/pdf/0701/0712.0830v2.pdf", ['arxiv.org/pdf/0712.0830v2','arxiv.org/pdf/0712.0830']),
("/ps_cache/arxiv/pdf/0701/0712.0830v11.pdf", ['arxiv.org/pdf/0712.0830v11','arxiv.org/pdf/0712.0830']),
("/ps_cache/arxiv/ps/0701/0712.0830v11.ps", ['arxiv.org/ps/0712.0830v11','arxiv.org/ps/0712.0830']),
("/ps_cache/arxiv/dvi/0701/0712.0830v11.dvi", ['arxiv.org/dvi/0712.0830v11','arxiv.org/dvi/0712.0830']),
("/ps_cache/arxiv/html/0701/0712.0830v11.html.gz", ['arxiv.org/html/0712.0830v11','arxiv.org/html/0712.0830','arxiv.org/html/0712.0830v11/','arxiv.org/html/0712.0830/']),
("/arxiv-production-data/ps_cache/hep-ph/pdf/0511/0511005v2.pdf", [  'arxiv.org/pdf/hep-ph/0511005v2', 'arxiv.org/pdf/hep-ph/0511005',]),
])
def test_purge_urls(key, urls):
    assert _purge_urls("", key, _paperid(key)) == urls
