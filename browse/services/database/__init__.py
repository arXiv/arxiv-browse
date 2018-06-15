"""Import db instance and define utility functions."""

import ipaddress
from typing import List, Optional
from sqlalchemy.sql import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Query
from sqlalchemy.orm.exc import NoResultFound
from browse.services.database.models import db, ArXivDocument, \
    MemberInstitution, MemberInstitutionIP, TrackbackPing


def __all_trackbacks_query() -> Query:
    return db.session.query(TrackbackPing)


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
        stmt = (db.session.query(TrackbackPing))
    except NoResultFound:
        return []
    except SQLAlchemyError as e:
        raise IOError('Database error: %s' % e) from e


def get_trackback_pings(paper_id: str) -> List[TrackbackPing]:
    """Get trackback pings for a particular document (paper_id)."""
    try:
        stmt = __all_trackbacks_query
    except NoResultFound:
        return []
    except SQLAlchemyError as e:
        raise IOError('Database error: %s' % e) from e


def count_trackback_pings(paper_id: str)-> int:
    """Count trackback pings for a particular document (paper_id)."""

    return get_trackback_pings(paper_id).count()


def count_all_trackback_pings()-> int:
    """Count trackback pings for a particular document (paper_id)."""

    return __all_trackbacks_query().count() # type: ignore 
