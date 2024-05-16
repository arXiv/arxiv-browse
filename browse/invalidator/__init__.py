import re
from typing import Optional, List

from arxiv.identifier import Identifier, STANDARD as MODERN_ID, OLD_STYLE, _archive, _category


PS_CACHE_OLD_ID = re.compile(r'(%s)\/[^\/]*\/\d*\/(\d{2}[01]\d{4}(v\d*)?)' % f'{_archive}|{_category}')
"EX /ps_cache/hep-ph/pdf/0511/0511005v2.pdf"


def _paperid(name: str) -> Optional[Identifier]:
    if match := MODERN_ID.search(name):
        return Identifier(match.group("arxiv_id"))
    if match := PS_CACHE_OLD_ID.search(name):
        return Identifier(match.group(1) + "/" + match.group(2))
    else:
        return None


def _purge_urls(bucket: str, name: str, paperid: Identifier) -> List[str]:
    # Since it is not clear if this is the current file or an older one
    # invalidate both the versioned URL and the un-versioned current URL
    if name.startswith('/ftp/') or name.startswith("/orig/"):
        if name.endswith(".abs"):
            return [f"arxiv.org/abs/{paperid.idv}", f"arxiv.org/abs/{paperid.id}"]
        else:
            return [f"arxiv.org/e-print/{paperid.idv}", f"arxiv.org/e-print/{paperid.id}",
                    f"arxiv.org/src/{paperid.idv}", f"arxiv.org/src/{paperid.id}"]
    elif "/pdf/" in name:
        return [f"arxiv.org/pdf/{paperid.idv}", f"arxiv.org/pdf/{paperid.id}"]
    elif '/html/' in name:
        # Note this does not invalidate any paths inside the html.tgz
        return [f"arxiv.org/html/{paperid.idv}", f"arxiv.org/html/{paperid.id}",
                # Note needs both with and without trailing slash
                f"arxiv.org/html/{paperid.idv}/", f"arxiv.org/html/{paperid.id}/"]
    elif '/ps/' in name:
        return [f"arxiv.org/ps/{paperid.idv}", f"arxiv.org/ps/{paperid.id}"]
    elif '/dvi/' in name:
        return [f"arxiv.org/dvi/{paperid.idv}", f"arxiv.org/dvi/{paperid.id}"]
    else:
        return []
