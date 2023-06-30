from typing import Optional, Dict, Any, Tuple, List
from urllib.parse import unquote
import re
from datetime import datetime, time
from lxml.etree import Element, SubElement, tostring, QName
import json
import xmltodict

from flask import request, url_for
from werkzeug.exceptions import BadRequest

from browse.domain.metadata import DocMetadata

from arxiv.util.authors import parse_author_affil
from arxiv.taxonomy import Category

from ...services.database import (
    get_user_id_by_author_id, 
    get_user_id_by_orcid,
    get_user_display_name,
    get_orcid_by_user_id,
    get_articles_for_author
)
from browse.services.documents import get_doc_service

from browse.controllers.list_page import (
    dl_for_articles, 
    latexml_links_for_articles,
    authors_for_articles,
)


ORCID_URI_PREFIX = 'https://orcid.org'
ORCID_RE = re.compile(r'^(\d{4}\-\d{4}\-\d{4}-\d{3}[\dX])$')

ARXIV_SCHEMA_URI = 'http://arxiv.org/schemas/atom'

def get_atom (id: str) -> str:
    return _get_atom_feed(id, False)

def get_atom2 (id: str) -> str:
    return _get_atom_feed(id, True)

def get_json (id: str) -> Dict:
    return xmltodict.parse(get_atom(id), xml_attribs=False)

def get_html_page (id: str) -> Tuple[Dict[str, Optional[Any]], int, Dict[str, str]]:
    user_id, is_orcid = _get_user_id(id)
    if user_id is None:
        raise BadRequest (f'Author {id} not found')
    
    response_data: Dict[str, Any] = {}

    response_data['display_name'] = get_user_display_name(user_id)
    response_data['auri'] = f'{request.url_root}{id}'
    if is_orcid:
        response_data['orcid'] = f'{ORCID_URI_PREFIX}/{unquote(id)}'
    else:
        response_data['orcid'] = _get_orcid_uri (user_id)
    response_data['title'] = f'{response_data["display_name"]}\'s articles on arXiv'

    listings = get_articles_for_author(user_id)
    for i, item in enumerate(listings):
        setattr(item, 'article', get_doc_service().get_abs(item.id))
        setattr(item, 'list_index', i + 1)

    response_data['abstracts'] = listings
    response_data['downloads'] = dl_for_articles(listings)
    response_data['latexml'] = latexml_links_for_articles(listings)
    response_data['author_links'] = authors_for_articles(listings)

    def author_query(article: DocMetadata, query: str)->str:
        try:
            if article.primary_archive:
                archive = article.primary_archive.id
            else:
                archive = CATEGORIES[article.primary_category.id]['in_archive'] # type: ignore
            return str(url_for('search_archive',
                           searchtype='author',
                           archive=archive,
                           query=query))
        except (AttributeError, KeyError):
            return str(url_for('search_archive',
                               searchtype='author',
                               archive=None, # TODO: This should be handled somehow
                               query=query))
    
    response_data['url_for_author_search'] = author_query

    return response_data, 200, dict()

def _get_user_id (raw_id: str) -> Tuple[Optional[int], bool]:
    id = unquote(raw_id) # Check if flask does this automatically
    if ORCID_RE.match(id):
        return get_user_id_by_orcid(id), True
    return get_user_id_by_author_id(id), False

def _get_orcid_uri (user_id: int) -> Optional[str]:
    orcid = get_orcid_by_user_id(user_id)
    if orcid is not None:
        return f'{ORCID_URI_PREFIX}/{orcid}'
    return None

def _author_name (author_line: List[str]) -> str:
    return f'{author_line[1]} {author_line[0]} {author_line[2]}'.strip()

def _author_affils (author_line: List[str]) -> Optional[List[str]]:
    return author_line[3:] if len(author_line) > 3 else None

def _add_atom_feed_entry (metadata: DocMetadata, feed: Element, atom2: bool = False):    
    entry = SubElement(feed, 'entry')
    SubElement(entry, 'id').text = metadata.arxiv_id_v
    SubElement(entry, 'updated').text = str(metadata.get_datetime_of_version(metadata.version))
    SubElement(entry, 'published').text = str(metadata.get_datetime_of_version(1))
    SubElement(entry, 'title').text = metadata.title
    SubElement(entry, 'summary').text = metadata.abstract
    if atom2:
        names = ', '.join(map(_author_name, parse_author_affil(metadata.authors.raw)))
        author = SubElement(entry, 'author')
        SubElement(author, 'name').text = names
    else:
        for author_line in parse_author_affil(metadata.authors.raw):
            author = SubElement(entry, 'author')
            SubElement(author, 'name').text = _author_name(author_line)
            affils = _author_affils(author_line)
            if affils:
                for affil in affils:
                    SubElement(author, QName(ARXIV_SCHEMA_URI, 'affiliation')).text = affil
    if metadata.comments:
        SubElement(entry, QName(ARXIV_SCHEMA_URI, 'comment')).text = metadata.comments
    if metadata.journal_ref:
        SubElement(entry, QName(ARXIV_SCHEMA_URI, 'journal_ref')).text = metadata.journal_ref
    SubElement(entry, 'link', attrib={ 
        'href': metadata.canonical_url(),
        'rel': 'alternate', 
        'type': 'text/html'
    })

    #TODO: linkType, linkScore?

    SubElement(entry, 'link', attrib={
        'title': 'pdf',
        'href': url_for('dissemination.pdf', arxiv_id=metadata.arxiv_id_v, _external=True),
        'rel': 'alternate', 
        'type': 'application/pdf'
    })

    all_categories = []
    if metadata.primary_category:
        all_categories.append(metadata.primary_category)
    else:
        return
    if metadata.secondary_categories:
        all_categories.extend(metadata.secondary_categories)

    SubElement(entry, QName(ARXIV_SCHEMA_URI, 'primary_category'), attrib={
        'term': metadata.primary_category.id,
        'scheme': ARXIV_SCHEMA_URI,
        'label': metadata.primary_category.display
    })

    for category in all_categories:
        SubElement(entry, 'category', attrib={
            'term': category.id,
            'scheme': ARXIV_SCHEMA_URI,
            'label': category.display
        })
    

def _get_atom_feed (id: str, atom2: bool = False) -> str:
    user_id, is_orcid = _get_user_id(id)

    if user_id is None:
        raise BadRequest (f'Author {id} not found')
    
    feed = Element('feed', attrib={'xmlns': 'http://www.w3.org/2005/Atom'}, nsmap={
        'arxiv': ARXIV_SCHEMA_URI
    })
    SubElement(feed, 'title').text = get_user_display_name(user_id)
    SubElement(feed, 'link', attrib={ 
        'rel': 'describes', 
        'href': (f'{ORCID_URI_PREFIX}/{unquote(id)}' 
                if is_orcid else _get_orcid_uri(user_id))
    })
    # TODO: May need to add timezone info
    SubElement(feed, 'updated').text = str(datetime.combine(datetime.today(), time.min))
    SubElement(feed, 'id').text = f'{request.url_root}{id}'
    SubElement(feed, 'link', 
               attrib={ 
                    'rel': 'describes', 
                    'href': f'{request.url_root}{id}'
                })
    
    for li in get_articles_for_author(user_id):
        _add_atom_feed_entry(get_doc_service().get_abs(li.id), feed, atom2)

    return tostring(feed, pretty_print=True)
    

