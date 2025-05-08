"""Controller for audio page."""
from typing import Dict, Tuple

from arxiv.identifier import Identifier
from arxiv.integration.fastly.headers import add_surrogate_key
from flask import render_template

from browse.exceptions import AbsNotFound
from browse.services.audio import get_audio_urls
from browse.services.documents import get_doc_service


def audio_landing_page(arxiv_id: str) -> Tuple:
    headers: Dict[str, str] = {}
    if not Identifier.is_mostly_safe(arxiv_id):
        raise AbsNotFound(data={"reason": "poorly formatted paper id"})

    arxiv_identifier = Identifier(arxiv_id=arxiv_id)
    headers = add_surrogate_key(headers, [f"paper-id-{arxiv_identifier.id}", "audio-landing"])
    abs_meta = get_doc_service().get_abs(arxiv_identifier)
    data = {'audio_urls': get_audio_urls(abs_meta),
            "abs_meta": abs_meta
            }
    return render_template('audio_landing_page.html', **data), 200, headers
