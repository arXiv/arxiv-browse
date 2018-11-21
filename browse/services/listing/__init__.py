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

Martin and Erick would like to continue to use the listings files for
IDs. (Communicated in an informal meeting 2018-11-05) They would like
to use something like abs and listings to create mirrors similar to
how legacy does mirrors.

Why month granularity? The legacy listing files have only month
granularity for when a paper was announced. In the future there might
be better date granularity for new papers.

"""

#from abs import ABCMeta, abstractmethod, classmethod
from typing import List, Optional, Tuple, Union, Sequence
from typing_extensions import Protocol
from mypy_extensions import TypedDict

from datetime import datetime, date
import re
import os

from browse.services.database.models import db
from browse.services.database.models import Metadata

ListingItem = TypedDict('ListingItem',
                        {'id':str,
                         'listingType':str})

                         
# class ListingItem(Protocol):
#     """Single article for a listing"""
#     id: str
#     """ arXiv ID or IDV of article"""
    
#     listingType: str
#     """What happened to the article on this day.

#     Currently one of new, rep, wdr, cross"""


# class SingleDayListingResponse(Protocol):
#     """Response when a single day is included"""

#     listings: List[ListingItem]
#     """Listings that were requested"""
    
#     pubdate: date
#     """Date all of the listings were on"""
    
#     count: int
#     """Count of total number of listnigs for the date"""

SingleDayListingResponse = TypedDict('SingleDayListingResponse',
                                     {'listings':List[ListingItem],
                                      'pubdate': date,
                                      'count': int })


ListingResponse = TypedDict('ListingResponse',
                            {'listings':List[ListingItem],
                             'pubdates': List[Tuple[date,int]],
                             'count': int })
                            
# class ListingResponse(Protocol):
#     """Resopnce when multiple days could be included"""

#     listings: List[ListingItem]
#     """Listings that were requested"""
    
#     dates: List[Tuple[date,int]]
#     """Dates with their zero based offsets into the listings"""
    
#     count: int
#     """Count of total number of listings for period"""


class ListingService:
    """Class for arXiv document listings."""
 #   __metaclass__ = ABCMeta

    @classmethod
    def version(self) -> str:
        return "0.2"

     #   @abstractmethod
    def list_articles_by_year(self,
                              archiveOrCategory: str,
                              year: int,
                              skip: int,
                              show: int,
                              if_modified_since: Optional[str]=None) -> ListingResponse:
        raise NotImplementedError

 #   @abstractmethod
    def list_articles_by_month(self,
                               archiveOrCategory: str,
                               year: int,
                               month: int,
                               skip: int,
                               show: int,
                               if_modified_since: Optional[str]=None) -> ListingResponse:
        raise NotImplementedError

#    @abstractmethod
    def list_new_articles(self,
                          archiveOrCategory: str,
                          skip: int,
                          show: int,
                          if_modified_since: Optional[str]=None) -> SingleDayListingResponse:
        """ Gets listings for the most recent publish.

        Notice that this returns a single DateListings, not a list of them."""
        raise NotImplementedError

#    @abstractmethod
    def list_pastweek_articles(self,
                               archiveOrCategory: str,
                               skip: int,
                               show: int,
                               if_modified_since: Optional[str]=None) -> ListingResponse:
        raise NotImplementedError

