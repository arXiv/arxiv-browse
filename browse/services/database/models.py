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
    TIMESTAMP
)
from sqlalchemy.dialects.mysql import (
    TINYINT,
    INTEGER
)
from sqlalchemy.engine import make_url
from sqlalchemy.orm import relationship
from validators import url as is_valid_url
from werkzeug.local import LocalProxy

class BrowseSQLAlchemy(SQLAlchemy):
    """Overrides how flask_sqlalchemy handles options that need to be passed to
    create_engine.

    Inspite of documentation to the contrary, flask_sqlalchemy does not seem to
    be able to handle a dict as the value for a SQLALCHEMY_BINDS.
    """

    def apply_driver_hacks(self, app, sa_url, options): # type: ignore
        if not isinstance(sa_url, dict):
            return super().apply_driver_hacks(app, sa_url, options)

        url = make_url(sa_url["url"])
        options.update(sa_url)
        options.pop("url")
        return url, options



db: SQLAlchemy = BrowseSQLAlchemy()

app_config = get_application_config()
tz = gettz(app_config.get("ARXIV_BUSINESS_TZ"))
tb_secret = app_config.get("TRACKBACK_SECRET", "baz")
metadata = db.metadata


class Document(db.Model):
    """Model for documents stored as part of the arXiv repository."""

    __tablename__ = "arXiv_documents"

    document_id = Column(Integer, primary_key=True)
    paper_id = Column(
        String(20), nullable=False, unique=True, server_default=text("''")
    )
    title = Column(String(255), nullable=False,
                   index=True, server_default=text("''"))
    authors = Column(Text)
    submitter_email = Column(
        String(64), nullable=False, index=True, server_default=text("''")
    )
    submitter_id = Column(ForeignKey("tapir_users.user_id"), index=True)
    dated = Column(Integer, nullable=False, index=True,
                   server_default=text("'0'"))
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
    note = Column(String(400))
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


class User(db.Model):
    """Model for legacy user data."""

    __tablename__ = "tapir_users"

    # This handles the fact that first_name and last_name are set to utf8 in this table.
    # It sets the whole table to utf8 but hopefully that isn't a problem.
    __table_args__ = {'mysql_engine': 'InnoDB',
                      'mysql_charset': 'utf8', 'mysql_collate': 'utf8_unicode_ci'}

    # This handles the fact that first_name and last_name are set to utf8 in this table.
    # It sets the whole table to utf8 but hopefully that isn't a problem.
    __table_args__ = {'mysql_engine': 'InnoDB',
                      'mysql_charset': 'utf8', 'mysql_collate': 'utf8_unicode_ci'}

    user_id = Column(Integer, primary_key=True)
    first_name = Column(String(50), index=True)
    last_name = Column(String(50), index=True)
    suffix_name = Column(String(50))
    share_first_name = Column(Integer, nullable=False,
                              server_default=text("'1'"))
    share_last_name = Column(Integer, nullable=False,
                             server_default=text("'1'"))
    email = Column(String(255), nullable=False,
                   unique=True, server_default=text("''"))
    share_email = Column(Integer, nullable=False, server_default=text("'8'"))
    email_bouncing = Column(Integer, nullable=False,
                            server_default=text("'0'"))
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
    joined_remote_host = Column(
        String(255), nullable=False, server_default=text("''"))
    flag_internal = Column(
        Integer, nullable=False, index=True, server_default=text("'0'")
    )
    flag_edit_users = Column(
        Integer, nullable=False, index=True, server_default=text("'0'")
    )
    flag_edit_system = Column(Integer, nullable=False,
                              server_default=text("'0'"))
    flag_email_verified = Column(
        Integer, nullable=False, server_default=text("'0'"))
    flag_approved = Column(
        Integer, nullable=False, index=True, server_default=text("'1'")
    )
    flag_deleted = Column(
        Integer, nullable=False, index=True, server_default=text("'0'")
    )
    flag_banned = Column(
        Integer, nullable=False, index=True, server_default=text("'0'")
    )
    flag_wants_email = Column(Integer, nullable=False,
                              server_default=text("'0'"))
    flag_html_email = Column(Integer, nullable=False,
                             server_default=text("'0'"))
    tracking_cookie = Column(
        String(255), nullable=False, index=True, server_default=text("''")
    )
    flag_allow_tex_produced = Column(
        Integer, nullable=False, server_default=text("'0'"))
    flag_can_lock = Column(Integer,
                           nullable=False, server_default=text("'0'"))
    tapir_policy_class = relationship('UserPolicyClass')


