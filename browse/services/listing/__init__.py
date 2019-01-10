"""Serves lists of articles for categories and time periods.

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
be better date granularity for new papers.
"""


from datetime import date
from typing import List, Optional, Tuple

from mypy_extensions import TypedDict


ListingItem = TypedDict('ListingItem',
                        {'id': str,
                         'listingType': str,
                         'primary': str})
'''A single item for a listing.

The id is the arXiv ID and may be an idv.

The listing type is one of 'new,'rep','cross','wdr','jref'. These
would be extended with any new types of actions/events that can happen
in the arXiv system.

primary is the primary category of the article.

'''


ListingResponse = TypedDict('ListingResponse',
                            {'listings': List[ListingItem],
                             'pubdates': List[Tuple[date, int]],
                             'count': int})
'''listings is the list of items a time period.

pubdates are the dates of publications. The int is the number of items
published on the associated date. 

count is the count of all the items in the listing for the query.

Why not just do listing: List[Tuple[date,List[ListingItem]}} ?
Because pastweek needs to support counts for the days and needs to be
able to support skip/show. 
'''

NewResponse = TypedDict('NewResponse',
                        {'listings': List[ListingItem],
                         'new_count':int,
                         'cross_count':int,
                         'rep_count':int,
                         'announced': date,
                         'submitted': Tuple[date,date]})
'''
listings is the list of items for the most recent publish cycle.

announced is the date of the most recent publish cycle.

new_count is the count of new the items in the listing for the query.
rep_count is the count of rep the items in the listing for the query.
cross_count is the count of cross the items in the listing for the query.

submitted is the start date of when these items were submitted and the end date.
'''

class ListingService:
    """Class for arXiv document listings."""

    @classmethod
    def version(self) -> str:
        """Version."""
        return "0.2"

    
    def list_articles_by_year(self,
                              archiveOrCategory: str,
                              year: int,
                              skip: int,
                              show: int,
                              if_modified_since: Optional[str] = None) -> ListingResponse:
        """Get listing items for a whole year."""
        raise NotImplementedError

    

    def list_articles_by_month(self,
                               archiveOrCategory: str,
                               year: int,
                               month: int,
                               skip: int,
                               show: int,
                               if_modified_since: Optional[str] = None) -> ListingResponse:
        """Get listings for a month."""
        raise NotImplementedError



    def list_new_articles(self,
                          archiveOrCategory: str,
                          skip: int,
                          show: int,
                          if_modified_since: Optional[str] = None) -> NewResponse:
        """Gets listings for the most recent announcement/publish."""
        raise NotImplementedError


    def list_pastweek_articles(self,
                               archiveOrCategory: str,
                               skip: int,
                               show: int,
                               if_modified_since: Optional[str] = None) -> ListingResponse:
        """Gets listings for the 5 most recent announcement/publish."""
        raise NotImplementedError
