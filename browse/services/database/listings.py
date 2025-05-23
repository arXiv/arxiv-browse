from datetime import  datetime
from dateutil.tz import gettz
from typing import List, Optional, Tuple, Set, Union

from sqlalchemy import case, distinct, or_, and_, desc
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.sql import func
from sqlalchemy.engine import Row
from sqlalchemy.orm import aliased, load_only

from browse.services.listing import (
    MonthCount,
    YearCount,
    Listing,
    ListingItem,
    gen_expires,
    ListingNew,
    AnnounceTypes
)

from arxiv.db import Session
from arxiv.db.models import Metadata, Document, Updates, t_arXiv_in_category 
from arxiv.document.metadata import DocMetadata, AuthorList
from arxiv.taxonomy.category import Group, Archive, Category
from arxiv.taxonomy.definitions import CATEGORIES, ARCHIVES
from arxiv.document.version import VersionEntry, SourceFlag

from arxiv.base.globals import get_application_config
from arxiv.base import logging
from werkzeug.exceptions import BadRequest

logger = logging.getLogger(__name__)
app_config = get_application_config()
tz = gettz(app_config.get("ARXIV_BUSINESS_TZ"))

def get_new_listing(archive_or_cat: str,skip: int, show: int) -> ListingNew:
    "gets the most recent day of listings for an archive or category"

    category_list=_all_possible_categories(archive_or_cat)
    archives, cats=_request_categories(archive_or_cat)

    up=aliased(Updates)
    case_order = case(*
        [
            (up.action == 'new', 0),
            (up.action == 'cross', 1),
            (up.action == 'replace', 2),
        ],
        else_=3 
    ).label('case_order')
        
    recent_date=Session.query(func.max(up.date)).scalar_subquery()
    doc_ids=(
        Session.query(
            up.document_id,
            up.date,
            up.action
        )
        .filter(up.date==recent_date)
        .filter(up.version<6)
        .filter(up.action!="absonly")
        .filter(up.category.in_(category_list))
        .group_by(up.document_id) #one listings per paper
        .order_by(case_order) #action kept chosen by priority if multiple
        .subquery() 
    )

    aic = aliased(t_arXiv_in_category)
    cat_conditions = [and_(aic.c.archive == arch_part, aic.c.subject_class == subj_part) for arch_part, subj_part in cats]
   
    #all listings for the specific category set
    all = (
        Session.query(
            doc_ids.c.document_id, 
            doc_ids.c.action, 
            doc_ids.c.date, 
            func.max(aic.c.is_primary).label('is_primary')
        )
        .join(aic, aic.c.document_id == doc_ids.c.document_id)
        .where(
            or_(
                aic.c.archive.in_(archives),
                or_(*cat_conditions)
            )
        )
        .group_by(aic.c.document_id) 
        .subquery() 
    )

    #sorting and counting by type of listing
    listing_type = case(*
        [
            (and_(all.c.action == 'new', all.c.is_primary == 1), 'new'),
            (and_(all.c.action == 'cross', all.c.is_primary == 1), 'no-match'), #removes intra archive crosses
            (or_(all.c.action == 'new', all.c.action == 'cross'), 'cross'),
            (and_(all.c.action == 'replace', all.c.is_primary == 1), 'rep'),
            (all.c.action == 'replace', 'repcross')
        ],
        else_="no_match"
    ).label('listing_type')

    case_order = case(*
        [
            (listing_type == 'new', 0),
            (listing_type == 'cross', 1),
            (listing_type == 'rep', 2),
            (listing_type == 'repcross', 3),
        ],
        else_=4 
    ).label('case_order')

    valid_types=["new", "cross", 'rep','repcross']

    #how many of each type
    counts = (
        Session.query(
            listing_type,
            func.count().label('type_count')
        )
        .filter(listing_type.label('case_order').in_(valid_types))
        .group_by(listing_type)
        .order_by(case_order)
        .all() 
    )

    new_count=0
    cross_count=0
    rep_count=0
    for name, number in counts:
        if name =="new":
            new_count+=number
        elif name=="cross":
            cross_count+=number
        else: #rep and repcross
            rep_count+=number

    #data for listings to be displayed
    meta = aliased(Metadata)
    results = (
        Session.query(
            listing_type,
            meta,
            all.c.date
        )
        .join(meta, meta.document_id == all.c.document_id)
        .filter(listing_type.label('case_order').in_(valid_types))
        .filter(meta.is_current ==1)
        .order_by(case_order, meta.paper_id)
        .offset(skip)
        .limit(show)
        .options(load_only(
            meta.document_id,
            meta.paper_id,
            meta.updated,
            meta.source_flags,
            meta.title,
            meta.authors,
            meta.abs_categories,
            meta.comments,
            meta.journal_ref,
            meta.version,
            meta.modtime,
            meta.abstract,
            raiseload= True
            ))
        .all() 
    )

    #organize results into expected listing
    items=[]
    for row in results:
        listing_case, metadata, _ = row
        if listing_case=="repcross":
            listing_case="rep"
        item= _metadata_to_listing_item(metadata, listing_case)
        items.append(item)

    if len(items)==0: #no results to find the last mailing day from
        mail_date=Session.query(func.max(up.date)).scalar()
    else:
        mail_date=results[0][2] 

    return ListingNew(listings=items, 
                      new_count=new_count, 
                      cross_count=cross_count, 
                      rep_count=rep_count, 
                      announced=mail_date,
                      expires=gen_expires())

