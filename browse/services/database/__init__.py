"""Import db instance and define utility functions."""

import ipaddress
from datetime import datetime
from dateutil.tz import tzutc, gettz
from typing import List, Optional, Any
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

def db_handle_operational_error(logger: Logger, default_return_val: Any):
    """Decorator for handling operational database errors."""
    def decorator(func):
        def wrapper(*args, **kwargs):
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


@db_handle_operational_error(logger=logger, default_return_val=None)
def get_institution(ip: str) -> Optional[str]:
    """Get institution label from IP address."""
    decimal_ip = int(ipaddress.ip_address(ip))
    try:
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
        institution_name = db.session.query(stmt.c.label).\
            filter(stmt.c.exclusions == 0).one().label
        assert isinstance(institution_name, str)
        return institution_name
    except NoResultFound:
        return None


@db_handle_operational_error(logger=logger, default_return_val=[])
def get_all_trackback_pings() -> List[TrackbackPing]:
    """Get all trackback pings in database."""
    try:
        return list(__all_trackbacks_query().all())
    except NoResultFound:
        return []


@db_handle_operational_error(logger=logger, default_return_val=[])
def get_trackback_pings(paper_id: str) -> List[TrackbackPing]:
    """Get trackback pings for a particular document (paper_id)."""
    try:
        return list(__paper_trackbacks_query(paper_id).all())
    except NoResultFound:
        return []
    return []


@db_handle_operational_error(logger=logger, default_return_val=None)
def get_trackback_ping_latest_date(paper_id: str) -> Optional[datetime]:
    """Get the most recent accepted trackback datetime for a paper_id."""
    try:
        timestamp: int = db.session.query(
            func.max(TrackbackPing.approved_time)
        ).filter(TrackbackPing.document_id == Document.document_id) \
            .filter(Document.paper_id == paper_id) \
            .filter(TrackbackPing.status == 'accepted').scalar()
        dt = datetime.fromtimestamp(timestamp, tz=gettz('US/Eastern'))
        dt = dt.astimezone(tz=tzutc())
        return dt
    except NoResultFound:
        return None


@db_handle_operational_error(logger=logger, default_return_val=0)
def count_trackback_pings(paper_id: str) -> int:
    """Count trackback pings for a particular document (paper_id)."""
    try:
        count: int = __paper_trackbacks_query(paper_id) \
            .group_by(TrackbackPing.url).count()
        return count
    except NoResultFound:
        return 0
    return 0


@db_handle_operational_error(logger=logger, default_return_val=0)
def count_all_trackback_pings() -> int:
    """Count trackback pings for all documents, without DISTINCT(URL)."""
    try:
        c = __all_trackbacks_query().count()
        assert isinstance(c, int)
        return c
    except NoResultFound:
        return 0


@db_handle_operational_error(logger=logger, default_return_val=False)
def has_sciencewise_ping(paper_id_v: str) -> bool:
    """Determine whether versioned document has a ScienceWISE ping."""
    try:
        test: bool = db.session.query(SciencewisePing) \
            .filter(SciencewisePing.paper_id_v == paper_id_v).count() > 0
        return test
    except NoResultFound:
        return False
    return False


@db_handle_operational_error(logger=logger, default_return_val=None)
def get_dblp_listing_path(paper_id: str) -> Optional[str]:
    """Get the DBLP Bibliography URL for a given document (paper_id)."""
    try:
        url: str = db.session.query(DBLP.url).join(Document).filter(
            Document.paper_id == paper_id).one().url
        return url
    except NoResultFound:
        return None


@db_handle_operational_error(logger=logger, default_return_val=None)
def get_dblp_authors(paper_id: str) -> List[str]:
    """Get sorted list of DBLP authors for a given document (paper_id)."""
    try:
        authors_t = db.session.query(DBLPAuthor.name).\
            join(DBLPDocumentAuthor).\
            join(Document).filter(Document.paper_id == paper_id).\
            order_by(DBLPDocumentAuthor.position).all()
        authors = [a for (a,) in authors_t]
        return authors
    except NoResultFound:
        return []
