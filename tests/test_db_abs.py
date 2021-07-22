import pytest

from bs4 import BeautifulSoup


def test_should_be_db_abs(dbclient):
    from browse.services.documents import db_docs, get_doc_service

    assert (
        dbclient and dbclient.application.config["DOCUMENT_ABSTRACT_SERVICE"] == db_docs
    )
    assert "db_abs" in str(get_doc_service())


def test_basic_db_abs(dbclient):
    rt = dbclient.get("/abs/0906.2112")
    assert rt.status_code == 200
    assert rt.headers.get("Expires")
    html = BeautifulSoup(rt.data.decode("utf-8"), "html.parser")

    subjects = html.select_one(".subjects")
    assert subjects
    primary = subjects.select_one(".primary-subject")
    assert primary
    assert "Algebraic Geometry" in primary.get_text()
    assert "math.AG" in primary.get_text()

    assert "Number Theory" in subjects.get_text()
    assert "math.NT" in subjects.get_text()


def test_db_abs_history(dbclient):
    pytest.skip("not yet implemented in db backend")

    rt = dbclient.get("/abs/0906.2112")
    assert rt.status_code == 200
    html = BeautifulSoup(rt.data.decode("utf-8"), "html.parser")
    history = html.select_one(".submission-history")
    assert history
    assert "Thu, 11 Jun 2009 14:09:14 UTC" in history.get_text()
    assert "Mon, 9 Aug 2010 13:12:58 UTC" in history.get_text()
    assert "Wed, 28 Mar 2012 08:04:12 UTC" in history.get_text()

    dateline = html.select_one(".dateline")
    assert "11 Jun 2009" in dateline.get_text()
    assert "v1" in dateline.get_text()
    assert "revised 28 Mar 2012" in dateline.get_text()
    assert "this version, v3" in dateline.get_text()


def test_db_abs_comment(dbclient):
    rt = dbclient.get("/abs/0906.2112v3")
    assert rt.status_code == 200
    html = BeautifulSoup(rt.data.decode("utf-8"), "html.parser")
    comments = html.select_one(".comments")
    assert "21 pages" in comments.get_text()

    # TODO: enable this test once version history ticket ARXIVNG-4282 completed
    # rt = dbclient.get("/abs/0906.2112v2")
    # assert rt.status_code == 200
    # html = BeautifulSoup(rt.data.decode("utf-8"), "html.parser")
    # comments = html.select_one(".comments")
    # assert (
    #     "slightly rewritten the introduction, and added a few comments. Conjecture 6.2 is true as stated. This follows from recent work of K. Yamaki and the author. See references in the present version"
    #     in comments.get_text()
    # )
