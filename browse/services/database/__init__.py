"""Import db instance and define utility functions."""
# pylint disable=no-member

import ipaddress
from datetime import date, datetime, timezone
from typing import (
    Any, 
    Callable, 
    List, 
    Mapping, 
    Optional, 
    Tuple, 
    Dict,
    Iterable
)

from flask import current_app

from arxiv.db import session
from arxiv.base.globals import get_application_config
from arxiv.document.metadata import DocMetadata
from dateutil.tz import gettz, tzutc
from sqlalchemy import Row, asc, desc, not_, select
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import func, select, Select, tuple_

from arxiv.identifier import Identifier
from arxiv.db.models import (
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
    TapirUser,
    PaperOwner,
    t_arXiv_in_category,
    t_arXiv_stats_hourly,
    Metadata
)
from browse.services.listing import ListingItem
from browse.services.listing import MonthCount, YearCount
from arxiv.base import logging
from logging import Logger

logger = logging.getLogger(__name__)
app_config = get_application_config()
tz = gettz(app_config.get("ARXIV_BUSINESS_TZ"))


def db_handle_error(db_logger: Logger, default_return_val: Any, ignore_errors: bool = False) -> Any:
    """Handle operational database errors via decorator.

    Parameters
    ----------
    db_logger
    default_return_val: return value in the case of an `NoResultFound`, `OperationalError` or `DBAPIError` of the inner fn.
    ignore_errors: By default, False. If True, all errors will get the `default_return_val`.

    """

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
                if ignore_errors:
                    return default_return_val
                else:
                    raise

        return wrapper

    return decorator


def __all_trackbacks_query() -> Select[Tuple[TrackbackPing]]:
    return select(TrackbackPing)


def __paper_trackbacks_query(paper_id: str) -> Select[Tuple[TrackbackPing]]:
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
        select(
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
        session.execute(
            select(stmt.c.id, stmt.c.label).filter(stmt.c.exclusions == 0)
        ).first()
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
def get_all_trackback_pings() -> List[Row[Tuple[TrackbackPing]]]:
    """Get all trackback pings in database."""
    return list(session.execute(__all_trackbacks_query()).fetchall())


# Used only on trackback page
@db_handle_error(db_logger=logger, default_return_val=[])
def get_paper_trackback_pings(paper_id: str) -> List[TrackbackPing]:
    """Get trackback pings for a particular document (paper_id)."""
    return list(
        session.execute(
            __paper_trackbacks_query(paper_id)
            .distinct(TrackbackPing.url)
            .group_by(TrackbackPing.url)
            .order_by(TrackbackPing.posted_date.desc())
        ).scalars().all()
    )

# Used on tb page and abs page
@db_handle_error(db_logger=logger, default_return_val=None)
def get_trackback_ping(trackback_id: int) -> Optional[TrackbackPing]:
    """Get an individual trackback ping by its id (trackback_id)."""
    return session.execute(select(TrackbackPing).filter(
        TrackbackPing.trackback_id == trackback_id
    )).scalar()


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
        select(TrackbackPing.url)
        .filter(TrackbackPing.status == "accepted")
        .distinct(TrackbackPing.url)
        .group_by(TrackbackPing.url)
        .order_by(TrackbackPing.posted_date.desc())
        .limit(max_trackbacks)
        .subquery()
    )
    tb_doc_tup = (
        select(TrackbackPing, Document.paper_id, Document.title)
        .join(Document, TrackbackPing.document_id == Document.document_id)
        .filter(TrackbackPing.status == "accepted")
        .filter(TrackbackPing.url == stmt.c.url)
        .order_by(TrackbackPing.posted_date.desc())
    )

    return [row._t for row in session.execute(tb_doc_tup).all()]


#Used on abs page
@db_handle_error(db_logger=logger, default_return_val=None)
def get_trackback_ping_latest_date(paper_id: str) -> Optional[datetime]:
    """Get the most recent accepted trackback datetime for a paper_id."""
    timestamp = session.execute(
        select(func.max(TrackbackPing.approved_time))
        .filter(TrackbackPing.document_id == Document.document_id)
        .filter(Document.paper_id == paper_id)
        .filter(TrackbackPing.status == "accepted")
    ).scalar()
    if timestamp:
        dt = datetime.fromtimestamp(timestamp, tz=tz)
        dt = dt.astimezone(tz=tzutc())
        return dt
    return None


