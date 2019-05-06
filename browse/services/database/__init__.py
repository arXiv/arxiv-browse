"""Import db instance and define utility functions."""

import ipaddress
from datetime import date, datetime
from dateutil.tz import tzutc, gettz
from typing import List, Optional, Any, Callable, Tuple
from sqlalchemy import not_, desc, asc
from sqlalchemy.sql import func
from sqlalchemy.orm import Query
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import OperationalError, DBAPIError
from arxiv.base.globals import get_application_config

from browse.services.database.models import db, Document, \
    MemberInstitution, MemberInstitutionIP, TrackbackPing, SciencewisePing, \
    DBLP, DBLPAuthor, DBLPDocumentAuthor, StatsMonthlySubmission, \
    StatsMonthlyDownload
from browse.services.database.models import in_category, stats_hourly
from browse.domain.identifier import Identifier
from arxiv.base import logging
from logging import Logger

logger = logging.getLogger(__name__)
app_config = get_application_config()
tz = gettz(app_config.get('ARXIV_BUSINESS_TZ', 'US/Eastern'))


def db_handle_error(logger: Logger, default_return_val: Any) \
        -> Any:
    """Handle operational database errors via decorator."""
    def decorator(func: Callable) -> Any:
        def wrapper(*args, **kwargs):  # type: ignore
            # Bypass attempt to perform query and just return default value
            is_db_disabled: bool = app_config.get(
                'BROWSE_DISABLE_DATABASE') or False
            if is_db_disabled:
                if logger:
                    logger.info(
                        'Database is disabled per BROWSE_DISABLE_DATABASE')
                return default_return_val
            try:
                return func(*args, **kwargs)
            except NoResultFound:
                return default_return_val
            except (OperationalError, DBAPIError) as ex:
                if logger:
                    logger.warning(
                        f'Error executing query in {func.__name__}: {ex}')
                return default_return_val
            except Exception as ex:
                if logger:
                    logger.warning(
                        f'Unknown exception in {func.__name__}: {ex}')
                raise
        return wrapper
    return decorator


def __all_trackbacks_query() -> Query:
    return db.session.query(TrackbackPing)


def __paper_trackbacks_query(paper_id: str) -> Query:
    return __all_trackbacks_query() \
        .filter(TrackbackPing.document_id == Document.document_id) \
        .filter(Document.paper_id == paper_id) \
        .filter(TrackbackPing.status == 'accepted')


@db_handle_error(logger=logger, default_return_val=None)
def get_institution(ip: str) -> Optional[str]:
    """Get institution label from IP address."""
    decimal_ip = int(ipaddress.ip_address(ip))

    stmt = (
        db.session.query(
            MemberInstitution.label,
            func.sum(MemberInstitutionIP.exclude).label("exclusions")
        ).
        join(MemberInstitutionIP).
        filter(
            MemberInstitutionIP.start <= decimal_ip,
            MemberInstitutionIP.end >= decimal_ip
        ).
        group_by(MemberInstitution.label).
        subquery()
    )
    institution_row = db.session.query(stmt.c.label).\
        filter(stmt.c.exclusions == 0).first()
    institution_name = None
    if institution_row:
        institution_name = institution_row.label
        assert isinstance(institution_name, str)
    return institution_name


@db_handle_error(logger=logger, default_return_val=[])
def get_all_trackback_pings() -> List[TrackbackPing]:
    """Get all trackback pings in database."""
    return list(__all_trackbacks_query().all())


@db_handle_error(logger=logger, default_return_val=[])
def get_paper_trackback_pings(paper_id: str) -> List[TrackbackPing]:
    """Get trackback pings for a particular document (paper_id)."""
    return list(__paper_trackbacks_query(paper_id)
                .distinct(TrackbackPing.url)
                .group_by(TrackbackPing.url)
                .order_by(TrackbackPing.posted_date.desc()).all())


@db_handle_error(logger=logger, default_return_val=None)
def get_trackback_ping(trackback_id: int) -> Optional[TrackbackPing]:
    """Get an individual trackback ping by its id (trackback_id)."""
    trackback: TrackbackPing = db.session.query(TrackbackPing).\
        filter(TrackbackPing.trackback_id == trackback_id).first()
    return trackback


