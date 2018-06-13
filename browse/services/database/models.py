"""arXiv browse database models."""

from typing import Optional
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import BigInteger, Column, DateTime, Enum, \
    ForeignKey, Index, Integer, SmallInteger, String, text, Text
from sqlalchemy.orm import relationship
from werkzeug.local import LocalProxy

db: SQLAlchemy = SQLAlchemy()

class ArXivDocument(db.Model):
    """Model for documents stored as part of the arXiv repository."""

    __tablename__ = 'arXiv_documents'

    document_id = Column(Integer, primary_key=True)
    paper_id = Column(String(20), nullable=False, unique=True, server_default=text("''"))
    title = Column(String(255), nullable=False, index=True, server_default=text("''"))
    authors = Column(Text)
    submitter_email = Column(String(64), nullable=False, index=True, server_default=text("''"))
    submitter_id = Column(ForeignKey('tapir_users.user_id'), index=True)
    dated = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    primary_subject_class = Column(String(16))
    created = Column(DateTime)
    submitter = relationship('TapirUser')

class ArXivLicense(db.Model):
    __tablename__ = 'arXiv_licenses'

    name = Column(String(255), primary_key=True)
    label = Column(String(255))
    active = Column(Integer, server_default=text("'1'"))
    note = Column(String(255))
    sequence = Column(Integer)


class ArXivMetadatum(db.Model):
    __tablename__ = 'arXiv_metadata'
    __table_args__ = (
        Index('pidv', 'paper_id', 'version', unique=True),
    )

    metadata_id = Column(Integer, primary_key=True)
    document_id = Column(ForeignKey('arXiv_documents.document_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True, server_default=text("'0'"))
    paper_id = Column(String(64), nullable=False)
    created = Column(DateTime)
    updated = Column(DateTime)
    submitter_id = Column(ForeignKey('tapir_users.user_id'), index=True)
    submitter_name = Column(String(64), nullable=False)
    submitter_email = Column(String(64), nullable=False)
    source_size = Column(Integer)
    source_format = Column(String(12))
    source_flags = Column(String(12))
    title = Column(Text)
    authors = Column(Text)
    abs_categories = Column(String(255))
    comments = Column(Text)
    proxy = Column(String(255))
    report_num = Column(Text)
    msc_class = Column(String(255))
    acm_class = Column(String(255))
    journal_ref = Column(Text)
    doi = Column(String(255))
    abstract = Column(Text)
    license = Column(ForeignKey('arXiv_licenses.name'), index=True)
    version = Column(Integer, nullable=False, server_default=text("'1'"))
    modtime = Column(Integer)
    is_current = Column(Integer, server_default=text("'1'"))
    is_withdrawn = Column(Integer, nullable=False, server_default=text("'0'"))

    document = relationship('ArXivDocument')
    arXiv_license = relationship('ArXivLicense')
    submitter = relationship('TapirUser')


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


class TapirUser(db.Model):
    """Legacy table that is a foreign key dependency of TapirSession."""

    __tablename__ = 'tapir_users'

    user_id = Column(Integer, primary_key=True)
    first_name = Column(String(50), index=True)
    last_name = Column(String(50), index=True)
    suffix_name = Column(String(50))
    share_first_name = Column(Integer, nullable=False, server_default=text("'1'"))
    share_last_name = Column(Integer, nullable=False, server_default=text("'1'"))
    email = Column(String(255), nullable=False, unique=True, server_default=text("''"))
    share_email = Column(Integer, nullable=False, server_default=text("'8'"))
    email_bouncing = Column(Integer, nullable=False, server_default=text("'0'"))
    policy_class = Column(
        ForeignKey('tapir_policy_classes.class_id'),
        nullable=False, index=True, server_default=text("'0'")
    )
    joined_date = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    joined_ip_num = Column(String(16), index=True)
    joined_remote_host = Column(String(255), nullable=False, server_default=text("''"))
    flag_internal = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_edit_users = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_edit_system = Column(Integer, nullable=False, server_default=text("'0'"))
    flag_email_verified = Column(Integer, nullable=False, server_default=text("'0'"))
    flag_approved = Column(Integer, nullable=False, index=True, server_default=text("'1'"))
    flag_deleted = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_banned = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_wants_email = Column(Integer, nullable=False, server_default=text("'0'"))
    flag_html_email = Column(Integer, nullable=False, server_default=text("'0'"))
    tracking_cookie = Column(String(255), nullable=False, index=True, server_default=text("''"))
    flag_allow_tex_produced = Column(Integer, nullable=False, server_default=text("'0'"))



class TapirPolicyClass(db.Model):
    """Legacy table that is a foreign key depency of TapirUse."""

    __tablename__ = 'tapir_policy_classes'

    class_id = Column(SmallInteger, primary_key=True)
    name = Column(String(64), nullable=False, server_default=text("''"))
    description = Column(Text, nullable=False)
    password_storage = Column(Integer, nullable=False, server_default=text("'0'"))
    recovery_policy = Column(Integer, nullable=False, server_default=text("'0'"))
    permanent_login = Column(Integer, nullable=False, server_default=text("'0'"))


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
