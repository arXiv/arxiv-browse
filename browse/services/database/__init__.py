"""Import db instance and define utility functions."""
# pylint disable=no-member

import ipaddress
from datetime import date, datetime
from typing import Any, Callable, List, Mapping, Optional, Tuple

from flask import current_app

from arxiv.base.globals import get_application_config
from dateutil.tz import gettz, tzutc
from sqlalchemy import asc, desc, not_, case, distinct, or_
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.orm import Query
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import func
from sqlalchemy.engine import Row

from browse.domain.identifier import Identifier
from browse.services.listing import MonthTotal, YearCount
from browse.services.database.models import (
    DBLP,
    DBLPAuthor,
    DBLPDocumentAuthor,
    DataciteDois,
    Document,
    MemberInstitution,
    MemberInstitutionIP,
    StatsMonthlyDownload,
    StatsMonthlySubmission,
    TrackbackPing,
    DBLaTeXMLDocuments,
    OrcidIds,
    AuthorIds,
    User,
    db,
    in_category,
    stats_hourly,
    paper_owners,
    Metadata
)
from browse.domain.identifier import Identifier
from browse.services.listing import ListingItem
from arxiv.base import logging
from logging import Logger

logger = logging.getLogger(__name__)
app_config = get_application_config()
tz = gettz(app_config.get("ARXIV_BUSINESS_TZ"))


def db_handle_error(db_logger: Logger, default_return_val: Any) -> Any:
    """Handle operational database errors via decorator."""

    def decorator(func_to_wrap: Callable) -> Any:
        def wrapper(*args, **kwargs):  # type: ignore
            # Bypass attempt to perform query and just return default value
            is_db_disabled: bool = app_config.get("BROWSE_DISABLE_DATABASE") or False
            if is_db_disabled:
                if db_logger:
                    db_logger.info("Database is disabled per BROWSE_DISABLE_DATABASE")
                return default_return_val
            try:
                return func_to_wrap(*args, **kwargs)
            except NoResultFound:
                return default_return_val
            except (OperationalError, DBAPIError) as ex:
                if db_logger:
                    db_logger.warning(f"Error executing query in {func_to_wrap.__name__}: {ex}")
                return default_return_val
            except Exception as ex:
                if db_logger:
                    db_logger.warning(f"Unknown exception in {func_to_wrap.__name__}: {ex}")
                raise

        return wrapper

    return decorator


def __all_trackbacks_query() -> Query:
    return db.session.query(TrackbackPing)


def __paper_trackbacks_query(paper_id: str) -> Query:
    return (
        __all_trackbacks_query()
        .filter(TrackbackPing.document_id == Document.document_id)
        .filter(Document.paper_id == paper_id)
        .filter(TrackbackPing.status == "accepted")
    )

@db_handle_error(db_logger=logger, default_return_val=None)
def get_institution(ip: str) -> Optional[Mapping[str, str]]:
    """Get institution label from IP address."""
    decimal_ip = int(ipaddress.ip_address(ip))

    stmt = (
        db.session.query(
            MemberInstitution.id,
            MemberInstitution.label,
            func.sum(MemberInstitutionIP.exclude).label("exclusions"),
        )
        .join(MemberInstitutionIP)
        .filter(
            MemberInstitutionIP.start <= decimal_ip,
            MemberInstitutionIP.end >= decimal_ip,
        )
        .group_by(MemberInstitution.id, MemberInstitution.label,)
        .subquery()
    )
    institution_row = (
        db.session.query(stmt.c.id, stmt.c.label).filter(stmt.c.exclusions == 0).first()
    )

    h = None
    if institution_row:
        h = {
            "id": institution_row.id,
            "label": institution_row.label,
            "ip" : ip,
        }
    return h


# Only used in tests
@db_handle_error(db_logger=logger, default_return_val=[])
def get_all_trackback_pings() -> List[TrackbackPing]:
    """Get all trackback pings in database."""
    return list(__all_trackbacks_query().all())


# Used only on trackback page
@db_handle_error(db_logger=logger, default_return_val=[])
def get_paper_trackback_pings(paper_id: str) -> List[TrackbackPing]:
    """Get trackback pings for a particular document (paper_id)."""
    return list(
        __paper_trackbacks_query(paper_id)
        .distinct(TrackbackPing.url)
        .group_by(TrackbackPing.url)
        .order_by(TrackbackPing.posted_date.desc())
        .all()
    )

