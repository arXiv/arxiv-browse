"""Handle requests to display and return stats about the arXiv service."""

import dateutil.parser
from datetime import datetime, timedelta
from typing import Any, Dict, Tuple
from werkzeug.exceptions import InternalServerError, BadRequest

from arxiv import status
from arxiv.base import logging
from browse.services.database import get_hourly_stats, get_hourly_stats_count, \
    get_monthly_download_stats, get_monthly_submission_stats, \
    get_monthly_submission_count, get_monthly_download_count, \
    get_max_download_stats_dt
from browse.services.document.config.deleted_papers import DELETED_PAPERS


NUM_NODES = 4
Response = Tuple[Dict[str, Any], int, Dict[str, Any]]
logger = logging.getLogger(__name__)


def get_hourly_stats_page(requested_date_str: str = None) -> Response:
    """Get data for the /stats/today page."""
    response_data: Dict[str, Any] = {}
    try:
        current_dt = datetime.now()
        requested_dt = current_dt - timedelta(hours=1)
        if requested_date_str:
            requested_dt = dateutil.parser.parse(requested_date_str)
        normal_count, admin_count = \
            get_hourly_stats_count(stats_date=requested_dt.date())

        response_data['current_dt'] = current_dt
        response_data['requested_dt'] = requested_dt
        response_data['normal_count'] = normal_count
        response_data['admin_count'] = admin_count
        return response_data, status.HTTP_200_OK, {}
    except (TypeError, ValueError):
        raise BadRequest
    except Exception as ex:
        logger.warning(f'Error getting hourly stats data: {ex}')
        raise InternalServerError


def get_hourly_stats_csv(requested_date_str: str = None) -> Response:
    """Get the hourly stats in CSV format."""
    hourly_stats: dict = {}
    max_node: int = NUM_NODES
    try:
        requested_dt = datetime.now() - timedelta(hours=1)
        if requested_date_str:
            requested_dt = dateutil.parser.parse(requested_date_str)
        rows = get_hourly_stats(stats_date=requested_dt.date())
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
                count = hourly_stats[hour][node] \
                    if node in hourly_stats[hour] else 0
                csv = csv + f",{count}"
            csv = f"{csv}\n"
        return {'csv': csv}, status.HTTP_200_OK, {'Content-Type': 'text/csv'}
    except (TypeError, ValueError) as ex:
        logger.warning(f'Type error getting sequential hourly stats csv: {ex}')
        raise BadRequest
    except Exception as ex:
        logger.warning(f'Error getting sequential hourly stats csv: {ex}')
        raise InternalServerError


def get_monthly_downloads_page() -> Response:
    """Get the data from the monthly downloads page."""
    response_data: Dict[str, Any] = {}
    try:
        response_data['total_downloads'] = get_monthly_download_count()
        response_data['most_recent_dt'] = get_max_download_stats_dt()
        return response_data, status.HTTP_200_OK, {}
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
    except Exception as ex:
        logger.warning(f'Error getting monthly download stats csv: {ex}')
        raise InternalServerError


def get_monthly_submissions_page() -> Response:
    """Get the data from the monthly submissions page."""
    response_data: Dict[str, Any] = {}
    current_dt = datetime.now()
    arxiv_start_dt = datetime(year=1991, month=8, day=1)
    arxiv_age = current_dt - arxiv_start_dt
    try:
        num_submissions, historical_delta = \
            get_monthly_submission_count()
        response_data['num_migrated'] = abs(historical_delta)
        response_data['num_deleted'] = len(DELETED_PAPERS)
        response_data['num_submissions'] = num_submissions
        response_data['current_dt'] = current_dt
        response_data['arxiv_start_dt'] = arxiv_start_dt
        response_data['num_deleted_papers'] = 0
        response_data['arxiv_age_years'] = arxiv_age.days / 365
        return response_data, status.HTTP_200_OK, {}
    except Exception as ex:
        logger.warning(f'Error getting monthly submissions stats data: {ex}')
        raise InternalServerError


def get_submission_stats_csv() -> Response:
    """Get submission stats in CSV format."""
    try:
        rows = get_monthly_submission_stats()
        csv = "month,submissions,historical_delta\n"
        for r in rows:
            csv = f"{csv}{r.ym.strftime('%Y-%m')},{r.num_submissions},{r.historical_delta}\n"
        return {'csv': csv}, status.HTTP_200_OK, {'Content-Type': 'text/csv'}
    except Exception as ex:
        logger.warning(f'Error getting monthly submission stats csv: {ex}')
        raise InternalServerError
