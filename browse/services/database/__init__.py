"""Import db instance and define utility functions."""

import ipaddress
from typing import List, Optional
from sqlalchemy.sql import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Query
from sqlalchemy.orm.exc import NoResultFound

from browse.services.database.models import db, Document, \
    MemberInstitution, MemberInstitutionIP, TrackbackPing, SciencewisePing


def __all_trackbacks_query() -> Query:
    return db.session.query(TrackbackPing)


def __paper_trackbacks_query(paper_id) -> Query:
    return __all_trackbacks_query() \
        .filter(TrackbackPing.document_id == Document.document_id) \
        .filter(Document.paper_id == paper_id) \
        .filter(TrackbackPing.status == 'accepted')


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
        return institution_name  # type: ignore
    except NoResultFound:
        return None
    except SQLAlchemyError as e:
        raise IOError('Database error: %s' % e) from e


def get_all_trackback_pings() -> List[TrackbackPing]:
    """Get all trackback pings in database."""
    try:
        return list(__all_trackbacks_query().all())
    except NoResultFound:
        return []
    except SQLAlchemyError as e:
        raise IOError('Database error: %s' % e) from e


def get_trackback_pings(paper_id: str) -> List[TrackbackPing]:
    """Get trackback pings for a particular document (paper_id)."""
    try:
        return list(__paper_trackbacks_query(paper_id).all())
    except NoResultFound:
        return []
    except SQLAlchemyError as e:
        raise IOError('Database error: %s' % e) from e


def count_trackback_pings(paper_id: str) -> int:
    """Count trackback pings for a particular document (paper_id)."""
    return __paper_trackbacks_query(paper_id)\
        .group_by(TrackbackPing.url).count()


def count_all_trackback_pings() -> int:
    """Count trackback pings for all documents, without DISTINCT(URL)."""
    return __all_trackbacks_query().count()  # type: ignore


def has_sciencewise_ping(paper_id_v: str) -> bool:
    """Determine whether versioned document has a ScienceWISE ping."""
    try:
        return db.session.query(SciencewisePing) \
            .filter(SciencewisePing.paper_id_v == paper_id_v).count() > 0
    except NoResultFound:
        return False
    except SQLAlchemyError as e:
        raise IOError('Database error: %s' % e) from e
