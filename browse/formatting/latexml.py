from typing import Optional

from browse.domain.identifier import Identifier
from browse.services.database import get_latexml_status_for_document
from browse.services.document.metadata import get_abs

def get_latexml_url (identifier: Identifier) -> Optional[str]:
    LATEXML_URI_BASE = "https://services.dev.arxiv.org/html"
    if identifier.has_version:
        status = get_latexml_status_for_document(identifier.id, identifier.version)
        path = f'{identifier.id}v{identifier.version}/{identifier.id}v{identifier.version}.html'
    else:
        version = get_abs(identifier.id).highest_version()
        status = get_latexml_status_for_document(identifier.id, version)
        path = f'{identifier.id}v{version}/{identifier.id}v{version}.html'
    return f'{LATEXML_URI_BASE}/{path}' if status == 1 else None