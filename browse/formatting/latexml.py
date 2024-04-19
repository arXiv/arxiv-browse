from typing import Optional, Dict, List, Any

from flask import current_app

from arxiv.document.metadata import DocMetadata

from browse.services.database import (
    get_latexml_status_for_document,
    get_latexml_status_for_listings
)

import logging

def get_latexml_url (article: DocMetadata, most_recent: bool=False) -> Optional[str]:
    if not current_app.config["LATEXML_ENABLED"]:
        return None
    LATEXML_URI_BASE = current_app.config['LATEXML_BASE_URL']
    status = get_latexml_status_for_document(article.arxiv_id, article.highest_version()) if most_recent \
             else get_latexml_status_for_document(article.arxiv_id, article.version)
    logging.debug(f'{article.arxiv_id_v} version: {article.version}, highest_version: {article.highest_version()}')
    path = f'html/{article.arxiv_id}v{article.version}'
    return f'{LATEXML_URI_BASE}/{path}' if status == 1 else None

def get_latexml_url_for_listings (listings: List[Any]) -> Dict[str, Any]:
    if not current_app.config['LATEXML_ENABLED']:
        return {}
    LATEXML_URI_BASE = current_app.config['LATEXML_BASE_URL']
    statuses = get_latexml_status_for_listings(listings)
    result: Dict[str, Optional[str]] = {}
    for k, v in statuses.items():
        if v:
            path = f'html/{k[0]}v{k[1]}'
            result[f'{k[0]}v{k[1]}'] = f'{LATEXML_URI_BASE}/{path}'
        else:
            result[f'{k[0]}v{k[1]}'] = None
    return result