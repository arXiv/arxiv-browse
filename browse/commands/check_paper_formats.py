"""Checks that the paper format in the DB matches what is in the FS.

This script checks the arXiv_metadata.source_format plausibly matches the file extension of the source files."""
from flask import  Blueprint
from sqlalchemy import or_
import json

import click

from browse.domain.identifier import Identifier
from browse.services.database import db
from browse.services.database.models import Metadata
from browse.services.dissemination import get_article_store, ArticleStore
from browse.services.documents.format_codes import formats_from_source_flag
from browse.services.object_store import FileObj
bp = Blueprint("check", __name__)

@bp.cli.command("paper_formats")
@click.argument("yymm")
def check_paper_formats(yymm: str) -> None:
    """Checks formats for yymm."""
    query = (db.session.query(Metadata.paper_id, Metadata.version,
                            Metadata.source_format,
                            Metadata.source_flags, Metadata.source_size)
                .filter(or_(Metadata.paper_id.like(f"%/{yymm}%"),
                            Metadata.paper_id.like(f"{yymm}.%"))))

    rows = query.all()
    if not rows:
        print(f"No rows found.")
    a_store: ArticleStore = get_article_store()
    results = {}
    for row in rows:
        paper_id, version, src_fmt, source_flags, source_size = row[0], row[1], row[2], row[3], row[4]
        print(f"Doing {paper_id}v{version}")
        result = {"paper_id": paper_id, "version":version, "db_source_format":src_fmt, "db_source_flags":source_flags, "db_source_size":source_size}
        results[f"{paper_id}v{version}"] = result
        arxiv_id = Identifier(f"{paper_id}v{version}")
        src = a_store.get_source(arxiv_id)
        if isinstance(src, str):
            result["src_file_problem"] = src
            continue
        elif isinstance(src, tuple):
            result["src_file_problem"] = ""
            result["source_flag_only_formats"] = formats_from_source_flag(source_flags)

            fileobj, fmt, docmeta, version = src
            if isinstance(fileobj, FileObj):
                result["sizes_match"] = source_size == fileobj.size
                result["fs_size"] = fileobj.size
                result["fs_name"] = fileobj.name
                result["dissemination_formats"] = a_store.get_dissemination_formats(docmeta, None, fileobj)
                result["formats_match"] = result["dissemination_formats"] == result["source_flag_only_formats"]
            else:
                result["src_file_problem"] = "MULTIPLE FILES"
        else:
            result["src_file_problem"] = "UNKNOWN SOURCE FORMAT TYPE {type(src)}"
            continue

    with open("paper_formats.json", "w") as fh:
        json.dump(results, fh, indent=4, default=str)
