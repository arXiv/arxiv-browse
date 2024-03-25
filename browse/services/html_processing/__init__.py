import arxiv.document.exceptions
from flask import render_template, url_for
from arxiv.identifier import Identifier, IdentifierException
import re
from io import BytesIO
import urllib.parse
from arxiv.document.metadata import DocMetadata
from browse.services.documents import get_doc_service
from browse.controllers.list_page import dl_for_article, latexml_links_for_article, authors_for_article
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

LAX_ID_REGEX = b'(arXiv:)?([a-z-]+(\.[A-Z][A-Z])?\/\d{7}|\d{4}\.\d{4,5})(v\d+)?'

def post_process_html(byte_line:bytes) -> bytes:
    """Transformes each `byte_line` with the HTML post processing to
    add in any ABS or LIST lines.

    If this is run after the app code returns, say with
    `make_resposne(post_process_html(somefile))` this needs to be used with
    `flask.stream_with_context`.
    """
    #line=byte_line.decode('utf-8')
    # Match LIST: or ABS: directives followed by an identifier using regular expressions
    list_match = re.match(b'(LIST|ABS):(' + LAX_ID_REGEX + b')', byte_line, re.I)
    report_no_match = re.match(b'^\s*REPORT-NO:([A-Za-z0-9-\/]+)', byte_line, re.I)
    if list_match:
        try:
            cmd = list_match.group(1) #which command to perform
            if cmd==b'ABS':
                include_abstract=True
            else:
                include_abstract=False
            id = list_match.group(2).decode('utf-8') #document ID
            arxiv_id=Identifier(id)

            new_html = "<dl>\n"

            if arxiv_id:
                #get and format metadata here as html
                metadata=get_doc_service().get_abs(arxiv_id)
                downloads= dl_for_article(metadata)
                latexml=latexml_links_for_article(metadata)
                author_links=authors_for_article(metadata)
                item_string=render_template('list/conference_item.html',
                                            item=metadata,
                                            include_abstract=include_abstract,
                                            downloads=downloads,
                                            latexml=latexml,
                                            author_links=author_links,
                                            url_for_author_search=author_query )

                new_html+= item_string
            else:
                new_html += f"<dd>{id} [failed to get identifier for paper]</dd>\n"

            new_html += "</dl>\n"
            new_bytes=new_html.encode('utf-8')
        except (arxiv.document.exceptions.AbsException, IdentifierException ) as ee:
            new_bytes = byte_line
            logger.error(f"Source of html paper had a problem during post_process_html: {ee}")

    elif report_no_match: #need to find proceeding to test with
        rn = report_no_match.group(1).decode('utf-8')
        url_encoded_rn = urllib.parse.quote(rn,safe="")
        new_html=f"<a href=\"/search/?searchtype=report_num&query={url_encoded_rn}\">{rn}</a>\n"
        new_bytes=new_html.encode('utf-8')
    else:
        new_bytes = byte_line
    return new_bytes

def author_query(article: DocMetadata, query: str)->str:
    return str(url_for('search_box', searchtype='author', query=query))