@db_handle_error(logger=logger, default_return_val=list())
def get_recent_trackback_pings(max_trackbacks: int = 25) \
        -> List[Tuple[TrackbackPing, str, str]]:
    """Get recent trackback pings across all of arXiv."""
    max_trackbacks = min(max(max_trackbacks, 0), 500)
    if max_trackbacks == 0:
        return list()

    # subquery to get the specified number of distinct trackback URLs
    stmt = (
        db.session.query(TrackbackPing.url).
        filter(TrackbackPing.status == 'accepted').
        distinct(TrackbackPing.url).
        group_by(TrackbackPing.url).
        order_by(TrackbackPing.posted_date.desc()).
        limit(max_trackbacks).
        subquery()
    )
    tb_doc_tup = db.session.query(
        TrackbackPing,
        Document.paper_id,
        Document.title
    ).\
        join(Document, TrackbackPing.document_id == Document.document_id).\
        filter(TrackbackPing.status == 'accepted').\
        filter(TrackbackPing.url == stmt.c.url).\
        order_by(TrackbackPing.posted_date.desc()).\
        all()

    return list(tb_doc_tup)


@db_handle_error(logger=logger, default_return_val=None)
def get_trackback_ping_latest_date(paper_id: str) -> Optional[datetime]:
    """Get the most recent accepted trackback datetime for a paper_id."""
    timestamp: int = db.session.query(
        func.max(TrackbackPing.approved_time)
    ).filter(TrackbackPing.document_id == Document.document_id) \
        .filter(Document.paper_id == paper_id) \
        .filter(TrackbackPing.status == 'accepted').scalar()
    dt = datetime.fromtimestamp(timestamp, tz=gettz('US/Eastern'))
    dt = dt.astimezone(tz=tzutc())
    return dt


@db_handle_error(logger=logger, default_return_val=0)
def count_trackback_pings(paper_id: str) -> int:
    """Count trackback pings for a particular document (paper_id)."""
    count: int = __paper_trackbacks_query(paper_id) \
        .group_by(TrackbackPing.url).count()
    return count


@db_handle_error(logger=logger, default_return_val=0)
def count_all_trackback_pings() -> int:
    """Count trackback pings for all documents, without DISTINCT(URL)."""
    c = __all_trackbacks_query().count()
    assert isinstance(c, int)
    return c


@db_handle_error(logger=logger, default_return_val=False)
def has_sciencewise_ping(paper_id_v: str) -> bool:
    """Determine whether versioned document has a ScienceWISE ping."""
    has_ping: bool = db.session.query(SciencewisePing) \
        .filter(SciencewisePing.paper_id_v == paper_id_v).count() > 0
    return has_ping


@db_handle_error(logger=logger, default_return_val=None)
def get_dblp_listing_path(paper_id: str) -> Optional[str]:
    """Get the DBLP Bibliography URL for a given document (paper_id)."""
    url: str = db.session.query(DBLP.url).join(Document).filter(
        Document.paper_id == paper_id).one().url
    return url


@db_handle_error(logger=logger, default_return_val=[])
def get_dblp_authors(paper_id: str) -> List[str]:
    """Get sorted list of DBLP authors for a given document (paper_id)."""
    authors_t = db.session.query(DBLPAuthor.name).\
        join(DBLPDocumentAuthor).\
        join(Document).filter(Document.paper_id == paper_id).\
        order_by(DBLPDocumentAuthor.position).all()
    authors = [a for (a,) in authors_t]
    return authors


@db_handle_error(logger=logger, default_return_val=None)
def get_document_count() -> Optional[int]:
    """Get the number of documents."""
    # func.count is used here because .count() forces a subquery which
    # is inefficient
    row = db.session.query(
            func.count(Document.document_id).label('num_documents')
          ).filter(not_(Document.paper_id.like('test%'))).first()
    return row.num_documents


@db_handle_error(logger=logger, default_return_val=0)
def get_document_count_by_yymm(paper_date: Optional[date] = None) -> int:
    """Get number of papers for a given year and month."""
    paper_date = date.today() if not isinstance(paper_date, date) \
        else paper_date
    yymm = paper_date.strftime('%y%m')
    yymm_like = f'{yymm}%'
    if paper_date < date(2007, 4, 1):
        yymm_like = f'%/{yymm}%'
    row = db.session.query(
            func.count(Document.document_id).label('num_documents')
          ).filter(Document.paper_id.like(yymm_like))\
           .filter(not_(Document.paper_id.like('test%'))).first()
    return row.num_documents