# Used on tb page and abs page
@db_handle_error(db_logger=logger, default_return_val=None)
def get_trackback_ping(trackback_id: int) -> Optional[TrackbackPing]:
    """Get an individual trackback ping by its id (trackback_id)."""
    trackback: TrackbackPing = db.session.query(TrackbackPing).filter(
        TrackbackPing.trackback_id == trackback_id
    ).first()
    return trackback


# Used only on tb page
@db_handle_error(db_logger=logger, default_return_val=list())
def get_recent_trackback_pings(max_trackbacks: int = 25) \
        -> List[Tuple[TrackbackPing, str, str]]:
    """Get recent trackback pings across all of arXiv."""
    max_trackbacks = min(max(max_trackbacks, 0), 500)
    if max_trackbacks == 0:
        return []

    # subquery to get the specified number of distinct trackback URLs
    stmt = (
        db.session.query(TrackbackPing.url)
        .filter(TrackbackPing.status == "accepted")
        .distinct(TrackbackPing.url)
        .group_by(TrackbackPing.url)
        .order_by(TrackbackPing.posted_date.desc())
        .limit(max_trackbacks)
        .subquery()
    )
    tb_doc_tup = (
        db.session.query(TrackbackPing, Document.paper_id, Document.title)
        .join(Document, TrackbackPing.document_id == Document.document_id)
        .filter(TrackbackPing.status == "accepted")
        .filter(TrackbackPing.url == stmt.c.url)
        .order_by(TrackbackPing.posted_date.desc())
        .all()
    )

    return list(tb_doc_tup)


#Used on abs page
@db_handle_error(db_logger=logger, default_return_val=None)
def get_trackback_ping_latest_date(paper_id: str) -> Optional[datetime]:
    """Get the most recent accepted trackback datetime for a paper_id."""
    timestamp: int = db.session.query(func.max(TrackbackPing.approved_time)).filter(
        TrackbackPing.document_id == Document.document_id
    ).filter(Document.paper_id == paper_id).filter(
        TrackbackPing.status == "accepted"
    ).scalar()
    dt = datetime.fromtimestamp(timestamp, tz=tz)
    dt = dt.astimezone(tz=tzutc())
    return dt


# used on abs page
@db_handle_error(db_logger=logger, default_return_val=0)
def count_trackback_pings(paper_id: str) -> int:
    """Count trackback pings for a particular document (paper_id)."""
    row = (
        db.session.query(
            func.count(func.distinct(TrackbackPing.url)).label("num_pings")
        )
        .filter(TrackbackPing.document_id == Document.document_id)
        .filter(Document.paper_id == paper_id)
        .filter(TrackbackPing.status == "accepted")
        .first()
    )

    return int(row.num_pings)


#Not used, only in tests
@db_handle_error(db_logger=logger, default_return_val=0)
def count_all_trackback_pings() -> int:
    """Count trackback pings for all documents, without DISTINCT(URL)."""
    c = __all_trackbacks_query().count()
    assert isinstance(c, int)
    return c


# used in abs page
@db_handle_error(db_logger=logger, default_return_val=None)
def get_dblp_listing_path(paper_id: str) -> Optional[str]:
    """Get the DBLP Bibliography URL for a given document (paper_id)."""
    url: str = db.session.query(DBLP.url).join(Document).filter(
        Document.paper_id == paper_id
    ).one().url
    return url


# used in abs page
@db_handle_error(db_logger=logger, default_return_val=[])
def get_dblp_authors(paper_id: str) -> List[str]:
    """Get sorted list of DBLP authors for a given document (paper_id)."""
    authors_t = (
        db.session.query(DBLPAuthor.name)
        .join(DBLPDocumentAuthor)
        .join(Document)
        .filter(Document.paper_id == paper_id)
        .order_by(DBLPDocumentAuthor.position)
        .all()
    )
    authors = [a for (a,) in authors_t]
    return authors

# Used on home page and stats page
@db_handle_error(db_logger=logger, default_return_val=None)
def get_document_count() -> Optional[int]:
    """Get the number of documents."""
    # func.count is used here because .count() forces a subquery which
    # is inefficient
    row = (
        db.session.query(func.count(Document.document_id).label("num_documents"))
        .filter(not_(Document.paper_id.like("test%")))
        .first()
    )
    return int(row.num_documents)


# Used on stats page
@db_handle_error(db_logger=logger, default_return_val=0)
def get_document_count_by_yymm(paper_date: Optional[date] = None) -> int:
    """Get number of papers for a given year and month."""
    paper_date = date.today() if not isinstance(paper_date, date) else paper_date
    yymm = paper_date.strftime("%y%m")
    yymm_like = f"{yymm}%"
    if paper_date < date(2007, 4, 1):
        yymm_like = f"%/{yymm}%"
    row = (
        db.session.query(func.count(Document.document_id).label("num_documents"))
        .filter(Document.paper_id.like(yymm_like))
        .filter(not_(Document.paper_id.like("test%")))
        .first()
    )
    return int(row.num_documents)