class Nickname(db.Model):
    __tablename__ = 'tapir_nicknames'
    __table_args__ = (
        Index('user_id', 'user_id', 'user_seq', unique=True),
    )

    nick_id = Column(Integer, primary_key=True)
    nickname = Column(String(20), nullable=False,
                      unique=True, server_default=text("''"))
    user_id = Column(ForeignKey('tapir_users.user_id'),
                     nullable=False, server_default=text("'0'"))
    user_seq = Column(Integer, nullable=False, server_default=text("'0'"))
    flag_valid = Column(Integer, nullable=False, index=True,
                        server_default=text("'0'"))
    role = Column(Integer, nullable=False, index=True,
                  server_default=text("'0'"))
    policy = Column(Integer, nullable=False, index=True,
                    server_default=text("'0'"))
    flag_primary = Column(Integer, nullable=False, server_default=text("'0'"))

    user = relationship('User')


class UserPolicyClass(db.Model):
    """Model for the legacy user policy class."""

    __tablename__ = "tapir_policy_classes"

    class_id = Column(SmallInteger, primary_key=True)
    name = Column(String(64), nullable=False, server_default=text("''"))
    description = Column(Text, nullable=False)
    password_storage = Column(Integer, nullable=False,
                              server_default=text("'0'"))
    recovery_policy = Column(Integer, nullable=False,
                             server_default=text("'0'"))
    permanent_login = Column(Integer, nullable=False,
                             server_default=text("'0'"))


class TrackbackPing(db.Model):
    """Primary model for arXiv trackback data."""

    __tablename__ = "arXiv_trackback_pings"

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
    posted_date = Column(
        Integer, nullable=False, index=True, server_default=text("'0'")
    )
    is_stale = Column(Integer, nullable=False, server_default=text("'0'"))
    approved_by_user = Column(Integer, nullable=False,
                              server_default=text("'0'"))
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

    pattern = Column(String(255), nullable=False,
                     index=True, server_default=text("''"))
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


class DBLaTeXMLDocuments(db.Model):
    __bind_key__ = 'latexml'
    __tablename__ = 'arXiv_latexml_doc'

    paper_id = Column(String(20), primary_key=True)
    document_version = Column(Integer, primary_key=True)
    # conversion_status codes:
    #   - 0 = in progress
    #   - 1 = success
    #   - 2 = failure
    conversion_status = Column(Integer, nullable=False)
    tex_checksum = Column(String)
    conversion_start_time = Column(Integer)
    conversion_end_time = Column(Integer)


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
    papers_to_endorse = Column(
        SmallInteger, nullable=False, server_default=text("'0'"))
    endorsement_domain = Column(
        ForeignKey("arXiv_endorsement_domains.endorsement_domain"), index=True
    )

    arXiv_archive = relationship("Archive")
    arXiv_endorsement_domain = relationship("EndorsementDomain")


