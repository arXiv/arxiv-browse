"""arXiv browse database models."""

import hashlib
import re
from datetime import datetime
from typing import Optional

from arxiv.base.globals import get_application_config
from dateutil.tz import gettz, tzutc
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    SmallInteger,
    String,
    Table,
    Text,
    text,
)
from sqlalchemy.orm import relationship
from validators import url as is_valid_url
from werkzeug.local import LocalProxy


db: SQLAlchemy = SQLAlchemy()

app_config = get_application_config()
tz = gettz(app_config.get("ARXIV_BUSINESS_TZ", "US/Eastern"))
tb_secret = app_config.get("TRACKBACK_SECRET", "baz")
metadata = db.metadata


class Document(db.Model):
    """Model for documents stored as part of the arXiv repository."""

    __tablename__ = "arXiv_documents"

    document_id = Column(Integer, primary_key=True)
    paper_id = Column(
        String(20), nullable=False, unique=True, server_default=text("''")
    )
    title = Column(String(255), nullable=False, index=True, server_default=text("''"))
    authors = Column(Text)
    submitter_email = Column(
        String(64), nullable=False, index=True, server_default=text("''")
    )
    submitter_id = Column(ForeignKey("tapir_users.user_id"), index=True)
    dated = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    primary_subject_class = Column(String(16))
    created = Column(DateTime)
    submitter = relationship("User")

    trackback_ping = relationship(
        "TrackbackPing",
        primaryjoin="foreign(TrackbackPing.document_id)==Document.document_id",
    )


class License(db.Model):
    """Model for arXiv licenses."""

    __tablename__ = "arXiv_licenses"

    name = Column(String(255), primary_key=True)
    label = Column(String(255))
    active = Column(Integer, server_default=text("'1'"))
    note = Column(String(255))
    sequence = Column(Integer)


