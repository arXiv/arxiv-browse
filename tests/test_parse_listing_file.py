from pathlib import Path

from browse.services.listing import Listing
from browse.services.listing.parse_listing_file import get_updates_from_list_file, _parse_item

ASTRO_LISTS = "ftp/astro-ph/listings"


def test_month_00s(abs_path):
    files = list( (abs_path / ASTRO_LISTS).glob("./0*"))
    for file in files:
        yy = file.stem[0:2]
        mm = file.stem[2:4]
        parsed = get_updates_from_list_file(yy, mm, file, "month")
        assert parsed and isinstance(parsed, Listing)
        assert parsed.listings
        assert parsed.count
        assert parsed.expires

def test_month_10s(abs_path):
    files = list( (abs_path / ASTRO_LISTS).glob("./1*"))
    for file in files:
        yy = file.stem[0:2]
        mm = file.stem[2:4]
        parsed = get_updates_from_list_file(yy, mm, file, "month")
        assert parsed and isinstance(parsed, Listing)
        assert parsed.listings
        assert parsed.count
        assert parsed.expires

def test_month_20s(abs_path):
    files = list( (abs_path / ASTRO_LISTS).glob("./2*"))
    for file in files:
        yy = file.stem[0:2]
        mm = file.stem[2:4]
        parsed = get_updates_from_list_file(yy, mm, file, "month")
        assert parsed and isinstance(parsed, Listing)
        assert parsed.listings
        assert parsed.count
        assert parsed.expires


def test_month_90s(abs_path):
    files = list( (abs_path / ASTRO_LISTS).glob("./9*"))
    for file in files:
        yy = file.stem[0:2]
        mm = file.stem[2:4]
        parsed = get_updates_from_list_file(yy, mm, file, "month")
        assert parsed and isinstance(parsed, Listing)
        assert parsed.listings
        assert parsed.count
        assert parsed.expires

def test_astroph_9204(abs_path):
    file = abs_path / ASTRO_LISTS / '9204'
    parsed = get_updates_from_list_file(1992,4, file, "month")
    assert parsed and isinstance(parsed, Listing)
    assert parsed.listings
    assert parsed.count
    assert parsed.expires

    assert len(parsed.listings) == 6
    item = parsed.listings[0]
    assert item.id == "astro-ph/9204001"
    assert item.listingType == 'new'
    assert item.primary == "astro-ph"


