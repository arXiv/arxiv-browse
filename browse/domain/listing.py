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
