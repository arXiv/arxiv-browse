import re
from typing import Optional, List, Tuple

import requests
from arxiv.identifier import Identifier, STANDARD as MODERN_ID, _archive, _category
from google.api_core import retry

PS_CACHE_OLD_ID = re.compile(r'(%s)\/[^\/]*\/\d*\/(\d{2}[01]\d{4}(v\d*)?)' % f'{_archive}|{_category}')
"EX /ps_cache/hep-ph/pdf/0511/0511005v2.pdf"

import logging
log = logging.getLogger(__name__)

def _paperid(name: str) -> Optional[Identifier]:
    if match := MODERN_ID.search(name):
        return Identifier(match.group("arxiv_id"))
    if match := PS_CACHE_OLD_ID.search(name):
        return Identifier(match.group(1) + "/" + match.group(2))
    else:
        return None


def purge_urls(key: str) -> Optional[Tuple[Identifier, List[str]]]:
    """

    Parameters
    ----------
    key: GS key should not start with a / ex. `ftp/arxiv/papers/1901/1901.0001.abs`

    paperid: The paper ID this is related to

    Returns
    -------
    List of paths to invalidate at fastly. Ex `["arxiv.org/abs/1901.0001"]`
    """
    # Since it is not clear if this is the current file or an older one
    # invalidate both the versioned URL and the un-versioned current URL
    paperid = _paperid(key)
    if paperid is None:
        return None

    if key.startswith('/ftp/') or key.startswith("/orig/"):
        if key.endswith(".abs"):
            return paperid, [f"arxiv.org/abs/{paperid.idv}", f"arxiv.org/abs/{paperid.id}"]
        else:
            return paperid, [f"arxiv.org/e-print/{paperid.idv}", f"arxiv.org/e-print/{paperid.id}",
                    f"arxiv.org/src/{paperid.idv}", f"arxiv.org/src/{paperid.id}"]
    elif "/pdf/" in key:
        return paperid, [f"arxiv.org/pdf/{paperid.idv}", f"arxiv.org/pdf/{paperid.id}"]
    elif '/html/' in key:
        # Note this does not invalidate any paths inside the html.tgz
        return paperid, [f"arxiv.org/html/{paperid.idv}", f"arxiv.org/html/{paperid.id}",
                # Note needs both with and without trailing slash
                f"arxiv.org/html/{paperid.idv}/", f"arxiv.org/html/{paperid.id}/"]
    elif '/ps/' in key:
        return paperid, [f"arxiv.org/ps/{paperid.idv}", f"arxiv.org/ps/{paperid.id}"]
    elif '/dvi/' in key:
        return paperid, [f"arxiv.org/dvi/{paperid.idv}", f"arxiv.org/dvi/{paperid.id}"]
    else:
        return paperid, []


class Invalidator:
    def __init__(self, fastly_url: str, fastly_api_token: str, always_soft_purge: bool=False, dry_run: bool=False) -> None:
        if fastly_url.endswith("/"):
            self.fastly_url = fastly_url[:-1]
        else:
            self.fastly_url = fastly_url
        self.fastly_api_token = fastly_api_token
        self.always_soft_purge = always_soft_purge
        self.dry_run = dry_run

    @retry.Retry()
    def invalidate(self, arxiv_url: str, paperid: Identifier, soft_purge: bool=False) -> None:
        headers = {"Fastly-Key": self.fastly_api_token}
        if self.always_soft_purge or soft_purge:
            headers["fastly-soft-purge"] = "1"

        url = f"{self.fastly_url}/{arxiv_url}"

        if self.dry_run:
            log.info(f"{paperid.idv} DRY_RUN: Would have requested '{url}'")
            return

        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            log.info(f"{paperid.idv} purged {arxiv_url}", )
            return
            log.error(f"{paperid.idv} purge failed. GET req to {url} failed: {resp.status_code} {resp.text}")
            return
        else:
            resp.raise_for_status()


def invalidate_for_gs_change(bucket: str, key: str, invalidator: Invalidator) -> None:
    tup = purge_urls(key)
    if not tup:
        log.info(f"No purge: gs://{bucket}/{key} not related to an arxiv paper id")
        return
    paper_id, paths = tup
    if not paths:
        log.info(f"No purge: gs://{bucket}/{key} Related to {paper_id} but no paths")
        return
    for path in paths:
            try:
                invalidator.invalidate(path, paper_id)
            except Exception as exc:
                log.error(f"Purge failed: {path} failed {exc}")
