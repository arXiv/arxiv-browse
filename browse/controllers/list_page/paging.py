"""Paginiation links for listing pages."""


import math
from typing import Any, Dict, List, Union

from flask import url_for


def paging(count: int, skipn: int, shown: int, context: str, subcontext: str) \
        -> List[Dict[str, Union[str, int]]]:
    """Get paging links."""
    bumper_pages = 3  # num of buffer pages on each side of current
    total_pages = math.floor(count-1 / (skipn+1))+1  # total number of pages

    slots_in_paging = 2 * bumper_pages + 5
    # Maximum number of slots for elements in the pages sections:
    # 2*bumper_pages + start + end + 2*dots + current

    def page_dict(n: int, nolink: bool = False) -> Dict[str, Union[str, int]]:
        txt = f'{n + 1}-{min(count, n + shown)}'
        if nolink:
            return {'nolink': txt}
        else:
            return {'skip': n,
                    'txt': txt,
                    'url': url_for('.list_articles',
                                   context=context,
                                   subcontext=subcontext,
                                   skip=n,
                                   show=shown)}

    page_starts = range(0, count, shown) # Paper indexs for each page start

    if total_pages < slots_in_paging:
        # just show all numbers number of pages is less than slots
        return [page_dict(n) for n in page_starts if n < skipn] + \
            [{'nolink': skipn}] + \
            [page_dict(n) for n in page_starts if n > skipn]

    page_links: List[Dict[str, Any]] = []
    if skipn >= shown:  # Not on first page?
        page_links = [page_dict(0)]

    prebumper = [n for n in page_starts if n >= (
        skipn - shown * bumper_pages) and n < skipn and n > 0]

    if prebumper:
        if prebumper[0] <= shown * bumper_pages:
            # Case of no dots between first and prebumper
            page_links = page_links + \
                [page_dict(n) for n in prebumper]
        else:
            page_links.append({'nolink': '...'})
            page_links = page_links + \
                [page_dict(n) for n in prebumper]

    page_links.append(page_dict(skipn, True))  # non-link for current page

    postbumper = [n for n in page_starts if n > skipn and n <=
                  (skipn + shown * bumper_pages)]
    if postbumper:
        page_links = page_links + \
            [page_dict(n) for n in postbumper]
        if postbumper[-1] < page_starts[-1]:
            # Case of need dots between postbumper and last
            page_links.append({'nolink': '...'})

    if postbumper and postbumper[-1] < page_starts[-1]:
        page_links.append(page_dict(page_starts[-1]))  # last

    return page_links