class Archive(db.Model):
    """Model for archive in taxonomy."""

    __tablename__ = "arXiv_archives"

    archive_id = Column(String(16), primary_key=True,
                        server_default=text("''"))
    in_group = Column(
        ForeignKey("arXiv_groups.group_id"),
        nullable=False,
        index=True,
        server_default=text("''"),
    )
    archive_name = Column(String(255), nullable=False,
                          server_default=text("''"))
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

    endorsement_domain = Column(
        String(32), primary_key=True, server_default=text("''"))
    endorse_all = Column(Enum("y", "n"), nullable=False,
                         server_default=text("'n'"))
    mods_endorse_all = Column(
        Enum("y", "n"), nullable=False, server_default=text("'n'")
    )
    endorse_email = Column(Enum("y", "n"), nullable=False,
                           server_default=text("'y'"))
    papers_to_endorse = Column(
        SmallInteger, nullable=False, server_default=text("'4'"))


class AuthorIds(db.Model):
    __tablename__ = 'arXiv_author_ids'

    user_id = Column(ForeignKey('tapir_users.user_id'), primary_key=True)
    author_id = Column(String(50), nullable=False, index=True)
    updated = Column(DateTime, nullable=False,
                     server_default=text("CURRENT_TIMESTAMP"))

    user = relationship('User', uselist=False)


class OrcidIds(db.Model):
    __tablename__ = 'arXiv_orcid_ids'

    user_id = Column(ForeignKey('tapir_users.user_id'), primary_key=True)
    orcid = Column(String(19), nullable=False, index=True)
    authenticated = Column(Integer, nullable=False, server_default=text("'0'"))
    updated = Column(DateTime, nullable=False,
                     server_default=text("CURRENT_TIMESTAMP"))

    user = relationship('User', uselist=False)


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
    Column("subject_class", String(16),
           nullable=False, server_default=text("''")),
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

    ym = Column(Date, primary_key=True
                # ,server_default=text("'0000-00-00'") # does not work in sqlite
                )
    num_submissions = Column(SmallInteger, nullable=False)
    historical_delta = Column(Integer, nullable=False,
                              server_default=text("'0'"))


stats_hourly = Table(
    "arXiv_stats_hourly",
    metadata,
    Column("ymd", Date, nullable=False, index=True),
    Column("hour", Integer, nullable=False, index=True),
    Column("node_num", Integer, nullable=False, index=True),
    Column("access_type", String(1), nullable=False, index=True),
    Column("connections", Integer, nullable=False),
)

paper_owners = Table(
    'arXiv_paper_owners',
    metadata,
    Column('document_id', ForeignKey('arXiv_documents.document_id'),
           nullable=False, server_default=text("'0'")),
    Column('user_id', ForeignKey('tapir_users.user_id'),
           nullable=False, index=True, server_default=text("'0'")),
    Column('date', INTEGER(10), nullable=False, server_default=text("'0'")),
    Column('added_by', ForeignKey('tapir_users.user_id'),
           nullable=False, index=True, server_default=text("'0'")),
    Column('remote_addr', String(16), nullable=False,
           server_default=text("''")),
    Column('remote_host', String(255),
           nullable=False, server_default=text("''")),
    Column('tracking_cookie', String(32),
           nullable=False, server_default=text("''")),
    Column('valid', INTEGER(1), nullable=False, server_default=text("'0'")),
    Column('flag_author', INTEGER(1), nullable=False,
           server_default=text("'0'")),
    Column('flag_auto', INTEGER(1), nullable=False, server_default=text("'1'")),
    Index('document_id', 'document_id', 'user_id', unique=True)
)


class CategoryDef(db.Model):
    __tablename__ = 'arXiv_category_def'
    __table_args__ = (
        ForeignKeyConstraint(['archive', 'subject_class'], [
                             'arXiv_categories.archive', 'arXiv_categories.subject_class']),
        Index('cat_def_fk', 'archive', 'subject_class')
    )

    category = Column(String(32), primary_key=True)
    name = Column(String(255))
    active = Column(Integer, server_default=text("'1'"))
    archive = Column(String(16), nullable=False, server_default=text("''"))
    subject_class = Column(String(16), nullable=False,
                           server_default=text("''"))

    arXiv_categories = relationship('Category')


