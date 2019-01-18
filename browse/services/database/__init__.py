"""Import db instance and define utility functions."""

import ipaddress
from datetime import datetime
from dateutil.tz import tzutc, gettz
from typing import List, Optional, Any, Callable
from sqlalchemy import not_
from sqlalchemy.sql import func
from sqlalchemy.orm import Query
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import OperationalError, DBAPIError
from arxiv.base.globals import get_application_config

from browse.services.database.models import db, Document, \
    MemberInstitution, MemberInstitutionIP, TrackbackPing, SciencewisePing, \
    DBLP, DBLPAuthor, DBLPDocumentAuthor
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
def get_trackback_pings(paper_id: str) -> List[TrackbackPing]:
    """Get trackback pings for a particular document (paper_id)."""
    return list(__paper_trackbacks_query(paper_id)
                .distinct(TrackbackPing.url)
                .group_by(TrackbackPing.url)
                .order_by(TrackbackPing.posted_date.desc()).all())


@db_handle_error(logger=logger, default_return_val=[])
def get_recent_trackback_pings(count: int=20) -> List[TrackbackPing]:
    """Get recent trackback pings across all of arXiv."""
    return list(__all_trackbacks_query()
                .filter(TrackbackPing.status == 'accepted')
                .distinct(TrackbackPing.url)
                .group_by(TrackbackPing.url)
                .order_by(TrackbackPing.posted_date.desc()).all())


@db_handle_error(logger=logger, default_return_val=None)
def get_trackback_ping_latest_date(paper_id: str) -> Optional[datetime]:
    """Get the most recent accepted trackback datetime for a paper_id."""
    timestamp: int = db.session.query(
        func.max(TrackbackPing.approved_time)
    ).filter(TrackbackPing.document_id == Document.document_id) \
        .filter(Document.paper_id == paper_id) \
        .filter(TrackbackPing.status == 'accepted').scalar()
    dt = datetime.fromtimestamp(timestamp, tz=tz)
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
    document_count: int = db.session.query(Document).\
        filter(not_(Document.paper_id.like('test%'))).count()
    return document_count