# used on abs page
@db_handle_error(db_logger=logger, default_return_val=0)
def count_trackback_pings(paper_id: str) -> int:
    """Count trackback pings for a particular document (paper_id)."""
    num_pings = session.scalar(
        select(
            func.count(func.distinct(TrackbackPing.url)).label("num_pings")
        )
        .filter(TrackbackPing.document_id == Document.document_id)
        .filter(Document.paper_id == paper_id)
        .filter(TrackbackPing.status == "accepted")
    )

    return num_pings or 0


#Not used, only in tests
@db_handle_error(db_logger=logger, default_return_val=0)
def count_all_trackback_pings() -> int:
    """Count trackback pings for all documents, without DISTINCT(URL)."""

    c = session.scalar(
        select(func.count()).
        select_from(TrackbackPing)
    )
    assert isinstance(c, int)
    return c
    


# used in abs page
@db_handle_error(db_logger=logger, default_return_val=None)
def get_dblp_listing_path(paper_id: str) -> Optional[str]:
    """Get the DBLP Bibliography URL for a given document (paper_id)."""
    url = session.scalar(
        select(DBLP.url)
        .filter(Document.paper_id == paper_id)
    )
    return url


# used in abs page
@db_handle_error(db_logger=logger, default_return_val=[])
def get_dblp_authors(paper_id: str) -> List[Optional[str]]:
    """Get sorted list of DBLP authors for a given document (paper_id)."""
    return list(session.execute(
        select(DBLPAuthor.name)
        .join(DBLPDocumentAuthor)
        .join(Document)
        .filter(Document.paper_id == paper_id)
        .order_by(DBLPDocumentAuthor.position)
    ).scalars().all())

# Used on home page and stats page
@db_handle_error(db_logger=logger, default_return_val=None)
def get_document_count() -> Optional[int]:
    """Get the number of documents."""
    # func.count is used here because .count() forces a subquery which
    # is inefficient
    num_documents = session.scalar(
        select(func.count(Document.document_id).label("num_documents"))
        .filter(not_(Document.paper_id.like("test%")))
    )
    return num_documents


# Used on stats page
@db_handle_error(db_logger=logger, default_return_val=0)
def get_document_count_by_yymm(paper_date: Optional[date] = None) -> int:
    """Get number of papers for a given year and month."""
    paper_date = date.today() if not isinstance(paper_date, date) else paper_date
    yymm = paper_date.strftime("%y%m")
    yymm_like = f"{yymm}%"
    if paper_date < date(2007, 4, 1):
        yymm_like = f"%/{yymm}%"
    num_documents = session.scalar(
        select(func.count(Document.document_id).label("num_documents"))
        .filter(Document.paper_id.like(yymm_like))
        .filter(not_(Document.paper_id.like("test%")))
    )
    return num_documents or 0


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

    query = select(Document.paper_id)
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
        query = query.join(t_arXiv_in_category).filter(t_arXiv_in_category.c.archive == archive)
        if subject_class:
            query = query.filter(t_arXiv_in_category.c.subject_class == subject_class)

    result = session.scalar(query)
    if result:
        return f"{result}"
    return None


def __all_hourly_stats_query() -> Select[Any]:
    return select(t_arXiv_stats_hourly)



