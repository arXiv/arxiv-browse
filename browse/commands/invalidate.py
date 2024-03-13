"""Invalidates pages in the CDN."""
import re
from typing import Optional, Iterable, List

import click
from flask import Blueprint
from google.api_core import retry

from google.cloud import compute_v1
from sqlalchemy.orm import scoped_session

from arxiv.db import session
from arxiv.db.models import NextMail

bp = Blueprint("invalidate", __name__)


@bp.cli.command(short_help="invalidates CDN for PDFs from a mailing")
@click.argument("mailings",
                # help="Invalidate all PDFs from these mailings. May have more than one. Format YYMMDD.",
                nargs=-1)
@click.option("--project", default="arxiv-production")
@click.option("--cdn", default="browse-arxiv-org-load-balancer2",
              help="Url-map of the CDN. Find it with `gcloud compute url-maps list`"
              )
@click.option("-n", "--dry-run", "dry_run", is_flag=True,
              help="Only display what paths would be invalidated.",
              default=False)
@click.option("-v", is_flag=True,
              help="Verbose.",
              default=False)
def invalidate_mailings(project: str, cdn: str, mailings: List[str], dry_run: bool, v: bool) -> None:
    """Invalidate CDN for PDFs in a mailing."""
    if not mailings:
        raise ValueError("mailing must not be empty.")

    mailings = [date for date in mailings if date]
    if any([not re.match(r'\d{6}', mailing) for mailing in mailings]):
        raise ValueError("mailings values must be like '230130'")

    paths: List[str] = []
    session: scoped_session = session
    for mailing in mailings:
        if v:
            print(f"About to query for {mailing}")
        papers = (session.query(NextMail.paper_id, NextMail.version)
                  .filter(NextMail.mail_id == int(mailing)))

        nn = 0;
        for paper_id, version in papers.all():
            paths.append(f"/pdf/{paper_id}.pdf")
            paths.append(f"/pdf/{paper_id}v{version}.pdf")
            nn = nn + 1

        if v:
            print(f"For {mailing} found {nn} papers.")

    if v:
        print(f"{len(paths)} paths to invalidate. "
              "Two for each paper. One with version and one without.")

    _invalidate(project, cdn, paths, dry_run=dry_run, v=v)


def _invalidate(proj: str, cdn: str, paths: List[str], dry_run: bool = False, v: bool = False) -> None:
    """Invalidates `paths` on `cdn` in `proj`."""
    paths.sort()
    if v:
        for path in paths:
            print(path)

    if dry_run:
        print("Skipping actual invalidate due to dry_run")
    else:
        if v:
            print("Starting invalidation of paths in CDN.")
        client = compute_v1.UrlMapsClient()
        for path in paths:
            request = compute_v1.InvalidateCacheUrlMapRequest(
                project=proj,
                url_map=cdn,
                cache_invalidation_rule_resource=
                compute_v1.CacheInvalidationRule(
                    # host="*",
                    path=path),
            )
            _invalidate_req(client, request)
            if v:
                print(f"Invalidated {path}.")


def _exception_pred(ex: Exception) -> bool:
    return bool(ex and
                (isinstance(ex, BaseException)
                 or "rate limit exceeded" in str(ex).lower()))


@retry.Retry(predicate=_exception_pred)
def _invalidate_req(client: compute_v1.UrlMapsClient, request: compute_v1.InvalidateCacheUrlMapRequest) -> None:
    client.invalidate_cache_unary(request=request)
