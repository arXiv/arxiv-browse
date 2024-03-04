"""arXiv listings backed by a DB."""
import datetime
from itertools import groupby
from typing import Any, List, Optional, Tuple, Union

from arxiv.taxonomy import ARCHIVES
from arxiv.db import session
from arxiv.db.models import (Document, DocumentCategory,
                                             NextMail)
from browse.services.listing import (Listing, ListingCountResponse,
                                     ListingItem, ListingNew,
                                     ListingService, MonthTotal,YearCount, MonthCount,
                                     NotModifiedResponse, gen_expires)
from sqlalchemy import func, text

"""
The following three paragraphs are from an older comment about listings
in arxiv:

Currently (2018-10) getting everything for a listing from the DB is
not possible. There is no table that correctly records the publish
history in the legacy DB.

The legacy listing files are used only for the IDs of the papers
announced. The rest of the metadata is not kept updated. An example of
this causing a problem is if an article published on 2018-01-01, then
crossed on 2018-01-02, then replaced with a different title on
2018-01-03. The cross on 2018-01-02 in the listing file will have the
old title.

Why month granularity? The legacy listing files have only month
granularity for when a paper was announced. In the future there might
be better date granularity for new papers."""


class DBListingService(ListingService):
    """arXiv document listings via DB."""

    def __init__(self) -> None:
        """Initialize the DB listing service."""
        self.session=session


    def _latest_mail(self) -> str:
        """Latest mailing day in YYMMDD format from NextMail.mail_id"""
        #TODO add some sort of caching based on publish time
        return str(self.session().query(func.max(NextMail.mail_id)).first()[0])


    def _year_to_yy(self, year:int)-> str:
        if year<0:
            raise ValueError("year must be positive")
        if year >= 2000:
            year = year - 2000
        elif year > 1900:
            year = year - 1900

        return f"{year:02}"

    def _query_yymm(self,
                    archiveOrCategory: str,
                    year: int,
                    month: Optional[int]=None) -> Any:
        yy = self._year_to_yy(year)
        mq = f"{month:02}" if month else ""
        return self._query_base(archiveOrCategory, f"{yy}{mq}%")


    def _query_base(self,
                    archiveOrCategory: str,
                    mail_id: Optional[str]=None) -> Any:
        query = session.query(NextMail)
        query = query.join(Document, NextMail.document_id==Document.document_id)
        query = query.join(DocumentCategory,
                           Document.document_id==DocumentCategory.document_id)
        if archiveOrCategory in ARCHIVES.keys():
            # TODO There is probably a better way to do archives
            query = query.filter(
                DocumentCategory.category.ilike(f'{archiveOrCategory}%'))
        else:
            query = query.filter(DocumentCategory.category == archiveOrCategory)

        if mail_id and '%' in mail_id:
            query = query.filter(NextMail.mail_id.like(mail_id))
        elif mail_id:
            query = query.filter(NextMail.mail_id == mail_id)

        return query


    def list_articles_by_year(self,
                              archiveOrCategory: str,
                              year: int,
                              skip: int,
                              show: int,
                              if_modified_since: Optional[str] = None) -> Listing:
        """Get listings by year."""
        query = self._query_yymm(archiveOrCategory, year)
        res = _add_skipshow(query, skip, show).all()
        count = self._query_yymm(archiveOrCategory, year).count()
        return _to_listings(list(res), count)


    def list_articles_by_month(self,
                               archiveOrCategory: str,
                               year: int,
                               month: int,
                               skip: int,
                               show: int,
                               if_modified_since: Optional[str] = None) -> Listing:
        """Get listings for a month."""
        query = self._query_yymm(archiveOrCategory, year, month)
        res = _add_skipshow(query, skip, show).all()
        count = self._query_yymm(archiveOrCategory, year, month).count()
        return _to_listings(res, count)


    def list_new_articles(self,
                          archiveOrCategory: str,
                          skip: int,
                          show: int,
                          if_modified_since: Optional[str] = None) -> ListingNew:
        """Gets listings for the most recent announcement/publish."""
        latest_mail = self._latest_mail()
        query = self._query_base(archiveOrCategory, latest_mail)
        res = _add_skipshow(query, skip, show).all()
        count = self._query_base(archiveOrCategory, latest_mail).count()
        # TODO crosses
        new=list(map(_nextmail_to_listing, res))
        return ListingNew(listings=new,
                          announced=datetime.date(2007, 4, 1), # TODO
                          submitted= (datetime.date(2007, 3, 30),
                                      datetime.date(2007, 4, 1)),
                          new_count=len(new),
                          cross_count=0, # TODO crosses
                          rep_count=0, # TODO repcount
                          expires='Wed, 21 Oct 2015 07:28:00 GMT' #TODO
                          )

    def list_pastweek_articles(self,
                               archiveOrCategory: str,
                               skip: int,
                               show: int,
                               if_modified_since: Optional[str] = None)\
                               -> Union[Listing, NotModifiedResponse]:
        """Gets listings for the 5 most recent announcement/publish."""
        query = self._query_base(archiveOrCategory)
        query = query.order_by(NextMail.mail_id.desc()).limit(5)
        res = list(query.all())
        return _to_listings(res, len(res))

    def monthly_counts(self,
                       archive: str,
                       year: int) -> YearCount:
        """Gets monthly listing counts for the year."""
        # TODO needs filtering by archive
        txtq="""
SELECT SUBSTR(mail_id,3,2) AS month,
SUM(CASE type WHEN 'new' THEN 1 ELSE 0 END) AS new_count,
SUM(CASE type WHEN 'cross' THEN 1 ELSE 0 END ) AS cross_count
FROM arXiv_next_mail
WHERE mail_id LIKE :yy
GROUP BY month
"""
        # TODO Limit to archive!
        yy = self._year_to_yy(int(year))
        res = self.session().execute(text(txtq), {"yy": yy+"%"})

        months= [MonthCount(int(yy), int(mm), int(new), int(cross))
                for mm,new,cross in res]

        result=YearCount(year, sum([mx.new for mx in months]), sum([mx.cross for mx in months]), months)
        return result



    def service_status(self)->List[str]:
        # TODO
        return []

def _nextmail_to_listing(row: Any) -> ListingItem:
    return ListingItem(id=row.paper_id, listingType=row.type,
                       primary='hep-ph')  # TODO add real primary


def _to_listings(res: Any, total_count: int) -> Listing:
    return Listing(listings=list(map(_nextmail_to_listing, res)),
                   pubdates=_to_pubdates(res),
                   count=total_count,
                   expires='')

def _to_pubdates(res: Any) -> List[Tuple[datetime.date, int]]:
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


def _add_skipshow(query, skip: int, show: int):  # type: ignore
    return query.offset(skip).limit(show)