def test_parse_item():
    examples = [
        {'data':r"""Paper: astro-ph/9204001
From: Tsvi  <example@example.com>
Date: Mon, 13 Apr 1992 18:20:01 GMT   (11kb)

Title: Gamma-Ray Bursts as the Death Throes of Massive Binary Stars
Authors: Ramesh Narayan, Bohdan Paczy\'nski, and Tsvi Piran
Categories: astro-ph
Comments: 14 pages
Journal-ref: Astrophys.J. 395 (1992) L83-L86""",
         'expected':[
             ("title", "Gamma-Ray Bursts as the Death Throes of Massive Binary Stars"),
         ],
         },
        {'data':r"""arXiv:2301.00010
From: Dibyendu Nandy  <example@example.com>
Date: Fri, 30 Dec 2022 11:18:21 GMT   (819kb)

Title: Exploring the Solar Poles: The Last Great Frontier of the Sun
Authors: Dibyendu Nandy, Dipankar Banerjee, Prantika Bhowmik, Allan Sacha Brun,
  Robert H. Cameron, S. E. Gibson, Shravan Hanasoge, Louise Harra, Donald M.
  Hassler, Rekha Jain, Jie Jiang, Laur\`ene Jouve, Duncan H. Mackay, Sushant S.
  Mahajan, Cristina H. Mandrini, Mathew Owens, Shaonwita Pal, Rui F. Pinto,
  Chitradeep Saha, Xudong Sun, Durgesh Tripathi, Ilya G. Usoskin
Categories: astro-ph.IM astro-ph.SR physics.space-ph
Comments: This White Paper was submitted in 2022 to the United States National
  Academies Solar and Space Physics (Heliophysics) Decadal Survey
License: http://creativecommons.org/licenses/by-nc-nd/4.0/""",

         },
        {'data':r"""arXiv:2301.00027
From: Casey Papovich  <example@example.com>
Date: Fri, 30 Dec 2022 19:00:12 GMT   (3739kb,D)

Title: CEERS Key Paper IV: Galaxies at $4 < z < 9$ are Bluer than They Appear
  -- Characterizing Galaxy Stellar Populations from Rest-Frame $\sim 1$ micron
  Imaging
Authors: Casey Papovich (Texas A&M University), Justin Cole, Guang Yang, Steven
  L. Finkelstein, Guillermo Barro, V\'eronique Buat, Denis Burgarella, Pablo G.
  P\'erez-Gonz\'alez, Paola Santini, Lise-Marie Seill\'e, Lu Shen, Pablo
  Arrabal Haro, Micaela B. Bagley, Eric F. Bell, Laura Bisigello, Antonello
  Calabr\`o, Caitlin M. Casey, Marco Castellano, Katherine Chworowsky, Nikko J.
  Cleri, M. C. Cooper, Luca Costantin, Mark Dickinson, Henry C. Ferguson,
  Adriano Fontana, Mauro Giavalisco, Andrea Grazian, Norman A. Grogin, Nimish
  P. Hathi, Benne W. Holwerda, Taylor A. Hutchison, Jeyhan S. Kartaltepe, Lisa
  J. Kewley, Allison Kirkpatrick, Dale D. Kocevski, Anton M. Koekemoer, Rebecca
  L. Larson, Arianna S. Long, Ray A. Lucas, Laura Pentericci, Nor Pirzkal,
  Swara Ravindranath, Rachel S. Somerville, Jonathan R. Trump, et al. (5
  additional authors not shown)
Categories: astro-ph.GA
Comments: submitted to ApJ as part of the CEERS Focus Issue. 27 pages, many
  figures (4 Figure Sets, available upon reasonable request)
License: http://creativecommons.org/licenses/by/4.0/""",
         },
        {'data':r"""Paper (*cross-listing*): gr-qc/9401026
From:  <example@example.com>
Date: Tue, 25 Jan 1994 19:21:39 GMT   (9kb)

Title: Relaxed Bounds on the Dilaton Mass in a String Cosmology Scenario
Authors: M. Gasperini
Categories: gr-qc astro-ph hep-th
Comments: 12 pages, plain tex, 2 figures (available on request) DFTT-03/94
Journal-ref: Phys.Lett. B327 (1994) 214-220""",
         'neworcross':'cross',
         },
        {'data':r"""arXiv:2301.01082
From: Sumanta Kumar Sahoo  <example@example.com>
Date: Tue, 3 Jan 2023 13:17:28 GMT   (6183kb,AD)

Title: A search for variable subdwarf B stars in TESS Full Frame Images III. An
  update on variable targets in both ecliptic hemispheres -- contamination
  analysis and new sdB pulsators
Authors: S. K. Sahoo (1 and 2), A. S. Baran (2, 3 and 4), H.L. Worters (5), P.
  N\'emeth (2, 6 and 7) and D. Kilkenny (8) ((1) Nicolaus Copernicus
  Astronomical Centre of the Polish Academy of Sciences Poland, (2) ARDASTELLA
  Research Group Poland, (3) Astronomical Observatory of University of Warsaw
  Poland, (4) Missouri State University USA, (5) South African Astronomical
  Observatory South Africa, (6) Astronomical Institute of the Czech Academy of
  Sciences Czech Republic, (7) Astroserver.org Hungary, (8) University of the
  Western Cape South Africa)
Categories: astro-ph.SR
Journal-ref: Monthly Notices of the Royal Astronomical Society, Volume 519,
  Issue 2, February 2023, Pages 2486-2499
DOI: 10.1093/mnras/stac3676
License: http://creativecommons.org/licenses/by/4.0/""",
         'expected':[
             ('journal_ref', 'Monthly Notices of the Royal Astronomical Society, Volume 519, Issue 2, February 2023, Pages 2486-2499')
         ]
         },
        ]

    for ex in examples:
        item, neworcross = _parse_item(ex['data'].split("\n"))
        assert item
        if 'neworcross' in ex:
            assert neworcross == ex['neworcross']
        if 'expected' in ex:
            for name, value in ex['expected']:
                assert getattr(item, name) == value , f"check of {name} failed"
