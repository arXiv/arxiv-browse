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

    def _query_base(self,
                    archiveOrCategory: str,
                    year: int, month: Optional[int]=None) -> Any:
        query = NextMail.query
            
        # query = query.join(Documents)
        # query = query.join(DocumentCategory)
        
        # #TODO make something that works for archives
        # query = query.filter(DocumentCategory.category == archiveOrCategory)

        # TODO Not filtered by category or archive right now

        mail_id = f"{year:02}{month:02}%" if month else f"{year:02}%"
        query = query.filter(NextMail.mail_id.like(mail_id))
        return query
    
    def list_articles_by_year(self,
                              archiveOrCategory: str,
                              year: int,
                              skip: int,
                              show: int,
                              if_modified_since: Optional[str] = None) -> ListingResponse:
        """Get listings by year."""
        query = self._query_base(archiveOrCategory,year,None)        
        query = _add_skipshow(query, skip, show)
        res = query.all()
        total_count = self._query_base(archiveOrCategory, year, None).count() # TODO probably very slow
        return _to_listings(list(res), total_count)

    def list_articles_by_month(self,
                               archiveOrCategory: str,
                               year: int,
                               month: int,
                               skip: int,
                               show: int,
                               if_modified_since: Optional[str] = None) -> ListingResponse:
        """Get listings for a month."""
        return _to_listings(self._query_base(archiveOrCategory,skip,show,year,month).all())


    def list_new_articles(self,
                          archiveOrCategory: str,
                          skip: int,
                          show: int,
                          if_modified_since: Optional[str] = None) -> NewResponse:
        """Gets listings for the most recent announcement/publish."""
        raise Exception("not implemented")


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



def _to_listings(res: Any, total_count) -> ListingResponse:
    return {'listings':[ {"id":row.paper_id,
                          "listingType":row.type,
                          "primary":'hep-ph'} #TODO add real primary
                         for row in res],  
            'pubdates': _to_pubdates(res),
            'count': total_count,
            'expires': ''}

def _to_pubdates(res: Any):
    pubdates = []
    keyf = lambda row: row.mail_id
    next_rows = list(sorted(res, key=keyf))
    for day, grp in groupby(next_rows, keyf):
        print(f"the day is {day}")
        yy, mm, dd = int(day[0:2]), int(day[2:4]), int(day[4:6])
        if yy > 80: # it's in 1900s
            yyyy = 1900 + yy
        else:
            yyyy = 2000 + yy
        pubdates.append( (datetime.date(yyyy,mm,dd), len(list(grp)) ))

    return pubdates


def _add_skipshow(query, skip: int, show: int):
    return query.offset(skip).limit(show)
