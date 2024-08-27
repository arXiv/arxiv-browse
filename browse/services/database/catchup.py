from typing import Union, Tuple, Set
from datetime import date

from sqlalchemy import or_, and_, case
from sqlalchemy.orm import aliased, load_only
from sqlalchemy.sql import func

from arxiv.db import Session
from arxiv.db.models import Metadata, NextMail, t_arXiv_in_category 
from arxiv.taxonomy.category import Group, Archive, Category

from browse.services.database.listings import _metadata_to_listing_item, process_requested_subject
from browse.services.listing import ListingNew, gen_expires

CATCHUP_LIMIT=2000

def get_catchup_data(subject: Union[Group, Archive, Category], day:date, include_abs:bool, page_num:int)-> ListingNew:
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

    #categorize by type of listing
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

    #counts
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

    #data
    meta = aliased(Metadata)
    load_fields = [
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
    ]
    if include_abs:
        load_fields.append(meta.abstract)

    #sort, limit and fetch
    results=(
        Session.query(
            listing_type,
            meta
        )
        .join(meta, meta.document_id == all_items.c.document_id)
        .filter(listing_type.label('case_order').in_(valid_types))
        .filter(meta.is_current ==1)
        .order_by(case_order, meta.paper_id)
        .offset(offset)
        .limit(10)
        .options(load_only(*load_fields, raiseload=True))
        .all()
    )

    #process similar to listings
    items=[]
    for row in results:
        listing_case, metadata = row
        if listing_case=="repcross":
            listing_case="rep"
        item= _metadata_to_listing_item(metadata, listing_case)
        items.append(item)

    return ListingNew(listings=items, 
                      new_count=new_count, 
                      cross_count=cross_count, 
                      rep_count=rep_count, 
                      announced=day,
                      expires=gen_expires())
