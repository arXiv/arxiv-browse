from typing import Union
from datetime import date

from sqlalchemy import or_

from arxiv.db import Session
from arxiv.db.models import Metadata, DocumentCategory, Document, NextMail, t_arXiv_in_category 
from arxiv.taxonomy.category import Group, Archive, Category

CATCHUP_LIMIT=2000

def get_catchup_data(subject: Union[Group, Archive, Category], day:date, include_abs:bool, page_num:int):
    
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

