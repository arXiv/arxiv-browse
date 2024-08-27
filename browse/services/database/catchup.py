from typing import Union, List, Tuple, Set
from datetime import date

from sqlalchemy import or_, and_, case
from sqlalchemy.orm import aliased, load_only
from sqlalchemy.sql import func

from arxiv.db import Session
from arxiv.db.models import Metadata, DocumentCategory, Document, NextMail, t_arXiv_in_category 
from arxiv.taxonomy.category import Group, Archive, Category

CATCHUP_LIMIT=2000

def get_catchup_data(subject: Union[Group, Archive, Category], day:date, include_abs:bool, page_num:int):
    """
    parameters should already be verified (only canonical subjects, date acceptable)
    """
    offset=(page_num-1)*CATCHUP_LIMIT

    mail_id=f"{(day.year-2000):02d}{day.month:02d}{day.day:02d}" #will need to be changed in 3000 ;)
    #get document ids
    doc_ids=(
        Session.query(
            NextMail.document_id,
            NextMail.version,
            NextMail.type
        )
        .filter(NextMail.mail_id==mail_id)
        .filter(NextMail.type!="jref")
        .filter(
            or_(
                NextMail.type != 'rep',
                NextMail.version <= 5
            )
        )
        .subquery()
    )

    #filter by subject
    aic = aliased(t_arXiv_in_category)
    archives, categories=process_requested_subject(subject)
    cat_conditions = [and_(aic.c.archive == arch_part, aic.c.subject_class == subj_part) for arch_part, subj_part in categories]

    all_items=(
        Session.query(
            doc_ids.c.document_id, 
            doc_ids.c.type,
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

    #sort and limit
    listing_type = case(*
        [
            (and_(all_items.c.type == 'new', all_items.c.is_primary == 1), 'new'),
            (and_(all_items.c.type == 'cross', all_items.c.is_primary == 1), 'no-match'), #removes intra archive crosses
            (or_(all_items.c.type == 'new', all_items.c.type == 'cross'), 'cross'),
            (and_(all_items.c.type == 'rep', all_items.c.is_primary == 1), 'rep'),
            (all_items.c.type == 'rep', 'repcross')
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
    selected_items=(
        Session.query(
            all_items.c.document_id, 
            listing_type
        )
        .filter(listing_type.label('case_order').in_(valid_types))
        .order_by(case_order)
        .offset(offset)
        .limit(CATCHUP_LIMIT)
        .subquery()
    )
    
    #fetch the data
    return


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
            for category in subject.get_archives(True):
                process_cat_name(category.alt_name) if category.alt_name else None 

    return archs, cats