@db_handle_error(logger=logger, default_return_val=None)
def get_sequential_id(paper_id: Identifier,
                      context: str = 'all',
                      is_next: bool = True) -> Optional[str]:
    """Get the next or previous paper ID in sequence."""
    query = db.session.query(Document.paper_id)
    if paper_id.is_old_id:
        # NB: classic did not support old identifiers in prevnext
        if context == 'all':
            like_id = f'{paper_id.archive}/{paper_id.yymm}%'
        else:
            like_id = f'%/{paper_id.yymm}%'
    else:
        like_id = f'{paper_id.yymm}.%'
    query = query.filter(Document.paper_id.like(like_id))

    if is_next:
        query = query.filter(Document.paper_id > paper_id.id). \
            order_by(asc(Document.paper_id))
    else:
        query = query.filter(Document.paper_id < paper_id.id). \
            order_by(desc(Document.paper_id))
    if context != 'all':
        archive: str = context
        subject_class: str = ''
        if '.' in archive:
            (archive, subject_class) = archive.split('.', 1)
        query = query.join(in_category).filter(
            in_category.c.archive == archive)
        if subject_class:
            query = query.filter(
                in_category.c.subject_class == subject_class)

    result = query.first()

    if result:
        return f'{result.paper_id}'
    return None


def __all_hourly_stats_query() -> Query:
    return db.session.query(stats_hourly)


@db_handle_error(logger=logger, default_return_val=(0, 0, 0))
def get_hourly_stats_count(stats_date: Optional[date]) -> Tuple[int, int]:
    """Get sum of normal/admin connections and nodes for a given date."""
    stats_date = date.today() if not isinstance(stats_date, date) \
        else stats_date
    normal_count = 0
    admin_count = 0
    num_nodes = 0
    rows = db.session.query(
        func.sum(stats_hourly.c.connections).label('num_connections'),
        stats_hourly.c.access_type,
        func.max(stats_hourly.c.node_num).label('num_nodes')).\
        filter(stats_hourly.c.ymd == stats_date.isoformat()).\
        group_by(stats_hourly.c.access_type).all()
    for r in rows:
        if r.access_type == 'A':
            admin_count = r.num_connections
        else:
            normal_count = r.num_connections
            num_nodes = r.num_nodes
    return (normal_count, admin_count, num_nodes)


@db_handle_error(logger=logger, default_return_val=[])
def get_hourly_stats(stats_date: Optional[date] = None) -> List:
    """Get the hourly stats for a given date."""
    stats_date = date.today() if not isinstance(stats_date, date) \
        else stats_date

    return list(__all_hourly_stats_query().
                filter(stats_hourly.c.access_type == 'N',
                       stats_hourly.c.ymd == stats_date.isoformat()).
                order_by(asc(stats_hourly.c.hour), stats_hourly.c.node_num).
                all())


@db_handle_error(logger=logger, default_return_val=[])
def get_monthly_submission_stats() -> List:
    """Get the monthly submission stats from StatsMonthlySubmission."""
    return list(db.session.query(StatsMonthlySubmission).
                order_by(asc(StatsMonthlySubmission.ym)).all())


@db_handle_error(logger=logger, default_return_val=(0, 0))
def get_monthly_submission_count() -> Tuple[int, int]:
    """Get submission totals: number of submissions and number migrated."""
    row = db.session.query(
        func.sum(
            StatsMonthlySubmission.num_submissions).label('num_submissions'),
        func.sum(
            StatsMonthlySubmission.historical_delta).label('num_migrated')
    ).first()
    return (row.num_submissions, row.num_migrated)


@db_handle_error(logger=logger, default_return_val=[])
def get_monthly_download_stats() -> List:
    """Get all the monthly download stats."""
    return list(db.session.query(StatsMonthlyDownload).
                order_by(asc(StatsMonthlyDownload.ym)).all())


@db_handle_error(logger=logger, default_return_val=0)
def get_monthly_download_count() -> int:
    """Get the sum of monthly downloads for all time."""
    row = db.session.query(
        func.sum(StatsMonthlyDownload.downloads).label('total_downloads')
    ).first()
    total_downloads: int = row.total_downloads if row else 0
    return total_downloads


@db_handle_error(logger=logger, default_return_val=None)
def get_max_download_stats_dt() -> Optional[datetime]:
    """Get the datetime of the most recent download stats."""
    row = db.session.query(
        func.max(StatsMonthlyDownload.ym).label('max_ym')
    ).first()
    return row.max_ym if row else None
