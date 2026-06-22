"""Tests for the /repec RePEc/ReDIF interface."""


def test_repec_index(dbclient):
    """Top-level index lists the archive, series and papers dir."""
    rv = dbclient.get("/repec")
    assert rv.status_code == 200
    assert rv.mimetype == "text/html"
    src = rv.data.decode("utf-8")
    assert "arxarch.rdf" in src
    assert "arxseri.rdf" in src
    assert "papers/" in src

    # trailing slash maps to the same index
    assert dbclient.get("/repec/").status_code == 200


def test_repec_archive_record(dbclient):
    rv = dbclient.get("/repec/arxarch.rdf")
    assert rv.status_code == 200
    assert rv.mimetype == "text/plain"
    src = rv.data.decode("utf-8")
    assert "Template-type: ReDIF-Archive 1.0" in src
    assert "Handle: RePEc:arx" in src


def test_repec_series_record(dbclient):
    rv = dbclient.get("/repec/arxseri.rdf")
    assert rv.status_code == 200
    src = rv.data.decode("utf-8")
    assert "Template-type: ReDIF-Series 1.0" in src
    assert "Handle: RePEc:arx:papers" in src


def test_repec_papers_index(dbclient):
    rv = dbclient.get("/repec/papers/")
    assert rv.status_code == 200
    assert rv.mimetype == "text/html"
    src = rv.data.decode("utf-8")
    # q-fin's group start year through the current year are advertised
    assert "2024.rdf" in src


def test_repec_not_found(dbclient):
    assert dbclient.get("/repec/bogus").status_code == 404
    assert dbclient.get("/repec/papers/9999.rdf").status_code == 404


def test_repec_year_file(dbclient):
    """A year file renders as plain text (empty if no q-fin/econ data)."""
    rv = dbclient.get("/repec/papers/2024.rdf")
    assert rv.status_code == 200
    assert rv.mimetype == "text/plain"


def test_repec_item_format(client_with_test_fs):
    """A single ReDIF-Paper record has the expected fields.

    Exercised directly because the test fixtures contain no q-fin/econ papers,
    so the year-file route never reaches the item renderer. The FS-backed client
    provides the app context get_doc_service() needs and has this paper.
    """
    from browse.controllers import repec

    out = repec._item("1607.08199")
    assert out is not None
    lines = out.splitlines()

    assert lines[0] == "Template-type: ReDIF-Paper 1.0"
    assert "Author-Name: Marcello Bernardara" in lines
    assert "Author-X-Name-First: Marcello" in lines
    assert "Author-X-Name-Last: Bernardara" in lines
    assert "Title: Bridgeland Stability Conditions on Fano Threefolds" in lines
    assert "File-URL: https://arxiv.org/pdf/1607.08199" in lines
    assert "File-Format: application/pdf" in lines
    assert "File-Function: Latest version" in lines
    assert "Handle: RePEc:arx:papers:1607.08199" in lines
    # v1 in 2016, current version in 2017 -> both dates present
    assert "Creation-Date: 2016-07" in lines
    assert "Revision-Date: 2017-04" in lines


def test_repec_item_abstract_wrapping(client_with_test_fs):
    """Abstract wraps at 80 columns with 2-space-indented continuation lines."""
    from browse.controllers import repec

    out = repec._item("1607.08199")
    lines = out.splitlines()

    abs_idx = next(i for i, ln in enumerate(lines) if ln.startswith("Abstract:"))
    # first abstract line: "Abstract: " label + 2-space indented text -> 3 spaces
    assert lines[abs_idx].startswith("Abstract:   We show")

    # continuation lines run until the next ReDIF field (e.g. Creation-Date:)
    cont = []
    for ln in lines[abs_idx + 1:]:
        if ln.startswith("  "):
            cont.append(ln)
        else:
            break
    assert cont, "abstract should wrap onto continuation lines"
    for ln in cont:
        assert ln.startswith("  "), "continuation lines indented by two spaces"
        assert len(ln) <= 80, f"line exceeds 80 columns: {ln!r}"
