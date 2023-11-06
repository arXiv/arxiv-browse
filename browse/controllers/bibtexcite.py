"""Gets BibTeX citation for the paper."""
from typing import Callable

from browse.domain.identifier import IdentifierIsArchiveException, IdentifierException
from browse.formatting.cite import arxiv_bibtex
from browse.services.documents import get_doc_service
from browse.services.documents.base_documents import (
    AbsDeletedException, AbsException, AbsNotFoundException,
    AbsVersionNotFoundException)
from flask import Response, make_response


def _handle_failure(func: Callable[[str],Response]) -> Callable[[str],Response]:
    """Handle errors similar to get_abs_page."""
    def wrapper(arxiv_id:str) -> Response:
        try:
            return func(arxiv_id)
        except AbsNotFoundException:
            return make_response("{'reason': 'not_found'}", 404)
        except AbsVersionNotFoundException:
            return make_response("{'reason': 'version_not_found'}", 404)
        except AbsDeletedException:
            return make_response("{'reason': 'deleted'}", 404)
        except (IdentifierIsArchiveException, IdentifierException):
            return make_response("{'reason': 'bad_id'}", 400)
        except AbsException:
            return make_response("", 400)
        # For all others let it fail and we'll notice the error in the logs.
        # Rethrowing as InternalServerError hides the error from the logs.

    return wrapper


@_handle_failure
def bibtex_citation(arxiv_id: str) -> Response:
    """Get citation for the paper in BibTeX format.

    Parameters
    ----------
    arxiv_id : str
        The arXiv identifier as provided in the request.

    Returns
    -------
    Flask response

    """
    abs_meta = get_doc_service().get_abs(arxiv_id)
    bibtex = arxiv_bibtex(abs_meta)
    response = make_response(bibtex, 200)
    response.mimetype = 'text/plain'
    return response
