import pytest


def test_fmt_txt_2112(dbclient):
    """Test abs/nnn?fmt=txt."""
    db_txt_abs = dbclient.get('/abs/0906.2112?fmt=txt').data.decode('utf-8')

    assert "arXiv:0906.2112" in db_txt_abs
    assert "From: Robin de Jong" in db_txt_abs
    assert "Date: Thu, 11 Jun 2009 14:09:14 UTC   (20kb,1)" in db_txt_abs
    assert "Date (revised v2): Mon, 9 Aug 2010 13:12:58 UTC   (21kb,1)" in db_txt_abs
    assert "Date (revised v3): Wed, 28 Mar 2012 08:04:12 UTC   (21kb,1)" in db_txt_abs

    assert "Title: Symmetric roots and admissible pairing" in db_txt_abs
    assert "Authors: Robin de Jong" in db_txt_abs
    assert "Categories: math.AG math.NT" in db_txt_abs
    assert "Comments: 21 pages" in db_txt_abs
    assert "MSC-class: 14G40; 11G20" in db_txt_abs
    assert "License: http://arxiv.org/licenses/nonexclusive-distrib/1.0/" in db_txt_abs


def test_fmt_txt_5132(dbclient):
    """Test abs/nnn?fmt=txt."""
    db_txt_abs = dbclient.get('/abs/0906.5132?fmt=txt').data.decode('utf-8')

    assert "arXiv:0906.5132" in db_txt_abs
    assert "From: Vladimir P. Mineev" in db_txt_abs
    assert "Date: Sun, 28 Jun 2009 11:24:35 UTC   (17kb,1)" in db_txt_abs
    assert "Date (revised v2): Tue, 21 Jul 2009 09:45:44 UTC   (17kb,1)" in db_txt_abs
    assert "Date (revised v3): Wed, 29 Jul 2009 11:13:43 UTC   (17kb,1)" in db_txt_abs
    assert "Date (revised v4): Thu, 8 Oct 2009 13:10:42 UTC   (16kb,1)" in db_txt_abs
    assert "Title: Recent developments in unconventional superconductivity theory" in db_txt_abs
    assert "Authors: V.P.Mineev" in db_txt_abs
    assert "Categories: cond-mat.supr-con cond-mat.mtrl-sci" in db_txt_abs
    assert "Comments: 15 pages" in db_txt_abs
    assert "License: http://arxiv.org/licenses/nonexclusive-distrib/1.0/" in db_txt_abs


@pytest.mark.skip(reason="fs doesn't exactly match db")
def test_fmt_txt_2112_db_vs_fs(dbclient, client_with_test_fs):
    """Test abs/nnn?fmt=txt."""
    fsclient = client_with_test_fs

    db_txt_abs = dbclient.get('/abs/0906.2112?fmt=txt').data.decode('utf-8')
    fs_txt_abs = fsclient.get('/abs/0906.2112?fmt=txt').data.decode('utf-8')
    assert fs_txt_abs == db_txt_abs


@pytest.mark.skip(reason="fs doesn't exactly match db")
def test_fmt_txt_5132_db_vs_fs(dbclient, client_with_test_fs):
    """Test abs/nnn?fmt=txt."""
    fsclient = client_with_test_fs

    db_txt_abs = dbclient.get('/abs/0906.5132?fmt=txt').data.decode('utf-8')
    fs_txt_abs = fsclient.get('/abs/0906.5132?fmt=txt').data.decode('utf-8')
    assert fs_txt_abs == db_txt_abs
