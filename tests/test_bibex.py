def test_bibex_supporting_meta_tags(client_with_test_fs):
    """Test that meta tags get set correctly to support bibex."""
    arxiv_id = "0906.3421"

    rv = client_with_test_fs.get(f"/abs?id={arxiv_id}")
    assert rv.status_code == 200
    txt = rv.data.decode('utf-8')

    assert f'<meta name="citation_arxiv_id" content="{arxiv_id}" />' in txt, "Must have the paper id meta tag"
    assert f'<meta name="citation_doi" content="10.48550/arXiv.{arxiv_id}" />' not in txt, "Must not have the datacite DOI overriding the jref-DOI ARXIVCE-264"
    assert '<meta name="citation_doi" content="10.3842/SIGMA.2010.014" />' in txt, "citation meta tag must have jref DOI"


def test_good_bibtex(client_with_test_fs):
    rv = client_with_test_fs.get(f"/bibtex/0906.3421")
    assert rv.status_code == 200

    rv = client_with_test_fs.get(f"/bibtex/0906.3421v1")
    assert rv.status_code == 200


def test_bibex_none(client_with_test_fs):
    """Don't do a 500 for /bibex/None ARXIVCE-339."""
    rv = client_with_test_fs.get(f"/bibtex/None")
    assert rv.status_code == 400


def test_bad_bibtex(client_with_test_fs):
    rv = client_with_test_fs.get(f"/bibtex/0906.3421v9999")
    assert rv.status_code == 404

    rv = client_with_test_fs.get(f"/bibtex/cs")
    assert rv.status_code == 400

    rv = client_with_test_fs.get(f"/bibtex/0906.3ab1")
    assert rv.status_code == 400

    rv = client_with_test_fs.get(f"/bibtex/0913.1234")
    assert rv.status_code == 400
