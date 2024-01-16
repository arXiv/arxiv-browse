from datetime import datetime
from dateutil.tz import gettz, tzutc
from typing import List, Optional, Tuple

from sqlalchemy import case, distinct, or_, and_
from sqlalchemy.sql import func, select
from sqlalchemy.engine import Row
from sqlalchemy.orm import aliased

from browse.services.listing import (
    MonthCount,
    YearCount,
    Listing,
    ListingItem,
    gen_expires,
)
from browse.services.database.models import Metadata, db, DocumentCategory, Document
from browse.domain.metadata import DocMetadata, AuthorList
from browse.domain.category import Category
from browse.domain.version import VersionEntry, SourceFlag

from arxiv import taxonomy
from arxiv.taxonomy.definitions import CATEGORIES
from arxiv.base.globals import get_application_config
from arxiv.base import logging
from logging import Logger
from werkzeug.exceptions import BadRequest

logger = logging.getLogger(__name__)
app_config = get_application_config()
tz = gettz(app_config.get("ARXIV_BUSINESS_TZ"))


def get_articles_for_month(
    archive_or_cat: str, year: int, month: Optional[int], skip: int, show: int
) -> Listing:
    """archive: archive or category name, year:requested year, month: requested month - no month means retreive listings for the year,
    skip: number of entries to skip, show:number of entries to return
    Retrieve entries from the Metadata table for papers in a given category and month.
    Searches for all possible category names that could apply to a particular archive or category
    also retrieves information on if any of the possible categories is the articles primary
    """
    category_list=_all_possible_categories(archive_or_cat)

    dc = aliased(DocumentCategory)
    doc = aliased(Document)
    meta = aliased(Metadata)

    """
    retrieves the max value for is_primary over all searched for categories per document
    this results in one entry per document with a value of 1 if any of the requested categories is the primary and 0 otherwise
    """

    #gets document_ids of paper_ids in right time frame
    starter=db.session.query(doc.document_id)
    if month: #for monthly listings
        if year > 2007: #new ids
            doc_ids=starter.filter(doc.paper_id.startswith(f"{year % 100:02d}{month:02d}"))
        elif year < 2007: #old ids (slow)
            doc_ids=starter.filter(doc.paper_id.like(f"%/{year % 100:02d}{month:02d}%"))
        else: #2007 splits in april
            if month<4:
                doc_ids=starter.filter(doc.paper_id.like(f"%/{year % 100:02d}{month:02d}%"))
            else:
                doc_ids=starter.filter(doc.paper_id.startswith(f"{year % 100:02d}{month:02d}"))

    else: #for yearly listings   
        if year > 2007: #new ids
            doc_ids=starter.filter(doc.paper_id.startswith(f"{year % 100:02d}"))
        elif year < 2007: #old ids (slow)
            doc_ids=starter.filter(doc.paper_id.like(f"%/{year % 100:02d}%"))
        else: #both styles present
            doc_ids=starter.filter(
                (doc.paper_id.startswith(f"{year % 100:02d}"))
                | (doc.paper_id.like(f"%/{year % 100:02d}%"))
            )                     

    #filters to only the ones in the right category and records if any of the requested categories are primary
    cat_query = (db.session.query(dc.document_id, func.max(dc.is_primary).label('is_primary'))
        .where(dc.document_id.in_(doc_ids))
        .where(dc.category.in_(category_list))
        .group_by(dc.document_id)
        .subquery()
    )

    #gets the metadata for applicable documents
    main_query=(db.session.query(meta, cat_query.c.is_primary)
        .select_from(
            cat_query.join(meta, meta.document_id==cat_query.c.document_id)
            )
        .filter(meta.is_current == 1)
    )

    rows=( 
        main_query.order_by(cat_query.c.is_primary.desc(), meta.paper_id)
        .offset(skip)
        .limit(show)
        )
    
    result=rows.all() #get listings to display
    count=main_query.count() #get total entries 
    new_listings, cross_listings = _entries_into_listing_items(result)

    if not month: month=1 #yearly listings need a month for datetime

    return Listing(
        listings=new_listings + cross_listings,
        pubdates=[(datetime(year, month, 1), 1)],  # only used for display month
        count=count,
        expires=gen_expires(),
    )

