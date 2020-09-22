"""Gets bibtex citation for the paper."""
from typing import Callable
from flask import make_response, Response

from werkzeug.exceptions import InternalServerError

from browse.exceptions import AbsNotFound
from browse.services.document import metadata
from browse.services.document.metadata import AbsNotFoundException, \
    AbsVersionNotFoundException, AbsDeletedException
from browse.services.cite import arxiv_bibtex


def _handle_failure(func: Callable[[str],Response]) -> Callable[[str],Response]:
    """Handle errors similar to get_abs_page."""
    def wrapper(arxiv_id:str) -> Response:
        try:
            return func(arxiv_id)
        except AbsNotFoundException:
            raise AbsNotFound(data={'reason': 'not_found'})
        except AbsVersionNotFoundException:
            raise AbsNotFound(data={'reason': 'version_not_found'})
        except AbsDeletedException as e:
            raise AbsNotFound(data={'reason': 'deleted', 'message': e})
        except Exception as ee:
            raise InternalServerError() from ee

    return wrapper


@_handle_failure
def bibtex_citation(arxiv_id: str) -> Response:
    """Get citation for the paper in bibtex format.

    Parameters
    ----------
    arxiv_id : str
        The arXiv identifier as provided in the request.

    Returns
    -------
    Flask response

    """
    abs_meta = metadata.get_abs(arxiv_id)
    bibtex = arxiv_bibtex(abs_meta)
    response = make_response(bibtex, 200)
    response.mimetype = 'text/plain'
    return response
