"""arXiv listings backed by a DB."""
from itertools import groupby
import datetime

from typing import Optional, Any

from sqlalchemy import func

from browse.services.listing.base_listing import NewResponse, \
    ListingResponse, ListingCountResponse, ListingService
from browse.services.database.models import Metadata, Document,\
    DocumentCategory, NextMail
"""
The following three paragraphs are from an older comment about listings
in arxiv:

Currently (2018-10) getting everything for a listing from the DB is
not possible. There is no table that correctly records the publish
history in the legacy DB.

The legacy listing files are used only for the IDs of the papers
announced. The rest of the metadata is not kept updated. An example of
this causing a problem is if an article published on 2018-01-01, then
crossed on 2018-01-02, then replaced with a differnt title on
2018-01-03. The cross on 2018-01-02 in the listing file will have the
old title.

Why month granularity? The legacy listing files have only month
granularity for when a paper was announced. In the future there might
be better date granularity for new papers."""


class DBListingService(ListingService):
    """arXiv document listings via DB."""

    def __init__(self, db: Any) -> None:
        """Initialize the DB listing service."""
        self.db=db


    def _latest_mail(self) -> str:
        """Latest mailing day in YYMMDD format from NextMail.mail_id"""
        #TODO add some sort of caching based on publish time
        return self.db.session.query(func.max(NextMail.mail_id)).first()[0]


    def _query_yymm(self,
                    archiveOrCategory: str,
                    year: int,
                    month: Optional[int]=None) -> Any:
        if year<0:
            raise ValueError("year must be positive")
        if year >= 2000:
            year = year - 2000
        elif year > 1900:
            year = year - 1900
        mq = f"{month:02}" if month else ""
        return self._query_base(archiveOrCategory, f"{year:02}{mq}%")


    def _query_base(self,
                    archiveOrCategory: str,
                    mail_id: str) -> Any:
        query = NextMail.query
        query = query.join(Document, NextMail.document_id==Document.document_id)
        query = query.join(DocumentCategory, Document.document_id==DocumentCategory.document_id)        
        query = query.filter(DocumentCategory.category == archiveOrCategory) # TODO make something that works for archives
        if '%' in mail_id:
            return query.filter(NextMail.mail_id.like(mail_id))
        else:
            return query.filter(NextMail.mail_id == mail_id)


    def list_articles_by_year(self,
                              archiveOrCategory: str,
                              year: int,
                              skip: int,
                              show: int,
                              if_modified_since: Optional[str] = None) -> ListingResponse:
        """Get listings by year."""
        query = self._query_yymm(archiveOrCategory, year)
        res = _add_skipshow(query, skip, show).all()
        count = self._query_yymm(archiveOrCategory, year).count() # TODO probably very slow
        return _to_listings(list(res), count)

    def list_articles_by_month(self,
                               archiveOrCategory: str,
                               year: int,
                               month: int,
                               skip: int,
                               show: int,
                               if_modified_since: Optional[str] = None) -> ListingResponse:
        """Get listings for a month."""
        query = self._query_yymm(archiveOrCategory, year, month)
        res = _add_skipshow(query, skip, show).all()
        count = self._query_yymm(archiveOrCategory, year, month).count() # TODO probably very slow
        return _to_listings(res, count)


    def list_new_articles(self,
                          archiveOrCategory: str,
                          skip: int,
                          show: int,
                          if_modified_since: Optional[str] = None) -> NewResponse:
        """Gets listings for the most recent announcement/publish."""
        latest_mail = self._latest_mail()
        query = self._query_base(archiveOrCategory, latest_mail)
        res = _add_skipshow(query, skip, show).all()
        count = self._query_base(archiveOrCategory, latest_mail).count() # TODO probably very slow        
        return _to_new_listings(res, count)


    def list_pastweek_articles(self,
                               archiveOrCategory: str,
                               skip: int,
                               show: int,
                               if_modified_since: Optional[str] = None) -> ListingResponse:
        """Gets listings for the 5 most recent announcement/publish."""
        raise Exception("not implemented")

    def monthly_counts(self,
                       archive: str,
                       year: int) -> ListingCountResponse:
        """Gets monthly listing counts for the year."""
        #TODO monthly_counts returns fake data
        counts = [
            {'year': year, 'month': 1, 'new': 1234, 'cross': 234},
            {'year': year, 'month': 2, 'new': 1224, 'cross': 134},
            {'year': year, 'month': 3, 'new': 1334, 'cross': 324},
            {'year': year, 'month': 4, 'new': 1534, 'cross': 134},
            {'year': year, 'month': 5, 'new': 1644, 'cross': 234},
            {'year': year, 'month': 6, 'new': 983, 'cross': 314},
            {'year': year, 'month': 7, 'new': 876, 'cross': 132},
            {'year': year, 'month': 8, 'new': 1233, 'cross': 294},
            {'year': year, 'month': 9, 'new': 1453, 'cross': 273},
            {'year': year, 'month': 10, 'new': 1502, 'cross': 120},
            {'year': year, 'month': 11, 'new': 1638, 'cross': 100},
            {'year': year, 'month': 12, 'new': 1601, 'cross': 233},
        ]
        return {'month_counts': counts, #type: ignore
                'new_count': sum([mm['new'] for mm in counts]),
                'cross_count': sum([mm['cross'] for mm in counts])}


def _nextmail_to_listing(row):
    return {"id":row.paper_id,
            "listingType":row.type,
            "primary":'hep-ph'} #TODO add real primary

def _to_new_listings(res: Any, count) -> NewResponse:
    # TODO crosses
    new=list(map(_nextmail_to_listing, res))
    return {'listings': new,
            'announced': datetime.date(2007, 4, 1), # TODO
            'submitted' : (datetime.date(2007, 3, 30), datetime.date(2007, 4, 1)),
            'new_count': len(new),
            'cross_count': 0, # TODO crosses
            'rep_count': 0, # TODO repcount
            'expires': 'Wed, 21 Oct 2015 07:28:00 GMT' #TODO
            }



def _to_listings(res: Any, total_count) -> ListingResponse:
    return {'listings': list(map(_nextmail_to_listing, res)),
            'pubdates': _to_pubdates(res),
            'count': total_count,
            'expires': ''}

def _to_pubdates(res: Any):
    pubdates = []
    keyf = lambda row: row.mail_id
    next_rows = list(sorted(res, key=keyf))
    for day, grp in groupby(next_rows, keyf):
        yy, mm, dd = int(day[0:2]), int(day[2:4]), int(day[4:6])
        if yy > 80: # it's in 1900s
            yyyy = 1900 + yy
        else:
            yyyy = 2000 + yy
        pubdates.append( (datetime.date(yyyy,mm,dd), len(list(grp)) ))

    return pubdates


def _add_skipshow(query, skip: int, show: int):
    return query.offset(skip).limit(show)
