from flask import render_template, url_for
from browse.domain.identifier import Identifier
import re
import urllib.parse
from browse.domain.metadata import DocMetadata
from browse.services.documents import get_doc_service
from browse.controllers.list_page import dl_for_article, latexml_links_for_article, authors_for_article

LIST_ITEM_RE = re.compile(r'<\!--\s(.+)\s-->\nLIST:(.+)\n')
LAX_ID_REGEX = '(arXiv:)?([a-z-]+(\.[A-Z][A-Z])?\/\d{7}|\d{4}\.\d{4,5})(v\d+)?'

def post_process_html(html:str) -> str:
    new_html=""
    #do we still want to count expansions?

    for line in html.split('\n'):
        # Match LIST: or ABS: directives followed by an identifier using regular expressions
        list_match = re.match(r'(LIST|ABS):(' + LAX_ID_REGEX + ')', line, re.I)
        report_no_match = re.match(r'^\s*REPORT-NO:([A-Za-z0-9-\/]+)', line, re.I)

        if list_match:
            cmd = list_match.group(1) #which command to perform
            if cmd=='ABS':
                include_abstract=True
            else:
                include_abstract=False
            id = list_match.group(2) #document ID
            arxiv_id=Identifier(id) 

            new_html += "<dl>\n"

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

        elif report_no_match: #need to find proceeding to test with
            rn = report_no_match.group(1)
            url_encoded_rn = urllib.parse.quote(rn,safe="")
            new_html+=f"<a href=\"/search/?searchtype=report_num&query={url_encoded_rn}\">{rn}</a>\n"

        else:
            new_html += line + "\n"
    return new_html

def author_query(article: DocMetadata, query: str)->str:
    return str(url_for('search_box', searchtype='author', query=query))