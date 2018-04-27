"""arXiv browse database models."""
from browse.domain.institution import Institution
import ipaddress
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import BigInteger, Column, DateTime, Enum, \
    ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound
from typing import Any, Optional
from werkzeug.local import LocalProxy

db: Any = SQLAlchemy()


class MemberInstitution(db.Model):
    """Primary model for arXiv member insitution data."""

    __tablename__ = 'Subscription_UniversalInstitution'

    resolver_URL = Column(String(255))
    name = Column(String(255), nullable=False, index=True)
    label = Column(String(255))
    id = Column(Integer, primary_key=True)
    alt_text = Column(String(255))
    link_icon = Column(String(255))
    note = Column(String(255))


class MemberInstitutionContact(db.Model):
    """Model for arXiv member institution contact information."""

    __tablename__ = 'Subscription_UniversalInstitutionContact'

    email = Column(String(255))
    sid = Column(ForeignKey('Subscription_UniversalInstitution.id',
                            ondelete='CASCADE'), nullable=False, index=True)
    active = Column(Integer, server_default=text("'0'"))
    contact_name = Column(String(255))
    id = Column(Integer, primary_key=True)
    phone = Column(String(255))
    note = Column(String(2048))

    Subscription_UniversalInstitution = relationship('MemberInstitution')


class MemberInstitutionIP(db.Model):
    """Model for arXiv member insitution IP address ranges and exclusions."""

    __tablename__ = 'Subscription_UniversalInstitutionIP'
    __table_args__ = (
        Index('ip', 'start', 'end'),
    )

    sid = Column(ForeignKey('Subscription_UniversalInstitution.id',
                            ondelete='CASCADE'), nullable=False, index=True)
    id = Column(Integer, primary_key=True)
    exclude = Column(Integer, server_default=text("'0'"))
    end = Column(BigInteger, nullable=False, index=True)
    start = Column(BigInteger, nullable=False, index=True)

    Subscription_UniversalInstitution = relationship('MemberInstitution')


class SciencewisePing(db.Model):
    """Model for ScienceWISE (trackback) pings."""

    __tablename__ = 'arXiv_sciencewise_pings'

    paper_id_v = Column(String(32), primary_key=True)
    updated = Column(DateTime)


class TrackbackPing(db.Model):
    """Primary model for arXiv trackback data."""

    __tablename__ = 'arXiv_trackback_pings'

    trackback_id = Column(Integer, primary_key=True)
    document_id = Column(Integer, index=True)
    title = Column(String(255), nullable=False, server_default=text("''"))
    excerpt = Column(String(255), nullable=False, server_default=text("''"))
    url = Column(String(255), nullable=False,
                 index=True, server_default=text("''"))
    blog_name = Column(String(255), nullable=False, server_default=text("''"))
    remote_host = Column(String(255), nullable=False,
                         server_default=text("''"))
    remote_addr = Column(String(16), nullable=False, server_default=text("''"))
    posted_date = Column(Integer, nullable=False,
                         index=True, server_default=text("'0'"))
    is_stale = Column(Integer, nullable=False, server_default=text("'0'"))
    approved_by_user = Column(Integer, nullable=False,
                              server_default=text("'0'"))
    approved_time = Column(Integer, nullable=False, server_default=text("'0'"))
    status = Column(Enum('pending', 'pending2', 'accepted',
                         'rejected', 'spam'),
                    nullable=False, index=True,
                    server_default=text("'pending'"))
    site_id = Column(Integer)


class TrackbackSite(db.Model):
    """Model for sites that submit trackbacks to arXiv."""

    __tablename__ = 'arXiv_trackback_sites'

    pattern = Column(String(255), nullable=False,
                     index=True, server_default=text("''"))
    site_id = Column(Integer, primary_key=True)
    action = Column(Enum('neutral', 'accept', 'reject', 'spam'),
                    nullable=False, server_default=text("'neutral'"))


def init_app(app: Optional[LocalProxy]) -> None:
    """Set configuration defaults and attach session to the application."""
    db.init_app(app)


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

        return (
            db.session.query(stmt.c.label).
            filter(stmt.c.exclusions == 0).one().label
        )
    except NoResultFound:
        return None
    except SQLAlchemyError as e:
        raise IOError('Database error: %s' % e) from e
