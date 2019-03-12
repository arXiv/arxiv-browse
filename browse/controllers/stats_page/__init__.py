"""Handle requests to display and return stats about the arXiv service."""

from datetime import date, datetime, timezone
from typing import Any, Dict, Tuple
from werkzeug.exceptions import InternalServerError, BadRequest
from browse.services.database import get_hourly_stats, \
    get_monthly_download_stats
from arxiv import status


NUM_NODES = 4
Response = Tuple[Dict[str, Any], int, Dict[str, Any]]


def get_hourly_stats_csv() -> Response:
    """Get the hourly stats in CSV format."""
    hourly_stats: dict = {}
    max_node: int = NUM_NODES
    try:
        requested_date = date(2019, 1, 2)
        rows = get_hourly_stats(requested_date)
        for r in rows:
            hour_dt: str = datetime(
                r.ymd.year, r.ymd.month, r.ymd.day,
                hour=r.hour).strftime('%Y-%m-%dT%H:%M:%SZ')
            if hour_dt not in hourly_stats:
                hourly_stats[hour_dt] = {}
            hourly_stats[hour_dt][r.node_num] = r.connections
            if r.node_num > max_node:
                max_node = r.node_num
        csv = 'hour'+''.join(f",node{i}" for i in range(1, max_node+1)) + "\n"
        for hour in sorted(hourly_stats):
            csv = csv + hour
            for node in range(1, max_node+1):
                count = hourly_stats[hour][node] if node in hourly_stats[hour] else 0
                csv = csv + f",{count}"
            csv = f"{csv}\n"
        return {'csv': csv}, status.HTTP_200_OK, {'Content-Type': 'text/csv'}

    except TypeError as e:
        raise BadRequest
    except Exception as e:
        raise InternalServerError

def get_download_stats_csv() -> Response:
    """Get download stats in CSV format."""
    download_stats: dict = {}

    try:
        rows = get_monthly_download_stats()
        csv = "month,downloads\n"
        for r in rows:
            csv = f"{csv}{r.ym[0:7]},{r.downloads}\n"
        print(csv)
        return {'csv': csv}, status.HTTP_200_OK, {'Content-Type': 'text/plain'}
    except Exception as e:
        raise InternalServerError
