"""Handle requests to display and return stats about the arXiv service."""

from datetime import date
from typing import Any, Dict, Tuple
from werkzeug.exceptions import InternalServerError, BadRequest
from browse.services.database import get_hourly_stats


Response = Tuple[Dict[str, Any], int, Dict[str, Any]]


def get_hourly_stats_csv() -> Response:
    try:
        requested_date = date(2019, 1, 2)
        rows = get_hourly_stats(requested_date)
        # for r in rows:
        #     print(f'{r}\n')

    except TypeError as e:
        print(f'error: {e}')
        raise BadRequest
    except Exception as e:
        print(f'error: {e}')
        raise InternalServerError
