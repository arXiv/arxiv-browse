"""Handle requests to display and return stats about the arXiv service."""

from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from werkzeug.exceptions import InternalServerError, BadRequest
import dateutil.parser

from arxiv import status
from arxiv.base import logging

from browse.services.database import get_hourly_stats, get_hourly_stats_count, \
    get_monthly_download_stats, get_monthly_submission_stats, \
    get_monthly_submission_count, get_monthly_download_count, \
    get_max_download_stats_dt, get_document_count_by_yymm
from browse.services.documents.config.deleted_papers import DELETED_PAPERS


Response = Tuple[Dict[str, Any], int, Dict[str, Any]]
logger = logging.getLogger(__name__)

def get_main_stats_page() -> Response:
    """Minimal rendering of the main stats page."""
    response_data: Dict[str, Any] = {}
    return response_data, status.HTTP_200_OK, {}

def get_hourly_stats_page(requested_date_str: Optional[str] = None) -> Response:
    """Get data for the /stats/today page."""
    response_data: Dict[str, Any] = {}
    current_dt = datetime.now()
    requested_dt = current_dt - timedelta(hours=1)
    response_data['current_dt'] = current_dt
    response_data['requested_dt'] = requested_dt

    if requested_date_str:
        try:
            requested_dt = dateutil.parser.parse(requested_date_str)
            response_data['requested_dt'] = requested_dt
        except (TypeError, ValueError) as ex:
            raise BadRequest from ex

    try:
        normal_count, admin_count, num_nodes = \
            get_hourly_stats_count(stats_date=requested_dt.date())
    except Exception as ex:
        raise InternalServerError from ex

    response_data['normal_count'] = normal_count
    response_data['admin_count'] = admin_count
    response_data['num_nodes'] = num_nodes
    return response_data, status.HTTP_200_OK, {}


def get_hourly_stats_csv(requested_date_str: Optional[str] = None) -> Response:
    """Get the hourly stats in CSV format."""
    hourly_stats: dict = {}
    max_node = 1

    requested_dt = datetime.now() - timedelta(hours=1)
    if requested_date_str:
        try:
            requested_dt = dateutil.parser.parse(requested_date_str)
        except (TypeError, ValueError) as ex:
            raise BadRequest from ex
    try:
        rows = get_hourly_stats(stats_date=requested_dt.date())
    except Exception as ex:
        raise InternalServerError from ex

    for r in rows:
        hour_dt: str = datetime(
            r.ymd.year, r.ymd.month, r.ymd.day,
            hour=r.hour).strftime('%Y-%m-%dT%H:%M:%SZ')
        if hour_dt not in hourly_stats:
            hourly_stats[hour_dt] = {}
        hourly_stats[hour_dt][r.node_num] = r.connections
        if r.node_num > max_node:
            max_node = r.node_num
    csv_head = 'hour' + \
        "".join(f",node{i}" for i in range(1, max_node + 1)) + "\n"
    csv_data = ""
    for hour in sorted(hourly_stats):
        csv_data = csv_data + hour
        for node in range(1, max_node + 1):
            count = hourly_stats[hour][node] \
                if node in hourly_stats[hour] else 0
            csv_data = csv_data + f",{count}"
        csv_data = csv_data + "\n"
    return {'csv': csv_head + csv_data}, status.HTTP_200_OK, {'Content-Type': 'text/csv'}


def get_monthly_downloads_page() -> Response:
    """Get the data from the monthly downloads page."""
    response_data: Dict[str, Any] = {}
    try:
        response_data['total_downloads'] = get_monthly_download_count()
        response_data['most_recent_dt'] = get_max_download_stats_dt()
        return response_data, status.HTTP_200_OK, {}
    except Exception as ex:
        raise InternalServerError from ex


def get_download_stats_csv() -> Response:
    """Get download stats in CSV format."""
    csv_head = "month,downloads\n"
    try:
        csv_data = "".join([
            f"{r.ym.strftime('%Y-%m')},{r.downloads}\n"
            for r in get_monthly_download_stats()
        ])
        return {'csv': csv_head + csv_data}, status.HTTP_200_OK, {'Content-Type': 'text/csv'}
    except Exception as ex:
        raise InternalServerError from ex


def get_monthly_submissions_page() -> Response:
    """Get the data from the monthly submissions page."""
    response_data: Dict[str, Any] = {}
    current_dt = datetime.now()
    arxiv_start_dt = datetime(year=1991, month=8, day=1)
    arxiv_age = current_dt - arxiv_start_dt
    num_deleted = len(DELETED_PAPERS)
    try:
        num_submissions, historical_delta = \
            get_monthly_submission_count()
        num_this_month = get_document_count_by_yymm(current_dt.date)
        num_submissions += num_this_month
    except Exception as ex:
        raise InternalServerError

    num_migrated = abs(historical_delta)
    response_data['current_dt'] = current_dt
    response_data['arxiv_age_years'] = arxiv_age.days / 365
    response_data['arxiv_start_dt'] = arxiv_start_dt
    response_data['num_migrated'] = num_migrated
    response_data['num_deleted'] = num_deleted
    response_data['num_submissions'] = num_submissions
    response_data['num_submissions_adjusted'] = \
        num_submissions - num_deleted + num_migrated
    return response_data, status.HTTP_200_OK, {}


def get_submission_stats_csv() -> Response:
    """Get submission stats in CSV format."""
    csv_head = "month,submissions,historical_delta\n"
    current_date = date.today()
    try:
        rows = get_monthly_submission_stats()
        csv_data = "".join([
            f"{r.ym.strftime('%Y-%m')},{r.num_submissions},{r.historical_delta}\n"
            for r in rows
        ])
        if rows and rows[-1].ym < current_date:
            this_month_count = get_document_count_by_yymm(current_date)
            if this_month_count > 0:
                csv_data = csv_data + f"{current_date.strftime('%Y-%m')},{this_month_count},0\n"
        return {'csv': csv_head + csv_data}, status.HTTP_200_OK, {'Content-Type': 'text/csv'}
    except Exception as ex:
        raise InternalServerError from ex
