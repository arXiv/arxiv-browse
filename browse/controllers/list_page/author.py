from typing import Optional, Dict, Any, Tuple, List
from urllib.parse import unquote
import re
from datetime import datetime, time

from arxiv.taxonomy.definitions import CATEGORIES
from lxml.etree import Element, SubElement, tostring, QName
from datetime import timezone

from flask import request, url_for
from werkzeug.exceptions import BadRequest

from arxiv.document.metadata import DocMetadata

from arxiv.authors import parse_author_affil
from arxiv.taxonomy.category import Category

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

def get_json (id: str) -> Optional[Dict]:
    user_id, is_orcid = _get_user_id(id)
    if user_id is None:
        return None

    entries = []
    for li in get_articles_for_author(user_id):
        entries.append(_make_json_entry(get_doc_service().get_abs(li.id)))

    if is_orcid:
        orcid = f'{ORCID_URI_PREFIX}/{unquote(id)}'
    else:
        orcid = _get_orcid_uri(user_id) or ''

    return {
        'entries': entries,
        'id': f'{request.url_root}{id}',
        'modified': str(datetime.combine(datetime.today(), time.min, timezone.utc).isoformat()),
        'orcid': orcid,
        'title': f'{get_user_display_name(user_id)}\'s articles on arXiv'
    }

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

    def author_query(article: DocMetadata, query: str) -> str:
        try:
            if article.primary_archive:
                archive = article.primary_archive.id
            else:
                archive = CATEGORIES[article.primary_category.id].in_archive  # type: ignore
            return str(url_for('search_archive',
                           searchtype='author',
                           archive=archive,
                           query=query))
        except (AttributeError, KeyError):
            return str(url_for('search_archive',
                               searchtype='author',
                               archive=None,  # TODO: This should be handled somehow
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


def _guess_pub_date(metadata: DocMetadata) -> Optional[str]:
    """Very old submisisons lack a pub date so guess one from the id"""
    if metadata.arxiv_identifier.year is None or \
       metadata.arxiv_identifier.month is None:
        return None

    yy = metadata.arxiv_identifier.year
    if yy > 90:
        yyyy = 1900 + yy
    else:
        yyyy = 20 + yy

    return f"{yyyy}-{metadata.arxiv_identifier.month}-01:00:00.000000"


def _make_json_entry (metadata: DocMetadata) -> Dict[str, str]:
    entry: Dict[str, Any] = {}

    # 'authors' field
    entry['authors'] = ', '.join(map(_author_name, parse_author_affil(metadata.authors.raw)))

    # 'categories' field
    all_categories = []
    if metadata.primary_category:
        all_categories.append(metadata.primary_category.display())
        if metadata.secondary_categories:
            all_categories.extend(map(lambda cat: cat.display(), metadata.secondary_categories))
    entry['categories'] = ', '.join(all_categories)

    # 'comment' field
    entry['comment'] = metadata.comments if metadata.comments else ''

    # 'doi' field
    if metadata.doi: # don't include if None
        entry['doi'] = metadata.doi

    # 'formats' field
    # TODO: ps format? It doesn't seem like this is possible in the arXiv-NG implementation
    entry['formats'] = {
        'html': metadata.canonical_url(),
        'pdf': url_for('dissemination.pdf', arxiv_id=metadata.arxiv_id_v, _external=True)
    }

    # 'id' field
    # TODO: This seems to be redundant with entry['formats']['html'] right above
    entry['id'] = metadata.canonical_url()

    # 'journal_ref' field
    if metadata.journal_ref:
        entry['journal_ref'] = metadata.journal_ref

    # 'published' field
    pubdate = metadata.get_datetime_of_version(1)
    entry['published'] = pubdate.isoformat() if pubdate is not None \
        else _guess_pub_date(metadata)

    # 'subject' field
    if metadata.primary_category:
        entry['subject'] = metadata.primary_category.display()

    # 'summary' field
    entry['summary'] = re.sub(r'\n+', ' ', metadata.abstract.strip())

    # 'title' field
    entry['title'] = metadata.title

    # 'updated' field
    dt_ver = metadata.get_datetime_of_version(metadata.version)
    if dt_ver:
        entry['updated'] = str(dt_ver.isoformat())

    return entry


def _add_atom_feed_entry (metadata: DocMetadata, feed: Element, atom2: bool = False) -> None:
    entry = SubElement(feed, 'entry')
    SubElement(entry, 'id').text = metadata.canonical_url()
    dt_ver = metadata.get_datetime_of_version(metadata.version)
    if dt_ver is not None:
        SubElement(entry, 'updated').text = str(dt_ver.isoformat())
    dt_orig_ver = metadata.get_datetime_of_version(1)
    if dt_orig_ver is not None:
        SubElement(entry, 'published').text = str(dt_orig_ver.isoformat())
    SubElement(entry, 'title').text = metadata.title
    SubElement(entry, 'summary').text = re.sub(r'\n+', ' ', metadata.abstract.strip())
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
                    SubElement(author, QName(ARXIV_SCHEMA_URI, 'affiliation'), nsmap={
                        'arxiv': ARXIV_SCHEMA_URI
                    }).text = affil
    if metadata.doi:
        SubElement(entry, QName(ARXIV_SCHEMA_URI, 'doi'), nsmap={
            'arxiv': ARXIV_SCHEMA_URI
        }).text = metadata.doi
    if metadata.comments:
        SubElement(entry, QName(ARXIV_SCHEMA_URI, 'comment'), nsmap={
            'arxiv': ARXIV_SCHEMA_URI
        }).text = metadata.comments
    if metadata.journal_ref:
        SubElement(entry, QName(ARXIV_SCHEMA_URI, 'journal_ref'), nsmap={
            'arxiv': ARXIV_SCHEMA_URI
        }).text = metadata.journal_ref
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

    #TODO: ps link

    all_categories: List[Category] = []
    if metadata.primary_category:
        all_categories.append(metadata.primary_category)
    else:
        return
    if metadata.secondary_categories:
        all_categories.extend(metadata.secondary_categories)

    SubElement(entry, QName(ARXIV_SCHEMA_URI, 'primary_category'), attrib={
        'term': metadata.primary_category.id,
        'scheme': ARXIV_SCHEMA_URI,
        'label': metadata.primary_category.display()
    }, nsmap={
        'arxiv': ARXIV_SCHEMA_URI
    })

    for category in all_categories:
        SubElement(entry, 'category', attrib={
            'term': category.id,
            'scheme': ARXIV_SCHEMA_URI,
            'label': category.display()
        })
    

def _get_atom_feed (id: str, atom2: bool = False) -> str:
    user_id, is_orcid = _get_user_id(id)

    if user_id is None:
        raise BadRequest (f'Author {id} not found')
    
    feed = Element('feed', attrib={'xmlns': 'http://www.w3.org/2005/Atom'})
    SubElement(feed, 'title').text = f'{get_user_display_name(user_id)}\'s articles on arXiv'
    SubElement(feed, 'link', attrib={ 
        'rel': 'describes', 
        'href': (f'{ORCID_URI_PREFIX}/{unquote(id)}' 
                if is_orcid else _get_orcid_uri(user_id))
    })
    # TODO: May need to add timezone info
    SubElement(feed, 'updated').text = str(datetime.combine(datetime.today(), time.min, timezone.utc).isoformat())
    SubElement(feed, 'id').text = f'{request.url_root}{id}'
    SubElement(feed, 'link', 
               attrib={
                   'href': request.base_url,
                   'rel': 'self',
                   'type': 'application/atom+xml'
               })
    SubElement(feed, 'link', 
               attrib={ 
                    'rel': 'describes', 
                    'href': f'{request.url_root}{id}'
                })
    
    for li in get_articles_for_author(user_id):
        _add_atom_feed_entry(get_doc_service().get_abs(li.id), feed, atom2)

    return tostring(feed, pretty_print=True, xml_declaration=True, encoding='UTF-8')  # type: ignore
    