# Only used on prevnext page
@db_handle_error(db_logger=logger, default_return_val=None)
def get_sequential_id(paper_id: Identifier,
                      context: str = 'all',
                      is_next: bool = True) -> Optional[str]:
    """Get the next or previous paper ID in sequence."""
    if not isinstance(paper_id, Identifier) or not paper_id.month or not paper_id.year:
        return None

    # In case we go over month or year boundry
    inc = 1 if is_next else -1
    nxtmonth = int(paper_id.month) + inc
    if nxtmonth > 12 or nxtmonth < 1:
        nxyear = int(paper_id.year) + inc
        nxtmonth = 1 if is_next else 12
    else:
        nxyear = paper_id.year

    nextyymm = "{}{:02d}".format(str(nxyear)[2:], nxtmonth)

    query = db.session.query(Document.paper_id)
    if paper_id.is_old_id:
        # NB: classic did not support old identifiers in prevnext
        if context == "all":
            like_id = f"{paper_id.archive}/{paper_id.yymm}%"
            next_q = f"{paper_id.archive}/{nextyymm}%"
        else:
            like_id = f"%/{paper_id.yymm}%"
            next_q = f"%/{nextyymm}%"
    else:
        like_id = f"{paper_id.yymm}.%"
        next_q = f"{nextyymm}.%"

    query = query.filter(
        (Document.paper_id.like(like_id) | Document.paper_id.like(next_q))
    )

    if is_next:
        query = query.filter(Document.paper_id > paper_id.id).order_by(
            asc(Document.paper_id)
        )
    else:
        query = query.filter(Document.paper_id < paper_id.id).order_by(
            desc(Document.paper_id)
        )
    if context != "all":
        archive: str = context
        subject_class: str = ""
        if "." in archive:
            (archive, subject_class) = archive.split(".", 1)
        query = query.join(in_category).filter(in_category.c.archive == archive)
        if subject_class:
            query = query.filter(in_category.c.subject_class == subject_class)

    result = query.first()
    if result:
        return f"{result.paper_id}"
    return None


def __all_hourly_stats_query() -> Query:
    return db.session.query(stats_hourly)



# Used on stats page
@db_handle_error(db_logger=logger, default_return_val=(0, 0, 0))
def get_hourly_stats_count(stats_date: Optional[date]) -> Tuple[int, int, int]:
    """Get sum of normal/admin connections and nodes for a given date."""
    stats_date = date.today() if not isinstance(stats_date, date) else stats_date
    normal_count = 0
    admin_count = 0
    num_nodes = 0
    rows = (
        db.session.query(
            func.sum(stats_hourly.c.connections).label("num_connections"),
            stats_hourly.c.access_type,
            func.max(stats_hourly.c.node_num).label("num_nodes"),
        )
        .filter(stats_hourly.c.ymd == stats_date.isoformat())
        .group_by(stats_hourly.c.access_type)
        .all()
    )
    for r in rows:
        if r.access_type == "A":
            admin_count = r.num_connections
        else:
            normal_count = r.num_connections
            num_nodes = r.num_nodes
    return (normal_count, admin_count, num_nodes)


# Used on stats page
# maybe on /today page?
@db_handle_error(db_logger=logger, default_return_val=[])
def get_hourly_stats(stats_date: Optional[date] = None) -> List:
    """Get the hourly stats for a given date."""
    stats_date = date.today() if not isinstance(stats_date, date) else stats_date

    return list(
        __all_hourly_stats_query()
        .filter(
            stats_hourly.c.access_type == "N",
            stats_hourly.c.ymd == stats_date.isoformat(),
        )
        .order_by(asc(stats_hourly.c.hour), stats_hourly.c.node_num)
        .all()
    )


# Used on stats page
@db_handle_error(db_logger=logger, default_return_val=[])
def get_monthly_submission_stats() -> List:
    """Get monthly submission stats from :class:`.StatsMonthlySubmission`."""
    return list(
        db.session.query(StatsMonthlySubmission)
        .order_by(asc(StatsMonthlySubmission.ym))
        .all()
    )

