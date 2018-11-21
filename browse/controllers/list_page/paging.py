"""Paginiation links for listing pages"""


from typing import Any, Dict, List, Optional, Tuple, cast
import math
from flask import current_app, request, url_for


def paging(count: int, skipn: int, shown: int, context: str, subcontext: str) -> List[Dict[str, Any]]:
    """ Get paging links. """

    B = 3  # num of buffer pages on each side of current
    L = math.floor(count-1 / (skipn+1))+1  # total number of pages
    S = 2 * B + 2 * 2 + 1  # number of total links in the pages sections:
    #  2*buffer + 2*(first number + dots) + current

    def page_dict(n: int, nolink: bool = False)->Dict[Any, Any]:
        txt = str(n+1)+'-'+str(min(count, n+shown))
        if nolink:
            return {'nolink': txt}
        else:
            return {'skip': n,
                    'txt': txt,
                    'url': url_for('.list_articles',
                                   context=context,
                                   subcontext=subcontext,
                                   skip=n,
                                   show=shown)
                    }

    R = range(0, count, shown)

    if L < S:  # just show all numbers number of pages is less than slots
        return [page_dict(n) for n in R if n < skipn] + \
            [{'nolink': skipn}] + [page_dict(n) for n in R if n > skipn]

    page_links: List[Dict[str, Any]] = []
    if skipn >= shown:  # Not on first page?
        page_links = [page_dict(0)]

    prebuffer = [n for n in R if n >= (
        skipn - shown * B) and n < skipn and n > 0]

    # No dots between first and prebuffer
    if prebuffer:
        if prebuffer[0] <= shown * B:
            page_links = page_links + \
                [page_dict(n) for n in prebuffer]
        else:
            page_links.append({'nolink': '...'})
            page_links = page_links + \
                [page_dict(n) for n in prebuffer]

    page_links.append(page_dict(skipn, True))  # current page

    postbuffer = [n for n in R if n > skipn and n <= (skipn + shown * B)]
    if postbuffer:
        page_links = page_links + \
            [page_dict(n) for n in postbuffer]
        if postbuffer[-1] < R[-1]:  # Need dots between postbuffer and last
            page_links.append({'nolink': '...'})

    if postbuffer and postbuffer[-1] < R[-1]:
        page_links.append(page_dict(R[-1]))  # last
    return page_links
