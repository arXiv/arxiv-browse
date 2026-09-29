import arxiv.document.exceptions
import arxiv.formats.html
from flask import render_template, url_for
from arxiv.identifier import Identifier
from typing import Optional
from arxiv.document.metadata import DocMetadata
from browse.services.documents import get_doc_service
from browse.controllers.list_page import dl_for_article, latexml_links_for_article, authors_for_article
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def post_process_html(byte_line:bytes) -> bytes:
    """Transformes each `byte_line` with the HTML post processing to
    add in any ABS or LIST lines.

    If this is run after the app code returns, say with
    `make_resposne(post_process_html(somefile))` this needs to be used with
    `flask.stream_with_context`.
    """
    return arxiv.formats.html.post_process_html(byte_line, _conference_item)

def _conference_item(arxiv_id: Identifier, include_abstract: bool) -> Optional[str]:
    """The listing of a paper for a LIST: or ABS: line."""
    try:
        metadata=get_doc_service().get_abs(arxiv_id)
    except arxiv.document.exceptions.AbsException as ee:
        logger.error(f"Source of html paper had a problem during post_process_html: {ee}")
        return None
    downloads= dl_for_article(metadata)
    latexml=latexml_links_for_article(metadata)
    author_links=authors_for_article(metadata)
    return render_template('list/conference_item.html',
                           item=metadata,
                           include_abstract=include_abstract,
                           downloads=downloads,
                           latexml=latexml,
                           author_links=author_links,
                           url_for_author_search=author_query )

def author_query(article: DocMetadata, query: str)->str:
    return str(url_for('search_box', searchtype='author', query=query))
