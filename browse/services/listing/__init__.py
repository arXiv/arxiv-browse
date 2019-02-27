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

from typing import Optional

from browse.domain.listing import NewResponse, ListingResponse


class ListingService:
    """Class for arXiv document listings."""

    @classmethod
    def version(cls) -> str:
        """Version."""
        return "0.2"

    def list_articles_by_year(self,
                              archiveOrCategory: str,
                              year: int,
                              skip: int,
                              show: int,
                              if_modified_since: Optional[str] = None) -> ListingResponse:
        """Get listing items for a whole year.

        if_modified_since is the if_modified_since header value passed by the web client
        It should be in RFC 1123 format.
        """
        raise NotImplementedError

    def list_articles_by_month(self,
                               archiveOrCategory: str,
                               year: int,
                               month: int,
                               skip: int,
                               show: int,
                               if_modified_since: Optional[str] = None) -> ListingResponse:
        """Get listings for a month.

        if_modified_since is the if_modified_since header value passed by the web client
        It should be in RFC 1123 format.
        """
        raise NotImplementedError

    def list_new_articles(self,
                          archiveOrCategory: str,
                          skip: int,
                          show: int,
                          if_modified_since: Optional[str] = None) -> NewResponse:
        """Gets listings for the most recent announcement/publish.

        if_modified_since is the if_modified_since header value passed by the web client
        It should be in RFC 1123 format.
        """
        raise NotImplementedError

    def list_pastweek_articles(self,
                               archiveOrCategory: str,
                               skip: int,
                               show: int,
                               if_modified_since: Optional[str] = None) -> ListingResponse:
        """Gets listings for the 5 most recent announcement/publish.

        if_modified_since is the if_modified_since header value passed by the web client
        It should be in RFC 1123 format.
        """
        raise NotImplementedError