# Used on stats page
@db_handle_error(db_logger=logger, default_return_val=(0, 0))
def get_monthly_submission_count() -> Tuple[int, int]:
    """Get submission totals: number of submissions and number migrated."""
    row = db.session.query(
        func.sum(StatsMonthlySubmission.num_submissions).label("num_submissions"),
        func.sum(StatsMonthlySubmission.historical_delta).label("num_migrated"),
    ).first()
    return (row.num_submissions, row.num_migrated)


# Used on stats page
@db_handle_error(db_logger=logger, default_return_val=[])
def get_monthly_download_stats() -> List:
    """Get all the monthly download stats."""
    return list(
        db.session.query(StatsMonthlyDownload)
        .order_by(asc(StatsMonthlyDownload.ym))
        .all()
    )

# Used on stats page
@db_handle_error(db_logger=logger, default_return_val=0)
def get_monthly_download_count() -> int:
    """Get the sum of monthly downloads for all time."""
    row = db.session.query(
        func.sum(StatsMonthlyDownload.downloads).label("total_downloads")
    ).first()
    total_downloads: int = row.total_downloads if row else 0
    return total_downloads


# Used on stats page
@db_handle_error(db_logger=logger, default_return_val=None)
def get_max_download_stats_dt() -> Optional[datetime]:
    """Get the datetime of the most recent download stats."""
    row = db.session.query(func.max(StatsMonthlyDownload.ym).label("max_ym")).first()
    return row.max_ym if row else None


@db_handle_error(db_logger=logger, default_return_val=None)
def get_datacite_doi(paper_id: str, account: str = "prod") -> Optional[str]:
    """Get the DataCite DOI for a given paper ID."""
    row = (
        db.session.query(DataciteDois)
        .filter(DataciteDois.paper_id == paper_id)
        .filter(DataciteDois.account == account)
        .first()
    )
    return row.doi if row else None


def service_status()->List[str]:
    try:
        db.session.query(Document.document_id).limit(1).first()
    except NoResultFound:
        return [f"{__file__}: service.database: No documents found in db"]
    except (OperationalError, DBAPIError) as ex:
        return [f"{__file__}: Error executing test query count on documents: {ex}"]
    except Exception as ex:
        return [f"{__file__}: Problem with DB: {ex}"]

    if current_app.config["LATEXML_ENABLED"]:
        try:
            db.session.query(DBLaTeXMLDocuments.paper_id).limit(1).first()
        except NoResultFound:
            return [f"{__file__}: service.database DBLaTeXML: No documents found in db"]
        except (OperationalError, DBAPIError) as ex:
            return [f"{__file__}: DBLaTeXML: Error executing test query count on documents: {ex}"]
        except Exception as ex:
            return [f"{__file__}: DBLaTeXML: Problem with DB: {ex}"]

    return []

@db_handle_error(db_logger=logger, default_return_val=None)
def get_yearly_article_counts(archive: str, year: int) -> YearCount:
    """fetch total of new and cross-listed articles by month for a given category and year
        supports both styles of ids at once
    """

    #filters to the correct database query based on the year the id schema changed
    if year > 2007: #query with the new id system
        return _get_yearly_article_counts_new_id(archive,year)
    elif year ==2007: #combine queries from both systems - ouch
        old_id_count=_get_yearly_article_counts_old_id(archive,year)
        new_id_count=_get_yearly_article_counts_new_id(archive,year)
        return _combine_yearly_article_counts(new_id_count, old_id_count)
    else: #query with the old id system
        return _get_yearly_article_counts_old_id(archive,year)

@db_handle_error(db_logger=logger, default_return_val=None)
def _get_yearly_article_counts_new_id(archive: str, year: int) -> YearCount:
    """fetch total of new and cross-listed articles by month for a given category and year
        designed to match new style ids
    """
    # Define the case statement for categorizing entries
    categorization_case = case([(Metadata.abs_categories.startswith(f"{archive}."), 'new'),
                               (Metadata.abs_categories.contains(f" {archive}."), 'cross')],
                              else_='no_match')

    # Build the query to get both counts for all months
    count_query = (
        db.session.query(
            func.substr(Metadata.paper_id, 3, 2).label('month'),
            func.count(distinct(case([(categorization_case == 'new', Metadata.paper_id)], else_=None))).label('count_new'),
            func.count(distinct(case([(categorization_case == 'cross', Metadata.paper_id)], else_=None))).label('count_cross')
        )
        .filter(Metadata.paper_id.startswith(f"{year % 100:02d}"))
        .group_by('month')
        .all()
    )

    return _process_yearly_article_counts(count_query, year)

