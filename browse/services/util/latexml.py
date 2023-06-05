from typing import Optional

from browse.domain.identifier import Identifier
from browse.services.database import get_latexml_status_for_document

def get_latexml_url (identifier: Identifier) -> Optional[str]:
    LATEXML_URI_BASE = "https://services.dev.arxiv.org/conversion/download/paper?arxiv_id="
    if identifier.has_version:
        status = get_latexml_status_for_document(identifier.id, identifier.version)
    else:
        status = get_latexml_status_for_document(identifier.id)
    return (LATEXML_URI_BASE + identifier.idv) if status == 1 else None