"""Tests /archive path."""

def test_astroph_archive(client_with_test_fs):
    rv = client_with_test_fs.get("/archive/astro-ph")
    assert rv.status_code == 200
    assert 'Expires' in rv.headers, 'Should have expires header'

    rv = client_with_test_fs.get("/archive/astro-ph/")
    assert rv.status_code == 200, 'Trailing slash should be allowed'

    src = rv.data.decode("utf-8")
    assert "Astrophysics" in src
    assert "/year/astro-ph/1992" in src
    assert "/year/astro-ph/2019" in src

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
    assert "No archive 'list'" not in src

    rv = client_with_test_fs.get("/archive/bogus-archive")
    assert rv.status_code == 404
    src = rv.data.decode("utf-8")

    assert "Astrophysics" in src
    assert "astro-ph" in src
    assert "Materials Theory" in src
    assert "mtrl-th" in src
    assert "No archive 'bogus-archive'" in src

    rv = client_with_test_fs.get("/archive")
    assert rv.status_code == 200
    src = rv.data.decode("utf-8")
    assert "Astrophysics" in src
    assert "astro-ph" in src
    assert "Materials Theory" in src
    assert "mtrl-th" in src
    assert "No archive '" not in src

def test_browse_form(client_with_test_fs):
    rv = client_with_test_fs.get("/archive/astro-ph")
    assert rv.status_code == 200
    assert '<input id="archive" name="archive" required type="hidden" value="astro-ph">' in rv.text
    assert '<select id="year" name="year" required>' in rv.text
    assert '<select id="month" name="month" required>' in rv.text
    assert '<input id="submit" name="submit" type="submit" value="Go">' in rv.text

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

def test_surrogate_keys(client_with_db_listings):
    client=client_with_db_listings

    rv = client.head("/archive/math")
    head=rv.headers["Surrogate-Key"]
    assert " archive " in " "+head+" "

    rv = client.head("/archive/comp-lg")
    head=rv.headers["Surrogate-Key"]
    assert " archive " in " "+head+" "

    rv = client.head("/archive")
    head=rv.headers["Surrogate-Key"]
    assert " archive " in " "+head+" "