def get_recent_listing(archive_or_cat: str,skip: int, show: int) -> Listing:

    category_list=_all_possible_categories(archive_or_cat)
    archives, cats=_request_categories(archive_or_cat)
    up=aliased(Updates)
    dates = (
        Session.query(distinct(up.date).label("date"))
        .order_by(desc(up.date))
        .limit(5)
        .subquery()
    )

    doc_ids=(
        Session.query(
            up.document_id,
            up.date
        )
        .filter(up.date.in_(dates.select()))
        .filter(or_(up.action=="new", up.action=="cross"))
        .filter(up.category.in_(category_list))
        .group_by(up.document_id) #one listing per paper
        .subquery() 
    )

    count_subquery = (
        Session.query(
            dates.c.date,
            func.count(doc_ids.c.document_id).label('count')
        )
        .outerjoin(doc_ids, doc_ids.c.date == dates.c.date)
        .group_by(dates.c.date)
        .order_by(desc(dates.c.date))
        .subquery()
    )

    counts = (
        Session.query(
            count_subquery.c.date,
            count_subquery.c.count
        )
        .all()
    )

    aic = aliased(t_arXiv_in_category)
    cat_conditions = [and_(aic.c.archive == arch_part, aic.c.subject_class == subj_part) for arch_part, subj_part in cats]
    all = (
        Session.query(
            doc_ids.c.date,
            doc_ids.c.document_id,   
            func.max(aic.c.is_primary).label('is_primary')
        )
        .join(aic, aic.c.document_id == doc_ids.c.document_id)
        .where(
            or_(
                aic.c.archive.in_(archives),
                or_(*cat_conditions)
            )
            )
        .group_by(aic.c.document_id) 
        .subquery() 
    )

    meta = aliased(Metadata)
    result=(
        Session.query(
            all.c.is_primary,
            meta
        )
        .join(meta, meta.document_id == all.c.document_id)
        .filter(meta.is_current ==1)
        .order_by(desc(all.c.date), desc(all.c.is_primary), desc(meta.paper_id))
        .offset(skip)
        .limit(show)
        .options(load_only(
            meta.document_id,
            meta.paper_id,
            meta.updated,
            meta.source_flags,
            meta.title,
            meta.authors,
            meta.abs_categories,
            meta.comments,
            meta.journal_ref,
            meta.version,
            meta.modtime,
            raiseload= True
            ))
        .all()
    )

    total=0
    daily_counts=[]
    for count in counts:
        day, number = count
        daily_counts.append((day, number))
        total+=number

    items=[]
    for row in result:
        primary=row[0]
        metadata: Metadata=row[1]
        listing_case: AnnounceTypes
        if primary:
            listing_case="new"
        else:
            listing_case="cross"
        metadata.abstract="" #abstract uneeded but will be referenced
        item= _metadata_to_listing_item(metadata, listing_case)
        items.append(item)

    return Listing(
        listings=items,
        pubdates=daily_counts,
        count=total,
        expires=gen_expires()
    )


