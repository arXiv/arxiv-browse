"""Handle requests to display and return stats about the arXiv service."""

from datetime import date, datetime, timezone
from typing import Any, Dict, Tuple
from werkzeug.exceptions import InternalServerError, BadRequest

from arxiv import status
from arxiv.base import logging
from browse.services.database import get_hourly_stats, \
    get_monthly_download_stats, get_monthly_submission_stats


NUM_NODES = 4
Response = Tuple[Dict[str, Any], int, Dict[str, Any]]
logger = logging.getLogger(__name__)

def get_hourly_stats_csv() -> Response:
    """Get the hourly stats in CSV format."""
    hourly_stats: dict = {}
    max_node: int = NUM_NODES
    try:
        requested_date = date(2019, 1, 2)
        rows = get_hourly_stats(requested_date)
        assert rows is not None
        for r in rows:
            hour_dt: str = datetime(
                r.ymd.year, r.ymd.month, r.ymd.day,
                hour=r.hour).strftime('%Y-%m-%dT%H:%M:%SZ')
            if hour_dt not in hourly_stats:
                hourly_stats[hour_dt] = {}
            hourly_stats[hour_dt][r.node_num] = r.connections
            if r.node_num > max_node:
                max_node = r.node_num
        csv = 'hour' + \
            ''.join(f",node{i}" for i in range(1, max_node + 1)) + "\n"
        for hour in sorted(hourly_stats):
            csv = csv + hour
            for node in range(1, max_node + 1):
                count = hourly_stats[hour][node] if node in hourly_stats[hour] else 0
                csv = csv + f",{count}"
            csv = f"{csv}\n"
        return {'csv': csv}, status.HTTP_200_OK, {'Content-Type': 'text/csv'}
    except TypeError:
        raise BadRequest
    except Exception:
        raise InternalServerError


def get_download_stats_csv() -> Response:
    """Get download stats in CSV format."""
    try:
        rows = get_monthly_download_stats()
        csv = "month,downloads\n"
        for r in rows:
            csv = f"{csv}{r.ym.strftime('%Y-%m')},{r.downloads}\n"
        return {'csv': csv}, status.HTTP_200_OK, {'Content-Type': 'text/csv'}
    except Exception as e:
        print(e)
        raise InternalServerError


def get_submission_stats_csv() -> Response:
    """Get submission stats in CSV format."""
    try:
        rows = get_monthly_submission_stats()
        csv = "month,submissions,historical_delta\n"
        for r in rows:
            csv = f"{csv}{r.ym.strftime('%Y-%m')},{r.num_submissions},{r.historical_delta}\n"
        return {'csv': csv}, status.HTTP_200_OK, {'Content-Type': 'text/csv'}
    except Exception:
        raise InternalServerError
