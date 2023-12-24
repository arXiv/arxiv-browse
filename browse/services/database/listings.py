from dateutil.tz import gettz, tzutc
from typing import List, Optional

from sqlalchemy import case, distinct
from sqlalchemy.sql import func
from sqlalchemy.engine import Row
from sqlalchemy.orm import aliased

from browse.services.listing import MonthCount, YearCount, Listing, ListingItem
from browse.services.database.models import Metadata, db, DocumentCategory, Document

from arxiv.base.globals import get_application_config
from arxiv.base import logging
from logging import Logger

logger = logging.getLogger(__name__)
app_config = get_application_config()
tz = gettz(app_config.get("ARXIV_BUSINESS_TZ"))

def get_articles_for_month(archive:str, year: int, month: int, skip: int, show: int) -> Listing:
    if archive=="math" and "." not in archive: #seperates math-ph from the general math category
        archive=archive+"."

    #filters to the correct database query based on the year the id schema changed
    if year > 2007: #query with the new id system
        return _get_articles_for_month_new_id(archive,year, month, skip, show)
    elif year ==2007: #combine queries from both systems - ouch
        print("2007 sucks")
    else: #query with the old id system
        return _get_articles_for_month_old_id(archive,year, month, skip, show)
    return

def _get_articles_for_month_new_id(archive:str, year: int, month: int, skip: int, show: Optional[int]) -> Listing:
    """Retrieve entries from the Document table for papers in a given category and month."""
    doc = aliased(Document)
    dc = aliased(DocumentCategory)
    query = (
        db.session.query(doc, dc)
        .join(dc, doc.document_id == dc.document_id)
        .filter(doc.paper_id.startswith(f"{year % 100:02d}{month:02d}"))
        .filter(dc.category.startswith(archive))
        .offset(skip)
        .limit(show)
        .all()
    )
    return query


def _get_articles_for_month_old_id(archive:str, year: int, month: int, skip: int, show: int) -> Listing:
    return

def get_yearly_article_counts(archive: str, year: int) -> YearCount:
    """fetch total of new and cross-listed articles by month for a given category and year
        supports both styles of ids at once
    """
    if archive=="math" and "." not in archive: #seperates math-ph from the general math category
        archive=archive+"."

    #filters to the correct database query based on the year the id schema changed
    if year > 2007: #query with the new id system
        return _get_yearly_article_counts_new_id(archive,year)
    elif year ==2007: #combine queries from both systems - ouch
        old_id_count=_get_yearly_article_counts_old_id(archive,year)
        new_id_count=_get_yearly_article_counts_new_id(archive,year)
        return _combine_yearly_article_counts(new_id_count, old_id_count)
    else: #query with the old id system
        return _get_yearly_article_counts_old_id(archive,year)
    

def _get_yearly_article_counts_new_id(archive: str, year: int) -> YearCount:
    """fetch total of new and cross-listed articles by month for a given category and year
        designed to match new style ids
    """
    # Define the case statement for categorizing entries
    categorization_case = case([(Metadata.abs_categories.startswith(f"{archive}"), 'new'),
                               (Metadata.abs_categories.contains(f" {archive}"), 'cross')],
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
        monthlist.append(MonthCount(year,i,0,0))
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
        new_month= MonthCount(yc1.year, i, yc1.by_month[i-1].new+yc2.by_month[i-1].new, yc1.by_month[i-1].cross+yc2.by_month[i-1].cross)
        months.append(new_month)
    total=YearCount(yc1.year,new_count, cross_count, months )
    return total