def get_articles_for_month(
    archive_or_cat: str, year: int, month: Optional[int], skip: int, show: int
) -> Listing:
    """archive: archive or category name, year:requested year, month: requested month - no month means retreive listings for the year,
    skip: number of entries to skip, show:number of entries to return
    Retrieve entries from the Metadata table for papers in a given category and month.
    Searches for all possible category names that could apply to a particular archive or category
    also retrieves information on if any of the possible categories is the articles primary
    """
    archives, cats=_request_categories(archive_or_cat)
    
    doc = aliased(Document)
    meta = aliased(Metadata)
    aic = aliased(t_arXiv_in_category)

    """
    retrieves the max value for is_primary over all searched for categories per document
    this results in one entry per document with a value of 1 if any of the requested categories is the primary and 0 otherwise
    """

    #gets document_ids of paper_ids in right time frame
    starter=Session.query(doc.document_id)
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
  
    cat_conditions = [and_(aic.c.archive == arch_part, aic.c.subject_class == subj_part) for arch_part, subj_part in cats]
    #filters to only the ones in the right category and records if any of the requested categories are primary
    cat_query = (Session.query(aic.c.document_id, func.max(aic.c.is_primary).label('is_primary'))
        .where(aic.c.document_id.in_(doc_ids))
        .where(
            or_(
                aic.c.archive.in_(archives),
                or_(*cat_conditions)
            )
        )
        .group_by(aic.c.document_id)
        .subquery()
    )

    #gets the metadata for applicable documents
    main_query=(Session.query(meta, cat_query.c.is_primary)
        .select_from(
            cat_query.join(meta, meta.document_id==cat_query.c.document_id)
            )
        .filter(meta.is_current == 1)
    )

    rows=( 
        main_query.order_by(cat_query.c.is_primary.desc(), meta.paper_id)
        .offset(skip)
        .limit(show)
        .options(load_only(
            meta.document_id,
            meta.paper_id,
            meta.updated,
            meta.source_flags,
            meta.title,
            meta.authors,
            meta.abs_categories,
            meta.comments,
            meta.journal_ref,
            meta.version,
            meta.modtime,
            raiseload= True
            ))
        )
    
    result=rows.all() #get listings to display
    count=main_query.count() #get total entries 
    new_listings, cross_listings = _entries_into_monthly_listing_items(result)

    if not month:
        month=1 #yearly listings need a month for datetime

    return Listing(
        listings=new_listings + cross_listings,
        pubdates=[(datetime(year, month, 1), 1)],  # only used for display month
        count=count,
        expires=gen_expires(),
    )

def _metadata_to_listing_item(meta: Metadata, type: AnnounceTypes) -> ListingItem:
    """"turns rows of document and category into a underfilled version of DocMetadata.
    Underfilled to match the behavior of fs_listings, omits data not needed for listing items
    meta: the metadata for an item 
    type: the type of announcement "new" "cross" or "rep" """
    updated=meta.updated
    modtime=meta.modtime
    if updated is None and modtime is None:
        modified=datetime(2010,3,6) #some time required, most recent modtime of an article with no updated column
    elif updated is not None and modtime is not None:
        modified=max(updated,datetime.fromtimestamp(float(modtime)))
    elif updated is None and modtime is not None:
        modified=datetime.fromtimestamp(float(modtime))
    elif updated is not None and modtime is None:
        modified=updated

    if meta.abs_categories:
        primary_cat=CATEGORIES[meta.abs_categories.split()[0]]
        secondary_cats= [
            CATEGORIES[sc] for sc in meta.abs_categories.split()[1:]
        ]
    else:
        primary_cat=CATEGORIES["bad-arch.bad-cat"]
        secondary_cats=[]

    try: #incase abstract wasnt loaded
        abstract=getattr(meta, 'abstract','') 
    except InvalidRequestError:
        abstract=''

    doc = DocMetadata(  
        arxiv_id=meta.paper_id,
        arxiv_id_v=f"{meta.paper_id}v{meta.version}",
        title=  getattr(meta, 'title',''),
        authors=AuthorList(getattr(meta, 'authors',"")),
        abstract= abstract,
        categories= getattr(meta, 'abs_categories',""),
        primary_category=primary_cat,
        secondary_categories=secondary_cats,
        comments=meta.comments,
        journal_ref=meta.journal_ref,
        version=meta.version,
        version_history=[
            VersionEntry(
                version=meta.version,
                raw="",
                submitted_date=None, # type: ignore
                size_kilobytes=0, 
                source_flag=SourceFlag(getattr(meta, 'source_flags', ''))
            )
        ],
        raw_safe="",
        submitter=None, # type: ignore
        arxiv_identifier=None, # type: ignore
        primary_archive=primary_cat.get_archive(), 
        primary_group=primary_cat.get_archive().get_group(), 
        modified=modified
    )
    item = ListingItem(
        id=meta.paper_id,
        listingType=type,
        primary=primary_cat.id, 
        article=doc,
    )
    return item

def _entries_into_monthly_listing_items(
    query_result: List[Tuple[Metadata, int]]
) -> Tuple[List[ListingItem], List[ListingItem]]:
    """ monthly and yearly listings only show new articles, 
    and new articles crosslisted into the category
    """
    new_listings = []
    cross_listings = []
    for entry in query_result:
        meta, primary = entry
        meta.abstract="" #protects from a db call to load an unneeded abstract
        if primary==1:
            list_type="new"
        else:
            list_type="cross"

        item=_metadata_to_listing_item(meta,list_type) #type:ignore

        if primary == 1:  # new listings go before crosslists
            new_listings.append(item)
        else:  # new listings go before crosslists
            cross_listings.append(item)

    return new_listings, cross_listings


