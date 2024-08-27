from typing import Union, List, Tuple, Set
from datetime import date

from sqlalchemy import or_
from sqlalchemy.orm import aliased, load_only

from arxiv.db import Session
from arxiv.db.models import Metadata, DocumentCategory, Document, NextMail, t_arXiv_in_category 
from arxiv.taxonomy.category import Group, Archive, Category

CATCHUP_LIMIT=2000

def get_catchup_data(subject: Union[Group, Archive, Category], day:date, include_abs:bool, page_num:int):
    """
    parameters should already be verified (only canonical subjects, date acceptable)
    """

    mail_id=f"{(day.year-2000):02d}{day.month:02d}{day.day:02d}" #will need to be changed in 3000 ;)
    #get document ids
    doc_ids=(
        Session.query(
            NextMail.document_id,
            NextMail.version,
            NextMail.type,
            NextMail.extra
        )
        .filter(NextMail.mail_id==mail_id)
        .filter(NextMail.type!="jref")
        .filter(
            or_(
                NextMail.type != 'rep',
                NextMail.version <= 5
            )
        )
        .limit(10) #TODO
        .subquery()
    )

    #filter by subject
    archives, categories=process_requested_subject(subject)

    aic = aliased(t_arXiv_in_category)
    all_items=(
        Session.query(
            doc_ids.c.document_id, 
            doc_ids.c.type,
            doc_ids.c.extra
        )
        .join(aic, aic.c.document_id == doc_ids.c.document_id)
    )


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
            cats.add((arch_part, cat_part))
        else:
            archs.add(name)

    def process_archive(arch: Archive) -> None:
        archs.add(arch.id)
        for category in arch.get_categories(True):
            process_cat_name(category.alt_name) if category.alt_name else None 

    #handle category request
    if isinstance(subject, Category):
        process_cat_name(subject.id)
        if subject.alt_name:
            process_cat_name(subject.alt_name)

    elif isinstance(subject, Archive):
        process_archive(subject)

    elif isinstance(subject, Group):
        for arch in subject.get_archives(True):
            process_archive(arch)

    return archs, cats
