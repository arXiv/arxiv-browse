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
from typing import List, Optional, Tuple
from datetime import datetime, date
import re
import os

from browse.services.database.models import db
from browse.services.database.models import Metadata


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
                               if_modified_since: Optional[str]=None) -> Tuple[List[str], int]:
        raise NotImplementedError

    
 #   @abstractmethod
    def list_articles_by_month(self,
                               archiveOrCategory: str,
                               year: int,
                               month: int,
                               skip: int,
                               show: int,
                               if_modified_since: Optional[str]=None) -> Tuple[List[str], int]:
        raise NotImplementedError

#    @abstractmethod
    def list_new_articles(self,
                          archiveOrCategory: str,
                          skip: int,
                          show: int,
                          if_modified_since: Optional[str]=None) -> Tuple[List[str], int]:
        raise NotImplementedError

#    @abstractmethod
    def list_pastweek_articles(self,
                               archiveOrCategory: str,
                               skip: int,
                               show: int,
                               if_modified_since: Optional[str]=None) -> Tuple[List[str], int]:
        raise NotImplementedError


_archive_re_str = r'([a-z\-])'
_cat_re_str = r'(\.([A-Z]{2}))'
archive_regex = re.compile(f'{_archive_re_str}')
archive_or_category_regex = re.compile(f'{_archive_re_str}{_cat_re_str}?')

    

# class LegacyListingFilesService(ListingService):
#     """Implments article listing for the legacy listings files.

#     This expects a directory with the structure:
#     $ARCHIVE/listings/
#                       $YYMM
#                       lastupdate
#                       new
#                       new.$SUBJECT
#                       pastweek
#                       pastweek.$SUBJECT

#     The directory arxiv/listings is not read from.
# """

#     def __init__(self, base_dir: str) ->None:
#         self.base_dir = base_dir

#     def list_articles_by_month(self,
#                                archive: str,
#                                year: int,
#                                month: int,
#                                skip: int,
#                                show: int,
#                                if_modified_since: Optional[str]=None) -> Tuple[List[str], int]:
#         if not archive:
#             raise ValueError('archive required')
#         if not year:
#             raise ValueError('year required')
#         if not month:
#             raise ValueError('month required')
#         if month < 1 or month > 12:
#             raise ValueError('month must be between 1 and 12')
#         if skip < 0:
#             raise ValueError('skip must be postive integer')
#         if show < 1:
#             raise ValueError('show must be greater than 1')

#         # Deal with archiveOrCategory carefully, it may be from a web
#         # client. We combine errors about invalid archive with no file
#         # found to obscure what part of the system is being probed
#         amtc = re.match(archive_regex, archive)
#         if not amtc or not amtc.group(1):
#             raise ValueError('No listing found')

#         l_file_name = self._listing_file(actc.group(1), year, month)
#         if not os.path.isfile(l_file_name):
#             raise ValueError('No listing found')

#         raise NotImplementedError
#         # extras = {}
#         # with open(l_file_name, 'rt') as l_f:
#         #     line = 'start'
#         #     while line and not line.startswith('\\'):
#         #         line = l_f.readline()
#         #     #Now just past first \\ of first entry block



#     def _listing_file(self,
#                       archive: str,
#                       year: int,
#                       month: int):
#         """Returns listing file name"""
#         return '%s/%02d%02d' % (self._listing_dir(archive), year, month)

#     def _listing_dir(self, archvie: str) ->str:
#         return f'{self.base_dir}/{archive}/listings'

#     def _file_name(self,
#                    archive: str,
#                    subject: Optional[str]=None,
#                    time_period: str,
#                    yymm: bool):
#         if time_period in ['pastweek', 'new']:
#             if subject:
#                 listingFile = f'{time_period}.{subject}'
#             else:
#                 listingFile = f'{time_period}'
#             return f'{self.base_dir}/{archive}/listings/{listingFile}'
#         elif time_period == 'pastyear':
#             raise NotImplementedError(
#                 'time period of pastyear not yet implemented')
#         elif
#         else:
#             if yymm:
#                 return f'{self.base_dir}/{archive}/listings/{time_period}'
#             else
