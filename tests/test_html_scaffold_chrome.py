"""The HTML-paper scaffold has one header: the design system's site header without its site
navigation, with the paper's controls as its page actions (article_scaffold/header.html)."""
from flask import render_template

from browse.services.html_processing.scaffold import ArticleScaffoldMetadata


def test_paper_controls_are_in_the_site_header(app_with_test_fs):
    meta = ArticleScaffoldMetadata(license="License: CC BY 4.0", page_id="0906.3336v1", published=True,
                                   primary_category="math.DG", date_of_version="18 Jun 2009")
    with app_with_test_fs.test_request_context("/html/0906.3336v1"):   # the scaffold's own route
        html = render_template("dissemination/article_scaffold/header.html", meta=meta)
    start = html.index('<header class="ds-site-header')
    header = html[start:html.index("</header>", start)]
    assert 'class="ds-site-header-tools"' in header
    assert 'class="color-tog"' in header
    assert 'id="ds-site-header-nav"' not in html and "Log in" not in html
    assert 'id="ds-search-toggle"' not in html
    assert '<span class="arxiv-html-header"></span>' in html   # reading mode's marker
