"""Return types for listing service."""

from datetime import date
from typing import List, Tuple

from mypy_extensions import TypedDict


ListingItem = TypedDict('ListingItem',
                        {'id': str,
                         'listingType': str,
                         'primary': str})
"""A single item for a listing.

The id is the arXiv ID and may be an idv.

The listing type is one of 'new,'rep','cross','wdr','jref'. These
would be extended with any new types of actions/events that can happen
in the arXiv system.

primary is the primary category of the article.

"""


ListingResponse = TypedDict('ListingResponse',
                            {'listings': List[ListingItem],
                             'pubdates': List[Tuple[date, int]],
                             'count': int,
                             'expires': str})
"""listings is the list of items a time period.

pubdates are the dates of publications. The int is the number of items
published on the associated date.

count is the count of all the items in the listing for the query.

expires is the time at which this data may no longer be cached. It
should be the sort of datetime that could go in an HTTP Expires response
header. It must be in rfc-1123 format ex. Wed, 22 Oct 2008 10:55:46 GMT
The timezone for this expires should be when the cache expires and does not need
to be the timezone of the listing service, listing client or web client.

Why not just do listing: List[Tuple[date,List[ListingItem]}} ?
Because pastweek needs to support counts for the days and needs to be
able to support skip/show.
"""

NewResponse = TypedDict('NewResponse',
                        {'listings': List[ListingItem],
                         'new_count': int,
                         'cross_count': int,
                         'rep_count': int,
                         'announced': date,
                         'submitted': Tuple[date, date],
                         'expires': str})
"""
listings is the list of items for the most recent publish cycle.

announced is the date of the most recent publish cycle.

new_count is the count of new the items in the listing for the query.
rep_count is the count of rep the items in the listing for the query.
cross_count is the count of cross the items in the listing for the query.

submitted is the start date of when these items were submitted and the end date.

expires is the time at which this data may no longer be cached. It
should be the sort of datetime that could go in an HTTP Expires response
header. It must be in rfc-1123 format ex. Wed, 22 Oct 2008 10:55:46 GMT
The timezone for this expires should be when the cache expires and does not need
to be the timezone of the listing service, listing client or web client.

"""


NotModifiedResponse = TypedDict('NotModifiedResponse',
                                {'not_modified': bool,
                                 'expires': str})
"""
Listing response that indicates that the listing has not been modified since
the date in the if-modified-since parameter.

expires must be in rfc-1123 format ex. Wed, 22 Oct 2008 10:55:46 GMT
The timezone for this expires should be when the cache expires and does not need
to be the timezone of the listing service, listing client or web client.

"""



MonthCount = TypedDict('MonthCount',
                        {'year': str,
                         'month': str,
                         'new': int,
                         'cross': int})
"""A single month's count for an archive.

year is the year the listing is for.

month is the month the listing is for.

new is the count of new listings for that month.

cross is the count of crosses for that month.

rep is the count of replaced for that month.

"""


ListingCountResponse = TypedDict('ListingCountResponse',
                                 {'month_counts': List[MonthCount],
                                  'new_count': int,
                                  'cross_count': int})
"""Response with the counts for an archive for a given year.

month_counts are counts for individual months.

new_count is the count of new articles for the year.

cross_count is the count of cross articles for the year.

rep_count is the count of replaced articles for the year.
"""
