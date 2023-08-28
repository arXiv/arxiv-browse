"""Tests /archive path."""

def test_astroph_archive(client_with_test_fs):
    rv = client_with_test_fs.get("/archive/astro-ph")
    assert rv.status_code == 200
    assert 'Expires' in rv.headers, 'Should have expires header'

    rv = client_with_test_fs.get("/archive/astro-ph/")
    assert rv.status_code == 200, 'Trailing slash should be allowed'

    src = rv.data.decode("utf-8")
    assert "Astrophysics" in src
    assert "/year/astro-ph/92" in src
    assert "/year/astro-ph/19" in src

    assert "Astrophysics of Galaxies" in src, "Subcategories of astro-ph should be on archive page"
    assert "Earth and Planetary Astrophysics" in src, "Subcategories of astro-ph should be on archive page"

def test_list(client_with_test_fs):
    rv = client_with_test_fs.get("/archive/list")
    assert rv.status_code == 200
    src = rv.data.decode("utf-8")

    assert "Astrophysics" in src
    assert "astro-ph" in src

    assert "Materials Theory" in src
    assert "mtrl-th" in src

    rv = client_with_test_fs.get("/archive/bogus-archive")
    assert rv.status_code == 404

def test_subsumed_archive(client_with_test_fs):
    rv = client_with_test_fs.get("/archive/comp-lg")
    assert rv.status_code == 404
    src = rv.data.decode("utf-8")

    assert "Computer Science" in src
    assert "cs.CL" in src

    rv = client_with_test_fs.get("/archive/acc-phys")
    assert rv.status_code == 200
    src = rv.data.decode("utf-8")

    assert "Accelerator Physics" in src
    assert "physics.acc-ph" in src

def test_single_archive(client_with_test_fs):
    rv = client_with_test_fs.get("/archive/hep-ph")
    assert rv.status_code == 200
    src = rv.data.decode("utf-8")

    assert "High Energy Physics" in src
    assert "Categories within" not in src

def test_301_redirects(client_with_test_fs):
    rv = client_with_test_fs.get("/archive/astro-ph/Astrophysics")
    assert rv.status_code == 301, "/archive/astro-ph/Astrophysics should get a 301 redirect ARXIVNG-2119"