class Metadata(db.Model):
    """Model for arXiv document metadata."""

    __tablename__ = "arXiv_metadata"
    __table_args__ = (Index("pidv", "paper_id", "version", unique=True),)

    metadata_id = Column(Integer, primary_key=True)
    document_id = Column(
        ForeignKey(
            "arXiv_documents.document_id", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
        index=True,
        server_default=text("'0'"),
    )
    paper_id = Column(String(64), nullable=False)
    created = Column(DateTime)
    updated = Column(DateTime)
    submitter_id = Column(ForeignKey("tapir_users.user_id"), index=True)
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
    license = Column(ForeignKey("arXiv_licenses.name"), index=True)
    version = Column(Integer, nullable=False, server_default=text("'1'"))
    modtime = Column(Integer)
    is_current = Column(Integer, server_default=text("'1'"))
    is_withdrawn = Column(Integer, nullable=False, server_default=text("'0'"))

    document = relationship("Document")
    arXiv_license = relationship("License")
    submitter = relationship("User")


class DataciteDois(db.Model):
    """Model for arXiv DataCite DOIs."""

    __tablename__ = "arXiv_datacite_dois"
    __table_args__ = (Index("account", "account", "paper_id"),)

    doi = Column(String(255), primary_key=True)
    account = Column(Enum("test", "prod"))
    metadata_id = Column(
        ForeignKey("arXiv_metadata.metadata_id"), nullable=False, index=True
    )
    paper_id = Column(String(64), nullable=False, unique=True)
    created = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    metadata_ = relationship("Metadata")


class MemberInstitution(db.Model):
    """Primary model for arXiv member insitution data."""

    __tablename__ = "Subscription_UniversalInstitution"

    resolver_URL = Column(String(255))
    name = Column(String(255), nullable=False, index=True)
    label = Column(String(255))
    id = Column(Integer, primary_key=True)
    alt_text = Column(String(255))
    link_icon = Column(String(255))
    note = Column(String(255))


class MemberInstitutionContact(db.Model):
    """Model for arXiv member institution contact information."""

    __tablename__ = "Subscription_UniversalInstitutionContact"

    email = Column(String(255))
    sid = Column(
        ForeignKey("Subscription_UniversalInstitution.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    active = Column(Integer, server_default=text("'0'"))
    contact_name = Column(String(255))
    id = Column(Integer, primary_key=True)
    phone = Column(String(255))
    note = Column(String(2048))

    Subscription_UniversalInstitution = relationship("MemberInstitution")


class MemberInstitutionIP(db.Model):
    """Model for arXiv member insitution IP address ranges and exclusions."""

    __tablename__ = "Subscription_UniversalInstitutionIP"
    __table_args__ = (Index("ip", "start", "end"),)

    sid = Column(
        ForeignKey("Subscription_UniversalInstitution.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    id = Column(Integer, primary_key=True)
    exclude = Column(Integer, server_default=text("'0'"))
    end = Column(BigInteger, nullable=False, index=True)
    start = Column(BigInteger, nullable=False, index=True)

    Subscription_UniversalInstitution = relationship("MemberInstitution")


class SciencewisePing(db.Model):
    """Model for ScienceWISE (trackback) pings."""

    __tablename__ = "arXiv_sciencewise_pings"

    paper_id_v = Column(String(32), primary_key=True)
    updated = Column(DateTime)


class User(db.Model):
    """Model for legacy user data."""

    __tablename__ = "tapir_users"

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
        ForeignKey("tapir_policy_classes.class_id"),
        nullable=False,
        index=True,
        server_default=text("'0'"),
    )
    joined_date = Column(
        Integer, nullable=False, index=True, server_default=text("'0'")
    )
    joined_ip_num = Column(String(16), index=True)
    joined_remote_host = Column(String(255), nullable=False, server_default=text("''"))
    flag_internal = Column(
        Integer, nullable=False, index=True, server_default=text("'0'")
    )
    flag_edit_users = Column(
        Integer, nullable=False, index=True, server_default=text("'0'")
    )
    flag_edit_system = Column(Integer, nullable=False, server_default=text("'0'"))
    flag_email_verified = Column(Integer, nullable=False, server_default=text("'0'"))
    flag_approved = Column(
        Integer, nullable=False, index=True, server_default=text("'1'")
    )
    flag_deleted = Column(
        Integer, nullable=False, index=True, server_default=text("'0'")
    )
    flag_banned = Column(
        Integer, nullable=False, index=True, server_default=text("'0'")
    )
    flag_wants_email = Column(Integer, nullable=False, server_default=text("'0'"))
    flag_html_email = Column(Integer, nullable=False, server_default=text("'0'"))
    tracking_cookie = Column(
        String(255), nullable=False, index=True, server_default=text("''")
    )
    flag_allow_tex_produced = Column(
        Integer, nullable=False, server_default=text("'0'")
    )

    tapir_policy_class = relationship("UserPolicyClass")


class UserPolicyClass(db.Model):
    """Model for the legacy user policy class."""

    __tablename__ = "tapir_policy_classes"

    class_id = Column(SmallInteger, primary_key=True)
    name = Column(String(64), nullable=False, server_default=text("''"))
    description = Column(Text, nullable=False)
    password_storage = Column(Integer, nullable=False, server_default=text("'0'"))
    recovery_policy = Column(Integer, nullable=False, server_default=text("'0'"))
    permanent_login = Column(Integer, nullable=False, server_default=text("'0'"))


class TrackbackPing(db.Model):
    """Primary model for arXiv trackback data."""

    __tablename__ = "arXiv_trackback_pings"

    trackback_id = Column(Integer, primary_key=True)
    document_id = Column(Integer, index=True)
    title = Column(String(255), nullable=False, server_default=text("''"))
    excerpt = Column(String(255), nullable=False, server_default=text("''"))
    url = Column(String(255), nullable=False, index=True, server_default=text("''"))
    blog_name = Column(String(255), nullable=False, server_default=text("''"))
    remote_host = Column(String(255), nullable=False, server_default=text("''"))
    remote_addr = Column(String(16), nullable=False, server_default=text("''"))
    posted_date = Column(
        Integer, nullable=False, index=True, server_default=text("'0'")
    )
    is_stale = Column(Integer, nullable=False, server_default=text("'0'"))
    approved_by_user = Column(Integer, nullable=False, server_default=text("'0'"))
    approved_time = Column(Integer, nullable=False, server_default=text("'0'"))
    status = Column(
        Enum("pending", "pending2", "accepted", "rejected", "spam"),
        nullable=False,
        index=True,
        server_default=text("'pending'"),
    )
    site_id = Column(Integer)

    document = relationship(
        "Document",
        primaryjoin="foreign(Document.document_id)==TrackbackPing.document_id",
    )

    @property
    def posted_datetime(self) -> DateTime:
        """Get posted_date as UTC datetime."""
        dt = datetime.fromtimestamp(self.posted_date, tz=tz)
        return dt.astimezone(tz=tzutc())

    @property
    def display_url(self) -> str:
        """Get the URL without the protocol, for display."""
        return str(re.sub(r"^[a-z]+:\/\/", "", self.url.strip(), flags=re.IGNORECASE,))

    @property
    def has_valid_url(self) -> bool:
        """Determine whether the trackback URL is valid."""
        return bool(is_valid_url(self.url, public=False))

    @property
    def hashed_document_id(self) -> str:
        """Get the hashed document_id."""
        s = f"{self.document_id}{self.trackback_id}{tb_secret}"
        return hashlib.md5(s.encode()).hexdigest()[0:9]


class TrackbackSite(db.Model):
    """Model for sites that submit trackbacks to arXiv."""

    __tablename__ = "arXiv_trackback_sites"

    pattern = Column(String(255), nullable=False, index=True, server_default=text("''"))
    site_id = Column(Integer, primary_key=True)
    action = Column(
        Enum("neutral", "accept", "reject", "spam"),
        nullable=False,
        server_default=text("'neutral'"),
    )


class DBLP(db.Model):
    """Primary model for the DBLP Computer Science Bibliography data."""

    __tablename__ = "arXiv_dblp"

    document_id = Column(
        ForeignKey("arXiv_documents.document_id"),
        primary_key=True,
        server_default=text("'0'"),
    )
    url = Column(String(80))


class DBLPAuthor(db.Model):
    """Model for DBLP author name."""

    __tablename__ = "arXiv_dblp_authors"

    author_id = Column(Integer, primary_key=True, unique=True)
    name = Column(String(40), unique=True)


class DBLPDocumentAuthor(db.Model):
    """Model for the DBLP document to author mapping with ordering."""

    __tablename__ = "arXiv_dblp_document_authors"

    document_id = Column(
        ForeignKey("arXiv_documents.document_id"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    author_id = Column(
        ForeignKey("arXiv_dblp_authors.author_id"),
        primary_key=True,
        nullable=False,
        index=True,
        server_default=text("'0'"),
    )
    position = Column(Integer, nullable=False, server_default=text("'0'"))

    author = relationship("DBLPAuthor")
    document = relationship("Document")


class Category(db.Model):
    """Model for category in taxonomy."""

    __tablename__ = "arXiv_categories"

    archive = Column(
        ForeignKey("arXiv_archives.archive_id"),
        primary_key=True,
        nullable=False,
        server_default=text("''"),
    )
    subject_class = Column(
        String(16), primary_key=True, nullable=False, server_default=text("''")
    )
    definitive = Column(Integer, nullable=False, server_default=text("'0'"))
    active = Column(Integer, nullable=False, server_default=text("'0'"))
    category_name = Column(String(255))
    endorse_all = Column(
        Enum("y", "n", "d"), nullable=False, server_default=text("'d'")
    )
    endorse_email = Column(
        Enum("y", "n", "d"), nullable=False, server_default=text("'d'")
    )
    papers_to_endorse = Column(SmallInteger, nullable=False, server_default=text("'0'"))
    endorsement_domain = Column(
        ForeignKey("arXiv_endorsement_domains.endorsement_domain"), index=True
    )

    arXiv_archive = relationship("Archive")
    arXiv_endorsement_domain = relationship("EndorsementDomain")


class Archive(db.Model):
    """Model for archive in taxonomy."""

    __tablename__ = "arXiv_archives"

    archive_id = Column(String(16), primary_key=True, server_default=text("''"))
    in_group = Column(
        ForeignKey("arXiv_groups.group_id"),
        nullable=False,
        index=True,
        server_default=text("''"),
    )
    archive_name = Column(String(255), nullable=False, server_default=text("''"))
    start_date = Column(String(4), nullable=False, server_default=text("''"))
    end_date = Column(String(4), nullable=False, server_default=text("''"))
    subdivided = Column(Integer, nullable=False, server_default=text("'0'"))

    arXiv_group = relationship("Group")


class Group(db.Model):
    """Model for group in taxonomy."""

    __tablename__ = "arXiv_groups"

    group_id = Column(String(16), primary_key=True, server_default=text("''"))
    group_name = Column(String(255), nullable=False, server_default=text("''"))
    start_year = Column(String(4), nullable=False, server_default=text("''"))


class EndorsementDomain(db.Model):
    """Model for endorsement domain."""

    __tablename__ = "arXiv_endorsement_domains"

    endorsement_domain = Column(String(32), primary_key=True, server_default=text("''"))
    endorse_all = Column(Enum("y", "n"), nullable=False, server_default=text("'n'"))
    mods_endorse_all = Column(
        Enum("y", "n"), nullable=False, server_default=text("'n'")
    )
    endorse_email = Column(Enum("y", "n"), nullable=False, server_default=text("'y'"))
    papers_to_endorse = Column(SmallInteger, nullable=False, server_default=text("'4'"))


in_category = Table(
    "arXiv_in_category",
    metadata,
    Column(
        "document_id",
        ForeignKey("arXiv_documents.document_id"),
        nullable=False,
        index=True,
        server_default=text("'0'"),
    ),
    Column("archive", String(16), nullable=False, server_default=text("''")),
    Column("subject_class", String(16), nullable=False, server_default=text("''")),
    Column("is_primary", Integer, nullable=False, server_default=text("'0'")),
    ForeignKeyConstraint(
        ["archive", "subject_class"],
        ["arXiv_categories.archive", "arXiv_categories.subject_class"],
    ),
    Index("archive", "archive", "subject_class", "document_id", unique=True),
    Index("arXiv_in_category_mp", "archive", "subject_class"),
)


class StatsMonthlyDownload(db.Model):
    """Model for monthly article download statistics."""

    __tablename__ = "arXiv_stats_monthly_downloads"

    ym = Column(Date, primary_key=True)
    downloads = Column(Integer, nullable=False)


class StatsMonthlySubmission(db.Model):
    """Model for monthly submission statistics."""

    __tablename__ = "arXiv_stats_monthly_submissions"

    ym = Column(Date, primary_key=True, server_default=text("'0000-00-00'"))
    num_submissions = Column(SmallInteger, nullable=False)
    historical_delta = Column(Integer, nullable=False, server_default=text("'0'"))


stats_hourly = Table(
    "arXiv_stats_hourly",
    metadata,
    Column("ymd", Date, nullable=False, index=True),
    Column("hour", Integer, nullable=False, index=True),
    Column("node_num", Integer, nullable=False, index=True),
    Column("access_type", String(1), nullable=False, index=True),
    Column("connections", Integer, nullable=False),
)


def init_app(app: Optional[LocalProxy]) -> None:
    """Set configuration defaults and attach session to the application."""
    db.init_app(app)