# Used on stats page
@db_handle_error(db_logger=logger, default_return_val=(0, 0, 0))
def get_hourly_stats_count(stats_date: Optional[date]) -> Tuple[int, int, int]:
    """Get sum of normal/admin connections and nodes for a given date."""
    stats_date = date.today() if not isinstance(stats_date, date) else stats_date
    normal_count = 0
    admin_count = 0
    num_nodes = 0
    a = (select(
            t_arXiv_stats_hourly,
            func.sum(t_arXiv_stats_hourly.c.connections).label("num_connections"),
            t_arXiv_stats_hourly.c.access_type,
            func.max(t_arXiv_stats_hourly.c.node_num).label("num_nodes"),
        )
        .filter(t_arXiv_stats_hourly.c.ymd == stats_date.isoformat())
        .group_by(t_arXiv_stats_hourly.c.access_type))
    
    rows = session.execute(
        a
    ).all()
    try:
        logger.warn(f'ROW TYPE: {type(rows[0])}')
    except Exception as e:
        logger.warn(f'CAN\'T PRINT ROW TYPE WITH {str(e)}')
    for r in rows:
        if r.access_type == "A":
            admin_count = int(r.num_connections) # This is a decimal.Decimal
        else:
            normal_count = int(r.num_connections) # This is a decimal.Decimal
            num_nodes = int(r.num_nodes) # This is an int but want to make sure for mypy

    assert isinstance(normal_count, int) and isinstance(admin_count, int) \
        and isinstance(num_nodes, int)
    return (normal_count, admin_count, num_nodes)


# Used on stats page
# maybe on /today page?
@db_handle_error(db_logger=logger, default_return_val=[])
def get_hourly_stats(stats_date: Optional[date] = None) -> List:
    """Get the hourly stats for a given date."""
    stats_date = date.today() if not isinstance(stats_date, date) else stats_date

    return list(
        session.execute(
            __all_hourly_stats_query()
            .filter(
                t_arXiv_stats_hourly.c.access_type == "N",
                t_arXiv_stats_hourly.c.ymd == stats_date.isoformat(),
            )
            .order_by(asc(t_arXiv_stats_hourly.c.hour), t_arXiv_stats_hourly.c.node_num)
        ).all()
    )


# Used on stats page
@db_handle_error(db_logger=logger, default_return_val=[])
def get_monthly_submission_stats() -> List[StatsMonthlySubmission]:
    """Get monthly submission stats from :class:`.StatsMonthlySubmission`."""
    return list(
        session.execute(
            select(StatsMonthlySubmission)
            .order_by(asc(StatsMonthlySubmission.ym))
        ).scalars().all()
    )

# Used on stats page
@db_handle_error(db_logger=logger, default_return_val=(0, 0))
def get_monthly_submission_count() -> Tuple[int, int]:
    """Get submission totals: number of submissions and number migrated."""
    row = session.execute(
        select(
            func.sum(StatsMonthlySubmission.num_submissions),
            func.sum(StatsMonthlySubmission.historical_delta),
        )
    ).first()
    return row._t if row else (0, 0)


# Used on stats page
@db_handle_error(db_logger=logger, default_return_val=[])
def get_monthly_download_stats() -> List[StatsMonthlyDownload]:
    """Get all the monthly download stats."""
    return list(
        session.execute(
            select(StatsMonthlyDownload)
            .order_by(asc(StatsMonthlyDownload.ym))
        ).scalars().all()
    )

# Used on stats page
@db_handle_error(db_logger=logger, default_return_val=0)
def get_monthly_download_count() -> int:
    """Get the sum of monthly downloads for all time."""
    row = session.scalar(
        select(func.sum(StatsMonthlyDownload.downloads).label("total_downloads"))
    )
    return row or 0


# Used on stats page
@db_handle_error(db_logger=logger, default_return_val=None)
def get_max_download_stats_dt() -> Optional[date]:
    """Get the datetime of the most recent download stats."""
    return session.scalar(select(func.max(StatsMonthlyDownload.ym).label("max_ym")))


@db_handle_error(db_logger=logger, default_return_val=None)
def get_datacite_doi(paper_id: str, account: str = "prod") -> Optional[str]:
    """Get the DataCite DOI for a given paper ID."""
    return session.scalar(
        select(DataciteDois.doi)
        .filter(DataciteDois.paper_id == paper_id)
        .filter(DataciteDois.account == account)
    )

def service_status()->List[str]:
    try:
        session.execute(select(Document.document_id).limit(1)).one()
    except NoResultFound:
        return [f"{__file__}: service.database: No documents found in db"]
    except (OperationalError, DBAPIError) as ex:
        return [f"{__file__}: Error executing test query count on documents: {ex}"]
    except Exception as ex:
        return [f"{__file__}: Problem with DB: {ex}"]

    if current_app.config["LATEXML_ENABLED"]:
        try:
            session.execute(select(DBLaTeXMLDocuments.paper_id).limit(1)).one()
        except NoResultFound:
            return [f"{__file__}: service.database DBLaTeXML: No documents found in db"]
        except (OperationalError, DBAPIError) as ex:
            return [f"{__file__}: DBLaTeXML: Error executing test query count on documents: {ex}"]
        except Exception as ex:
            return [f"{__file__}: DBLaTeXML: Problem with DB: {ex}"]

    return []


