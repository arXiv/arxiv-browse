import os
from typing import Callable, Optional, List
import logging
from datetime import datetime, timedelta, timezone
import sqlite3
import pathspec
import argparse
import re

from digester import digest_from_filepath

GIT_DIR = [".git/"]
DEFAULT_IGNORES = """*~
"""


class WalkerReport(object):
    def __init__(self):
        self.last_report = datetime.now()
        self.quiescent = timedelta(seconds=5)
        self.report_format = "{} files visited."
        pass

    def fileop_progress_logging(self, n_files) -> None:
        if (n_files % 1000) == 0:
            this_time = datetime.now()
            if this_time - self.last_report > self.quiescent:
                logging.info(self.report_format.format(n_files))
                self.last_report = this_time
                pass
            pass
        pass


def canonicalize_filepath(filepath: str) -> str:
    if filepath.startswith("./"):
        filepath = filepath[2:]
        pass
    return filepath


def walk_docs(doc_root: str) -> List[dict]:
    ignore_file = os.path.join(doc_root, ".gitignore")
    if os.path.exists(ignore_file):
        logging.info(f"{ignore_file} used, ovreriding default.")
        with open(ignore_file, encoding="ascii") as ignore_fd:
            spec_text = ignore_fd.read()
            pass
        pass
    else:
        spec_text = DEFAULT_IGNORES
        pass
    ignores = GIT_DIR + spec_text.splitlines()
    logging.debug("ignore " + repr(ignores))
    ignore_spec = pathspec.GitIgnoreSpec.from_lines(ignores)

    local_files = []
    progress = WalkerReport()
    for dirpath, dirnames, filenames in os.walk(doc_root):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(filepath, doc_root)
            if ignore_spec.match_file(filepath):
                logging.debug(f"Skip {rel_path}")
                continue
            try:
                digested = digest_from_filepath(filepath)
                file_stat = os.stat(filepath)
                entry = {
                    "filepath": canonicalize_filepath(rel_path),
                    "digest": digested,
                    "size": file_stat.st_size,
                    "modified_at": datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc).isoformat(),
                    "gcp": None,
                }
                local_files.append(entry)
                progress.fileop_progress_logging(len(local_files))
                pass
            except PermissionError:
                pass
            except IOError:
                pass
            pass
        pass
    local_files.sort(key=lambda elem: elem['filepath'])
    return local_files


def doc_root_to_table_name(doc_root: str) -> str:
    return "doc_" + re.sub('\W|^(?=\d)', '_', doc_root)


COLUMNS_LOCAL = ["filepath", "digest", "size", "modified_at"]
COLUMNS_REMOTE = ["blob", "remote_digest"]
COLUMN_DESC = {
    "filepath": "varchar primary key",
    "digest": "char(64)",
    "size": "number",
    "modified_at": "char(30)",
    "blob": "varchar",
    "remote_digest": "varchar",
}

def open_db(db_url, table_name):
    conn = sqlite3.connect(db_url)
    cur = conn.cursor()
    #
    columns = ",".join(["{} {}".format(col_name, COLUMN_DESC[col_name]) for col_name in COLUMNS_LOCAL + COLUMNS_REMOTE])
    sql = 'create table if not exists {table_name} ({columns})'.format(table_name=table_name, columns=columns)
    logging.debug(sql)
    cur.execute(sql)
    cur.close()
    return conn


def update_doc_db(doc_root: str, metas: List[dict], db_url: str):
    table_name = doc_root_to_table_name(doc_root)
    conn = open_db(db_url, table_name)

    cursor = conn.cursor()
    cursor.execute("begin")
    columns = ",".join(COLUMNS_LOCAL)
    stmt1 = f"insert or replace into {table_name} ({columns}) values (?, ?, ?, ?)"
    for meta in metas:
        cursor.execute(stmt1, [meta.get(attr) for attr in COLUMNS_LOCAL])
        pass
    cursor.execute("commit")
    cursor.close()
    conn.close()


def compare_doc_db(doc_root: str, metas: List[dict], db_url: str):
    table_name = doc_root_to_table_name(doc_root)
    conn = open_db(db_url, table_name)

    cursor = conn.cursor()
    cursor.execute("begin")
    columns = ",".join(COLUMNS_LOCAL)
    stmt1 = f"select {columns} from {table_name} where filepath=?"
    for meta in metas:
        cursor.execute(stmt1, [meta["filepath"]])
        known_meta_row = None
        try:
            known_meta_row = cursor.fetchone()
        except:
            pass
        if known_meta_row:
            known_meta = {attr: value for attr, value in zip(COLUMNS_LOCAL, known_meta_row)}
            if meta["digest"] != known_meta["digest"]:
                # modified file
                logging.info(repr(meta))
                pass
            pass
        else:
            # New file
            logging.info(repr(meta))
            pass
        pass
    cursor.execute("commit")
    cursor.close()
    conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("doc_root", help="Root directory for the file scan")
    parser.add_argument("db_url", help="sqlite3 db file path")
    parser.add_argument("-v", "--verify", action="store_true", help="verify files")
    parser.add_argument("-u", "--update", action="store_true", help="update digests")
    args = parser.parse_args()

    if args.verify:
        docs = walk_docs(args.doc_root)
        compare_doc_db(args.doc_root, docs, args.db_url)
        exit(0)
        pass

    if args.update:
        docs = walk_docs(args.doc_root)
        update_doc_db(args.doc_root, docs, args.db_url)
        exit(0)
        pass

    parser.print_help()
    pass