class DocumentCategory(db.Model):
    __tablename__ = 'arXiv_document_category'

    document_id = Column(ForeignKey('arXiv_documents.document_id', ondelete='CASCADE'),
                         primary_key=True, nullable=False, index=True,
                         server_default=text("'0'"))
    category = Column(ForeignKey('arXiv_category_def.category'), primary_key=True,
                      nullable=False, index=True)
    is_primary = Column(Integer, nullable=False, server_default=text("'0'"))

    document = relationship('Document')


class NextMail(db.Model):
    """Model for mailings from publish"""
    __tablename__ = 'arXiv_next_mail'
    __table_args__ = (
        Index('arXiv_next_mail_idx_document_id_version',
              'document_id', 'version'),
    )
    next_mail_id = Column(Integer, primary_key=True)
    submission_id = Column(Integer, nullable=False)
    document_id = Column(Integer, nullable=False,
                         index=True, server_default=text("'0'"))
    paper_id = Column(String(20))
    version = Column(Integer, nullable=False, server_default=text("'1'"))
    type = Column(String(255), nullable=False, server_default=text("'new'"))
    extra = Column(String(255))
    mail_id = Column(String(6))
    is_written = Column(Integer, nullable=False, server_default=text("'0'"))


class AdminLog(db.Model):
    __tablename__ = 'arXiv_admin_log'

    id = Column(Integer(), primary_key=True)
    logtime = Column(String(24))
    created = Column(DateTime, nullable=False,
                     # Only works on mysql:
                     # server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
                     )
    paper_id = Column(String(20), index=True)
    username = Column(String(20), index=True)
    host = Column(String(64))
    program = Column(String(20))
    command = Column(String(20), index=True)
    logtext = Column(Text)
    document_id = Column(Integer())
    submission_id = Column(Integer(), index=True)
    notify = Column(Integer(), server_default=text("'0'"))


def init_app(app: Optional[LocalProxy]) -> None:
    """Set configuration defaults and attach session to the application."""
    if app is None:
        raise RuntimeError("Cannot init a app of None")

    _config_latexml(app)
    db.init_app(app)


def _config_latexml(app: LocalProxy) -> None:
    """Set up the latexml database.

    This will detech if LATEXML_INSTANCE_CONNECTION_NAME is set and if it is,
    it will use a GCP connector with TLS."""
    config = app.config  # type: ignore
    if not config["LATEXML_ENABLED"]:
        return

    if "SQLALCHEMY_BINDS" in config and config["SQLALCHEMY_BINDS"]:
        return  # already set?

    if config["LATEXML_INSTANCE_CONNECTION_NAME"]:
        from google.cloud.sql.connector import Connector, IPTypes
        import pg8000

        ip_type = IPTypes.PRIVATE if config["LATEXML_IP_TYPE"] == "PRIVATE_IP"\
            else IPTypes.PUBLIC
        connector = Connector()

        def getconn() -> pg8000.dbapi.Connection:
            conn: pg8000.dbapi.Connection = connector.connect(
                config["LATEXML_INSTANCE_CONNECTION_NAME"],
                "pg8000",
                user=config["LATEXML_DB_USER"],
                password=config["LATEXML_DB_PASS"],
                db=config["LATEXML_DB_NAME"],
                ip_type=ip_type,
            )
            return conn


        bind = {
            #"url": make_url("postgresql+pg8000://"),
            "url": "postgresql+pg8000://",
            "creator": getconn}

        config["SQLALCHEMY_BINDS"]["latexml"] = bind
    elif config["LATEXML_DB_USER"] and config["LATEXML_DB_PASS"] and config["LATEXML_DB_NAME"]:
        user = config["LATEXML_DB_USER"]
        pw = config["LATEXML_DB_PASS"]
        db = config["LATEXML_DB_NAME"]
        config["SQLALCHEMY_BINDS"]["latexml"] = {"url": f"postgresql+pg8000://{user}@{pw}/{db}"}