@db_handle_error(db_logger=logger, default_return_val=None)
def _get_yearly_article_counts_old_id(archive: str, year: int) -> YearCount:
    """fetch total of new and cross-listed articles by month for a given category and year
        designed to match old style ids
    """
    # Define the case statement for categorizing entries
    categorization_case = case([(Metadata.abs_categories.startswith(archive), 'new'),
                               (Metadata.abs_categories.contains(f" {archive}"), 'cross')],
                              else_='no_match')

    # Build the query to get both counts for all months
    count_query = (
        db.session.query(
            func.substring(func.substring_index(Metadata.paper_id, '/', -1), 3,2).label('month'),
            func.count(distinct(case([(categorization_case == 'new', Metadata.paper_id)], else_=None))).label('count_new'),
            func.count(distinct(case([(categorization_case == 'cross', Metadata.paper_id)], else_=None))).label('count_cross')
        )
        .filter(Metadata.paper_id.like(f"%/{year % 100:02d}%"))
        .group_by('month')
        .all()
    )
    return _process_yearly_article_counts(count_query, year)

def _process_yearly_article_counts(query_result: List[Row], year: int) -> YearCount:
    """take entries found in metadata table for yearly totals and create YearCount of them"""
    monthlist=[]
    #create empty months
    for i in range(1,13):
        monthlist.append(MonthTotal(year,i,0,0))
    new_total=0
    cross_total=0

    for entry in query_result:
        index=int(entry.month)-1
        monthlist[index].new=entry.count_new
        monthlist[index].cross=entry.count_cross

        new_total+=entry.count_new
        cross_total+=entry.count_cross

    data=YearCount(year,new_total, cross_total,monthlist)
    return data

def _combine_yearly_article_counts(yc1: YearCount, yc2: YearCount)-> YearCount:
    """combines the monthly article totals for a year for two YearCounts
    output year is that of yearcount 1. Intended for combining year data of 2007 due to id style switch
    """
    new_count=yc1.new_count+yc2.new_count
    cross_count=yc1.cross_count+yc2.cross_count
    months=[]
    for i in range(1,13):
        new_month= MonthTotal(yc1.year, i, yc1.by_month[i-1].new+yc2.by_month[i-1].new, yc1.by_month[i-1].cross+yc2.by_month[i-1].cross)
        months.append(new_month)
    total=YearCount(yc1.year,new_count, cross_count, months )
    return total

@db_handle_error(db_logger=logger, default_return_val=None)
def get_latexml_status_for_document(paper_id: str, version: int = 1) -> Optional[int]:
    """Get latexml conversion status for a given paper_id and version"""
    row = (
        db.session.query(DBLaTeXMLDocuments)
        .filter(DBLaTeXMLDocuments.paper_id == paper_id)
        .filter(DBLaTeXMLDocuments.document_version == version)
        .first()
    )
    return row.conversion_status if row else None


@db_handle_error(db_logger=logger, default_return_val=None)
def get_user_id_by_author_id(author_id: str) -> Optional[int]:
    row = (
        db.session.query(AuthorIds)
        .filter(AuthorIds.author_id == author_id)
        .first()
    )
    return row.user_id if row else None


@db_handle_error(db_logger=logger, default_return_val=None)
def get_user_id_by_orcid(orcid: str) -> Optional[int]:
    row = (
        db.session.query(OrcidIds)
        .filter(OrcidIds.orcid == orcid)
        .first()
    )
    return row.user_id if row else None


@db_handle_error(db_logger=logger, default_return_val=None)
def get_user_display_name(user_id: int) -> Optional[str]:
    row = (
        db.session.query(User)
        .filter(User.user_id == user_id)
        .first()
    )
    if row is None:
        return None

    first = f"{row.first_name} " if row.first_name else ""
    last = f"{row.last_name}" if row.last_name else ""
    return first + last


@db_handle_error(db_logger=logger, default_return_val=None)
def get_orcid_by_user_id(user_id: int) -> Optional[str]:
    row = (
        db.session.query(OrcidIds)
        .filter(OrcidIds.user_id == user_id)
        .first()
    )
    return row.orcid if row else None


@db_handle_error(db_logger=logger, default_return_val=[])
def get_articles_for_author(user_id: int) -> List[ListingItem]:
    rows = (
        db.session.query(Document, paper_owners)
        .filter(Document.document_id == paper_owners.c.document_id)
        .filter(paper_owners.c.user_id == user_id)
        .filter(paper_owners.c.flag_author == 1)
        .filter(paper_owners.c.valid == 1)
        .filter(Document.paper_id.notlike('test%'))
        .order_by(Document.dated.desc())
        .all()
    )
    return [ListingItem(row[0].paper_id, 'new', row[0].primary_subject_class)
            for row in rows]