def _entries_into_listing_items(
    query_result: List[Tuple[Metadata, int]]
) -> Tuple[List[ListingItem], List[ListingItem]]:
    """turns rows of document and category into a underfilled version of DocMetadata.
    Underfilled to match the behavior of fs_listings, omits data not needed for listing items
    """
    new_listings = []
    cross_listings = []
    for entry in query_result:
        meta, primary = entry
      
        doc = DocMetadata(  
            arxiv_id=meta.paper_id,
            arxiv_id_v=f"{meta.paper_id}v{meta.version}",
            title=meta.title,
            authors=AuthorList(meta.authors),
            abstract=meta.abstract,
            categories=meta.abs_categories,
            primary_category=Category(meta.abs_categories.split()[0]),
            secondary_categories=[
                Category(sc) for sc in meta.abs_categories.split()[1:]
            ],
            comments=meta.comments,
            journal_ref=meta.journal_ref,
            version=meta.version,
            version_history=[
                VersionEntry(
                    version=meta.version,
                    raw="",
                    submitted_date=None, # type: ignore
                    size_kilobytes=meta.source_size,
                    source_flag=SourceFlag(meta.source_flags),
                )
            ],
            raw_safe="",
            submitter=None, # type: ignore
            arxiv_identifier=None, # type: ignore
            primary_archive=None, # type: ignore
            primary_group=None, # type: ignore
            modified=None, # type: ignore
        )

        item = ListingItem(
            id=meta.paper_id,
            listingType="new" if primary == 1 else "cross",
            primary=Category(meta.abs_categories.split()[0]).id,
            article=doc,
        )
        if primary == 1:  # new listings go before crosslists
            new_listings.append(item)
        else:  # new listings go before crosslists
            cross_listings.append(item)

    return new_listings, cross_listings

def _all_possible_categories(archive_or_cat:str) -> List[str]:
    """returns a list of all categories in an archive, or all possible alternate names for categories
    takes into account aliases and subsumed archives
    """
    if archive_or_cat in taxonomy.ARCHIVES: #get all categories for archvie
        return get_categories_from_archive(archive_or_cat)
    elif archive_or_cat in taxonomy.CATEGORIES: #check for alternate names
        second_name=_check_alternate_name(archive_or_cat)
        if second_name: 
            return [archive_or_cat, second_name]
        else:
            return [archive_or_cat]
    else:
        raise BadRequest

def get_categories_from_archive(archive:str) ->List[str]:
    """returns a list names of all categories under an archive
    includes older names that make no longer be active
    """
    list=[]
    for category in CATEGORIES.keys():
        if CATEGORIES[category]["in_archive"] == archive:
            list.append(category)
            second_name=_check_alternate_name(category)
            if second_name:
                list.append(second_name)

    return list

def _check_alternate_name(category:str) -> Optional[str]:
    # returns alternate name for aliases
    #returns previous name if archive was subsumed

    #check for aliases
    for key, value in taxonomy.CATEGORY_ALIASES.items():
        if category == key: #old alias name provided
            return value # type: ignore
        elif category == value: #new alias name provided
            return key # type: ignore
        
    #check for subsumed archives
    for key, value in taxonomy.ARCHIVES_SUBSUMED.items():
        if category == value: #has old archive name
            return key # type: ignore

    return None #no alternate names

def get_yearly_article_counts(archive: str, year: int) -> YearCount:

    dc = aliased(DocumentCategory)
    doc = aliased(Document)

    category_list=_all_possible_categories(archive)
    new_doc_ids=(
        db.session.query(
            doc.document_id,
            func.substr(doc.paper_id, 3, 2).label("month"),
        )
        .filter(doc.paper_id.startswith(f"{year % 100:02d}"))
        .subquery()
    )
    old_doc_ids=(
        db.session.query(
            doc.document_id,
            func.substring(
                func.substring_index(doc.paper_id, "/", -1), 3, 2
            ).label("month")
        )
        .filter(doc.paper_id.like(f"%/{year % 100:02d}%"))
        .subquery()
    )

    if year > 2007: 
        doc_ids=new_doc_ids        
    elif year < 2007: 
        doc_ids=old_doc_ids
    else: #both styles present
        doc_ids=db.session.query(
            old_doc_ids.c.document_id.label("document_id"), 
            old_doc_ids.c.month.label("month")
            ).union_all(
                db.session.query(
                    new_doc_ids.c.document_id.label("document_id"), 
                    new_doc_ids.c.month.label("month")
                )
            ).subquery()

    subquery=(
        db.session.query(
            doc_ids.c.month,
            func.max(dc.is_primary).label("is_primary")
        )
        .select_from(
        doc_ids.join(dc, dc.document_id==doc_ids.c.document_id)
        )
        .where(dc.category.in_(category_list))
        .group_by(doc_ids.c.document_id)
        .subquery()
    )

    query = (
        db.session.query(
            subquery.c.month,
            func.count(case([(subquery.c.is_primary == 1, 1)])).label("count_new"),
            func.count(case([(subquery.c.is_primary == 0, 1)])).label("count_cross")
        )
        .group_by(subquery.c.month)
    )


    result=query.all()
    return _process_yearly_article_counts(result, year)

def _process_yearly_article_counts(query_result: List[Row], year: int) -> YearCount:
    """take entries found in metadata table for yearly totals and create YearCount of them"""
    monthlist = []
    # create empty months
    for i in range(1, 13):
        monthlist.append(MonthCount(year, i, 0, 0))
    new_total = 0
    cross_total = 0

    for entry in query_result:
        index = int(entry.month) - 1
        monthlist[index].new = entry.count_new
        monthlist[index].cross = entry.count_cross

        new_total += entry.count_new
        cross_total += entry.count_cross

    data = YearCount(year, new_total, cross_total, monthlist)
    return data