def process_requested_subject(subject: Union[Group, Archive, Category])-> Tuple[Set[str], Set[Tuple[str,str]]]:
    """ 
    set of archives to search if appliable, 
    set of tuples are the categories to check for in addition to the archive broken into archive and category parts
    only categories not contained by the set of archives will be returned seperately to work with the archive in category table
    """
    archs=set()
    cats=set()

    #utility functions
    def process_cat_name(name: str) -> None:
        #splits category name into parts and adds it
        if "." in name:
            arch_part, cat_part = name.split(".")
            if arch_part not in archs:
                cats.add((arch_part, cat_part))
        elif name not in archs:
            archs.add(name)

    #handle category request
    if isinstance(subject, Category):
        process_cat_name(subject.id)
        if subject.alt_name:
            process_cat_name(subject.alt_name)

    elif isinstance(subject, Archive):
        archs.add(subject.id)
        for category in subject.get_categories(True):
            process_cat_name(category.alt_name) if category.alt_name else None 

    elif isinstance(subject, Group):
        for arch in subject.get_archives(True):
            archs.add(arch.id)
        for arch in subject.get_archives(True): #twice to avoid adding cateogires covered by archives
            for category in arch.get_categories(True):
                process_cat_name(category.alt_name) if category.alt_name else None 

    return archs, cats


def _request_categories(archive_or_cat:str) -> Tuple[List[str],List[Tuple[str,str]]]:
    """ list of archives to search if appliable, 
    list of tuples are the categories to check for (possibly in addition to the archive) broken into archvie and category parts
    if a category is received, return the category and possible alternate names
    if an archive is received return the archive name and a list of all categories that should be included but arent nominally part of the archive 
    """
    if archive_or_cat in ARCHIVES:
        arch, cats=process_requested_subject(ARCHIVES[archive_or_cat])
    elif archive_or_cat in CATEGORIES:
        arch, cats=process_requested_subject(CATEGORIES[archive_or_cat])
 
    return list(arch), list(cats)

def _all_possible_categories(archive_or_cat:str) -> List[str]:
    """returns a list of all categories in an archive, or all possible alternate names for categories
    takes into account aliases and subsumed archives
    should not return newer names for subsumed archives
    """
    if archive_or_cat in ARCHIVES: #get all categories for archive
        archive=ARCHIVES[archive_or_cat]
        all=set()
        for category in archive.get_categories(True):
            all.add(category.id)
            if category.alt_name:
                all.add(category.alt_name)
        return list(all)
    
    elif archive_or_cat in CATEGORIES: #check for alternate names
        cat=CATEGORIES[archive_or_cat]
        if cat.alt_name: 
            return [cat.id, cat.alt_name]
        else:
            return [cat.id]
    else:
        raise BadRequest(f'Invalid category: {archive_or_cat}')


def get_yearly_article_counts(archive: str, year: int) -> YearCount:

    aic = aliased(t_arXiv_in_category)
    doc = aliased(Document)
    archives, cats=_request_categories(archive)
    cat_conditions = [and_(aic.c.archive == arch_part, aic.c.subject_class == subj_part) for arch_part, subj_part in cats]
   
    new_doc_ids=(
        Session.query(
            doc.document_id,
            func.substr(doc.paper_id, 3, 2).label("month"),
        )
        .filter(doc.paper_id.startswith(f"{year % 100:02d}"))
        .subquery()
    )
    old_doc_ids=(
        Session.query(
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
        doc_ids=Session.query(
            old_doc_ids.c.document_id.label("document_id"), 
            old_doc_ids.c.month.label("month")
            ).union_all(
                Session.query(
                    new_doc_ids.c.document_id.label("document_id"), 
                    new_doc_ids.c.month.label("month")
                )
            ).subquery()
         
    subquery=(
        Session.query(
            doc_ids.c.month,
            func.max(aic.c.is_primary).label("is_primary")
        )
        .select_from(
        doc_ids.join(aic, aic.c.document_id==doc_ids.c.document_id)
        )
        .where(
            or_(
                aic.c.archive.in_(archives),
                or_(*cat_conditions)
            )
        )
        .group_by(doc_ids.c.document_id)
        .subquery()
    )

    query = (
        Session.query(
            subquery.c.month,
            func.count(case(*[(subquery.c.is_primary == 1, 1)])).label("count_new"),
            func.count(case(*[(subquery.c.is_primary == 0, 1)])).label("count_cross")
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

def check_service() -> str:
    query=Session.query(Metadata).limit(1).all()
    if len(query)==1:
        return "GOOD"
    return "BAD"
