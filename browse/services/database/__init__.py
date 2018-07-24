"""Import db instance and define utility functions."""

import ipaddress
from typing import List, Optional
from sqlalchemy.sql import func
from sqlalchemy.orm import Query
from sqlalchemy.orm.exc import NoResultFound

from browse.services.database.models import db, Document, \
    MemberInstitution, MemberInstitutionIP, TrackbackPing, SciencewisePing, \
    DBLP, DBLPAuthor, DBLPDocumentAuthor


def __all_trackbacks_query() -> Query:
    return db.session.query(TrackbackPing)


def __paper_trackbacks_query(paper_id: str) -> Query:
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


def get_all_trackback_pings() -> List[TrackbackPing]:
    """Get all trackback pings in database."""
    try:
        return list(__all_trackbacks_query().all())
    except NoResultFound:
        return []


def get_trackback_pings(paper_id: str) -> List[TrackbackPing]:
    """Get trackback pings for a particular document (paper_id)."""
    try:
        return list(__paper_trackbacks_query(paper_id).all())
    except NoResultFound:
        return []


def count_trackback_pings(paper_id: str) -> int:
    """Count trackback pings for a particular document (paper_id)."""
    try:
        count: int = __paper_trackbacks_query(paper_id) \
            .group_by(TrackbackPing.url).count()
        return count
    except NoResultFound:
        return 0


def count_all_trackback_pings() -> int:
    """Count trackback pings for all documents, without DISTINCT(URL)."""
    try:
        return __all_trackbacks_query().count()  # type: ignore
    except NoResultFound:
        return 0


def has_sciencewise_ping(paper_id_v: str) -> bool:
    """Determine whether versioned document has a ScienceWISE ping."""
    try:
        test: bool = db.session.query(SciencewisePing) \
            .filter(SciencewisePing.paper_id_v == paper_id_v).count() > 0
        return test
    except NoResultFound:
        return False


def get_dblp_listing_path(paper_id: str) -> Optional[str]:
    """Get the DBLP Bibliography URL for a given document (paper_id)."""
    try:
        url: str = db.session.query(DBLP.url).join(Document).filter(
            Document.paper_id == paper_id).one().url
        return url
    except NoResultFound:
        return None


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