@db_handle_error(db_logger=logger, default_return_val=None, ignore_errors=True)
def get_latexml_status_for_document(paper_id: str, version: int = 1) -> Optional[int]:
    """Get latexml conversion status for a given paper_id and version"""
    if not current_app.config["LATEXML_ENABLED"]:
        return None
    return session.scalar(
        select(DBLaTeXMLDocuments.conversion_status)
        .filter(DBLaTeXMLDocuments.paper_id == paper_id)
        .filter(DBLaTeXMLDocuments.document_version == version)
    )


@db_handle_error(db_logger=logger, default_return_val={}, ignore_errors=True)
def get_latexml_statuses_for_listings (listings: Iterable[DocMetadata]) -> Dict[Tuple[str, int], int]:
    if not current_app.config["LATEXML_ENABLED"]:
        return {}
    statuses = session.execute(
        select(DBLaTeXMLDocuments.paper_id, DBLaTeXMLDocuments.document_version, DBLaTeXMLDocuments.conversion_status)
        .filter(tuple_(DBLaTeXMLDocuments.paper_id, DBLaTeXMLDocuments.document_version).in_(
            [(article.arxiv_id, article.highest_version()) for article in listings]
        ))
    ).all()
    return { (i[0], i[1]): i[2] for i in statuses }


def _inside_get_latexml_publish_dt() -> None:
    """Just to enable patching."""
    pass

@db_handle_error(db_logger=logger, default_return_val=None, ignore_errors=True)
def get_latexml_publish_dt (paper_id: str, version: int = 1) -> Optional[datetime]:
    _inside_get_latexml_publish_dt()
    if not current_app.config["LATEXML_ENABLED"]:
        return None
    publish_dt = session.scalar(
        select(DBLaTeXMLDocuments.publish_dt)
        .filter(DBLaTeXMLDocuments.paper_id == paper_id)
        .filter(DBLaTeXMLDocuments.document_version == version)
    )
    return publish_dt.replace(tzinfo=timezone.utc) if publish_dt else None


@db_handle_error(db_logger=logger, default_return_val=None)
def get_user_id_by_author_id(author_id: str) -> Optional[int]:
    return session.scalar(
        select(AuthorIds.user_id)
        .filter(AuthorIds.author_id == author_id)
    )

@db_handle_error(db_logger=logger, default_return_val=None)
def get_user_id_by_orcid(orcid: str) -> Optional[int]:
    return session.scalar(
        select(OrcidIds.user_id)
        .filter(OrcidIds.orcid == orcid)
    )

@db_handle_error(db_logger=logger, default_return_val=None)
def get_user_display_name(user_id: int) -> Optional[str]:
    row = session.scalar(
        select(TapirUser)
        .filter(TapirUser.user_id == user_id)
    )
    if row is None:
        return None

    first = f"{row.first_name} " if row.first_name else ""
    last = f"{row.last_name}" if row.last_name else ""
    return first + last


@db_handle_error(db_logger=logger, default_return_val=None)
def get_orcid_by_user_id(user_id: int) -> Optional[str]:
    return session.scalar(
        select(OrcidIds.orcid)
        .filter(OrcidIds.user_id == user_id)
    )

@db_handle_error(db_logger=logger, default_return_val=[])
def get_articles_for_author(user_id: int) -> List[ListingItem]:
    rows = session.execute(
        select(Document, PaperOwner)
        .filter(Document.document_id == PaperOwner.document_id)
        .filter(PaperOwner.user_id == user_id)
        .filter(PaperOwner.flag_author == 1)
        .filter(PaperOwner.valid == 1)
        .filter(Document.paper_id.notlike('test%'))
        .order_by(Document.dated.desc())
    ).scalars().all()
    return [ListingItem(row[0].paper_id, 'new', row[0].primary_subject_class)
            for row in rows]
