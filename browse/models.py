# coding: utf-8
from sqlalchemy import BINARY, BigInteger, Column, Date, DateTime, Enum, ForeignKey, ForeignKeyConstraint, Index, Integer, Numeric, SmallInteger, String, Table, Text, text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
metadata = Base.metadata


class MemberInstitution(Base):
    __tablename__ = 'Subscription_UniversalInstitution'

    resolver_URL = Column(String(255))
    name = Column(String(255), nullable=False, index=True)
    label = Column(String(255))
    id = Column(Integer, primary_key=True)
    alt_text = Column(String(255))
    link_icon = Column(String(255))
    note = Column(String(255))


class MemberInstitutionContact(Base):
    __tablename__ = 'Subscription_UniversalInstitutionContact'

    email = Column(String(255))
    sid = Column(ForeignKey('Subscription_UniversalInstitution.id', ondelete='CASCADE'), nullable=False, index=True)
    active = Column(Integer, server_default=text("'0'"))
    contact_name = Column(String(255))
    id = Column(Integer, primary_key=True)
    phone = Column(String(255))
    note = Column(String(2048))

    Subscription_UniversalInstitution = relationship('SubscriptionUniversalInstitution')


class MemberInstitutionIP(Base):
    __tablename__ = 'Subscription_UniversalInstitutionIP'
    __table_args__ = (
        Index('ip', 'start', 'end'),
    )

    sid = Column(ForeignKey('Subscription_UniversalInstitution.id', ondelete='CASCADE'), nullable=False, index=True)
    id = Column(Integer, primary_key=True)
    exclude = Column(Integer, server_default=text("'0'"))
    end = Column(BigInteger, nullable=False, index=True)
    start = Column(BigInteger, nullable=False, index=True)

    Subscription_UniversalInstitution = relationship('SubscriptionUniversalInstitution')

class SciencewisePing(Base):
    __tablename__ = 'arXiv_sciencewise_pings'

    paper_id_v = Column(String(32), primary_key=True)
    updated = Column(DateTime)

class TrackbackPing(Base):
    __tablename__ = 'arXiv_trackback_pings'

    trackback_id = Column(Integer, primary_key=True)
    document_id = Column(Integer, index=True)
    title = Column(String(255), nullable=False, server_default=text("''"))
    excerpt = Column(String(255), nullable=False, server_default=text("''"))
    url = Column(String(255), nullable=False, index=True, server_default=text("''"))
    blog_name = Column(String(255), nullable=False, server_default=text("''"))
    remote_host = Column(String(255), nullable=False, server_default=text("''"))
    remote_addr = Column(String(16), nullable=False, server_default=text("''"))
    posted_date = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    is_stale = Column(Integer, nullable=False, server_default=text("'0'"))
    approved_by_user = Column(Integer, nullable=False, server_default=text("'0'"))
    approved_time = Column(Integer, nullable=False, server_default=text("'0'"))
    status = Column(Enum('pending', 'pending2', 'accepted', 'rejected', 'spam'), nullable=False, index=True, server_default=text("'pending'"))
    site_id = Column(Integer)


class TrackbackSite(Base):
    __tablename__ = 'arXiv_trackback_sites'

    pattern = Column(String(255), nullable=False, index=True, server_default=text("''"))
    site_id = Column(Integer, primary_key=True)
    action = Column(Enum('neutral', 'accept', 'reject', 'spam'), nullable=False, server_default=text("'neutral'"))
