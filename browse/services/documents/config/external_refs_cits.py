"""Configuration for external reference and citation resources."""
from datetime import date


start_of_time = date(1900, 1, 1)
INSPIRE_REF_CIT_CATEGORIES = {
    'hep-th': start_of_time,
    'hep-lat': start_of_time,
    'hep-ph': start_of_time,
    'hep-ex': start_of_time,
    'gr-qc': start_of_time,
    'quant-ph': start_of_time,
    'astro-ph': start_of_time,
    'nucl-th': start_of_time,
    'nucl-ex': start_of_time,
    'acc-phys': start_of_time,
    'physics.acc-ph': start_of_time,
    'astro-ph.CO': date(2013, 1, 1),
    'astro-ph.HE': date(2013, 1, 1),
    'physics.data-an': date(2013, 1, 1),
    'physics.ins-det': date(2013, 1, 1)
}
"""
This specifies which categories/archives should have INSPIRE reference and
citation links from the arXiv abstract pages. The date indicates when
INSPIRE started adding papers from that category/archive.
Prior to 2013, INSPIRE only had arXiv papers from a subset of the
categories/archives. Starting in 2013, several additional categories
were added. INSPIRE also includes individual papers outside the below
categories a case-by-case basis, but as of 2014-03 there is no attempt
in the arXiv system to handle these (see also ARXIVDEV-2089).
"""

DBLP_BASE_URL = 'https://dblp.uni-trier.de'
DBLP_BIBTEX_PATH = '/rec/bibtex'
DBLP_AUTHOR_SEARCH_PATH = '/search/author'
DBLP_ARCHIVES = ['cs', 'cmp-lg']
DBLP_START_DATE = date(2005, 1, 1)
"""
Config params for the DBLP Bibliography service for Computer Science papers.

In cases where the browse DB service is unavailable, we can generate DBLP links
programmatically if papers were published in the archives specified in
DBLP_ARCHIVES after the date specified in DBLP_START_DATE."""
