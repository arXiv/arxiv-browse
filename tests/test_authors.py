# tests the /a route that gets papers by tapir_user.user_id
import pytest

from tests import comment

@pytest.mark.parametrize("url", ["/a/33510.atom", "/a/33510.atom2"])
def test_authors_atom(url, dbclient, mocker):
    from browse.services.listing import ListingItem

    mock_gafa = mocker.patch("browse.controllers.list_page.author.get_articles_for_author")
    mock_gafa.return_value = [
        ListingItem('cond-mat/0703772', 'new', 'cond-mat'),
        ListingItem('2310.08262', 'new', 'cheese'),
        ListingItem('chao-dyn/9510015', 'new', 'chao-dyn'),
        ListingItem('cond-mat/0501593', 'new', 'cond-mat'),
        ListingItem('cond-mat/0703772', 'new', 'cond-mat'),
        ListingItem('cond-mat/0703772', 'new', 'cond-mat'),
        ListingItem('cond-mat/9805021', 'new', 'cond-mat'),
        ListingItem('cond-mat/9805021', 'new', 'cond-mat'),
        ListingItem('cs/0001024', 'new', 'cs'),
        ListingItem('hep-th/0703166', 'new', 'hep-th'),
        ListingItem('hep-th/0703166', 'new', 'hep-th'),
        ListingItem('hep-th/0703166', 'new', 'hep-th'),
        ListingItem('hep-th/0703166', 'new', 'hep-th'),
        ListingItem('hep-th/0703166', 'new', 'hep-th'),
        ListingItem('hep-th/9901002', 'new', 'hep-th'),
        ListingItem('math/0510544', 'new', 'math'),
        ListingItem('math/0510544', 'new', 'math'),
        ListingItem('physics/0612123', 'new', 'physics'),
    ]
    mock_get_id = mocker.patch("browse.controllers.list_page.author._get_user_id")
    mock_get_id.return_value = 33510, False

    mock_get_orcid_uri =mocker.patch("browse.controllers.list_page.author._get_orcid_uri")
    mock_get_orcid_uri.return_value = "234-fakeorcid-234"

    resp = dbclient.get(url)
    assert resp.text

    import xml.etree.ElementTree as ET
    root = ET.fromstring(resp.text)
    assert 'feed' in root.tag

    ns = {'atom': 'http://www.w3.org/2005/Atom',
          'arxiv': 'http://arxiv.org/schemas/atom'}
    entries = root.findall('atom:entry', ns)
    assert len(entries) == 18

    entry1 = entries[0]
    assert entry1 is not None
    assert entry1.find('atom:title', ns) is not None
    assert entry1.find('atom:id', ns) is not None
    assert entry1.find('atom:updated', ns) is not None
    assert entry1.find('atom:published', ns) is not None
    assert entry1.find('atom:summary', ns) is not None
    assert entry1.find('atom:author', ns) is not None
    assert entry1.find('atom:category', ns) is not None
    assert entry1.find('arxiv:comment', ns) is not None
    assert entry1.find('arxiv:primary_category', ns) is not None


def test_authors_json(dbclient, mocker):
    from browse.services.listing import ListingItem

    mock_gafa = mocker.patch("browse.controllers.list_page.author.get_articles_for_author")
    mock_gafa.return_value = [
        ListingItem('cond-mat/0703772', 'new', 'cond-mat'),
        ListingItem('2310.08262', 'new', 'cheese'),
        ListingItem('chao-dyn/9510015', 'new', 'chao-dyn'),
        ListingItem('cond-mat/0501593', 'new', 'cond-mat'),
        ListingItem('cond-mat/0703772', 'new', 'cond-mat'),
        ListingItem('cond-mat/0703772', 'new', 'cond-mat'),
        ListingItem('cond-mat/9805021', 'new', 'cond-mat'),
        ListingItem('cond-mat/9805021', 'new', 'cond-mat'),
        ListingItem('cs/0001024', 'new', 'cs'),
        ListingItem('hep-th/0703166', 'new', 'hep-th'),
        ListingItem('hep-th/0703166', 'new', 'hep-th'),
        ListingItem('hep-th/0703166', 'new', 'hep-th'),
        ListingItem('hep-th/0703166', 'new', 'hep-th'),
        ListingItem('hep-th/0703166', 'new', 'hep-th'),
        ListingItem('hep-th/9901002', 'new', 'hep-th'),
        ListingItem('math/0510544', 'new', 'math'),
        ListingItem('math/0510544', 'new', 'math'),
        ListingItem('physics/0612123', 'new', 'physics'),
    ]
    mock_get_id = mocker.patch("browse.controllers.list_page.author._get_user_id")
    mock_get_id.return_value = 33510, False

    mock_get_orcid_uri =mocker.patch("browse.controllers.list_page.author._get_orcid_uri")
    mock_get_orcid_uri.return_value = "234-fakeorcid-234"

    resp = dbclient.get("/a/33510.json")
    assert resp.json
    data = resp.json
    assert "entries" in data and len(data['entries']) == 18
    entry1 = data['entries'][0]
    assert entry1
    assert 'authors' in entry1
    assert 'categories' in entry1
    assert 'comment' in entry1
    assert 'formats' in entry1
    assert 'id' in entry1
    assert 'published' in entry1
    assert 'subject' in entry1
    assert 'summary' in entry1
    assert 'title' in entry1
    assert 'updated' in entry1


def test_authors_html(dbclient, mocker):
    from browse.services.listing import ListingItem

    mock_gafa = mocker.patch("browse.controllers.list_page.author.get_articles_for_author")
    mock_gafa.return_value = [
        ListingItem('cond-mat/0703772', 'new', 'cond-mat'),
        ListingItem('2310.08262', 'new', 'cheese'),
        ListingItem('chao-dyn/9510015', 'new', 'chao-dyn'),
        ListingItem('cond-mat/0501593', 'new', 'cond-mat'),
        ListingItem('cond-mat/0703772', 'new', 'cond-mat'),
        ListingItem('cond-mat/0703772', 'new', 'cond-mat'),
        ListingItem('cond-mat/9805021', 'new', 'cond-mat'),
        ListingItem('cond-mat/9805021', 'new', 'cond-mat'),
        ListingItem('cs/0001024', 'new', 'cs'),
        ListingItem('hep-th/0703166', 'new', 'hep-th'),
        ListingItem('hep-th/0703166', 'new', 'hep-th'),
        ListingItem('hep-th/0703166', 'new', 'hep-th'),
        ListingItem('hep-th/0703166', 'new', 'hep-th'),
        ListingItem('hep-th/0703166', 'new', 'hep-th'),
        ListingItem('hep-th/9901002', 'new', 'hep-th'),
        ListingItem('math/0510544', 'new', 'math'),
        ListingItem('math/0510544', 'new', 'math'),
        ListingItem('physics/0612123', 'new', 'physics'),
    ]
    mock_get_id = mocker.patch("browse.controllers.list_page.author._get_user_id")
    mock_get_id.return_value = 33510, False

    mock_get_orcid_uri =mocker.patch("browse.controllers.list_page.author._get_orcid_uri")
    mock_get_orcid_uri.return_value = "234-fakeorcid-234"

    resp = dbclient.get("/a/33510.html")
    assert resp.text
