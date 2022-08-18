"""Test utility functions."""
import os
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.engine.base import Engine


def grep_f_count(filename: str, query: str) -> Optional[int]:
    """Like counting lines from grep -F "query" filename."""
    try:
        with open(filename) as search_file:
            file_lines: List[str] = [line.strip() for line in search_file]
        return sum(map(lambda ln: 1 if query in ln else 0, file_lines))
    except OSError:
        print('cannot open', filename)
        return None


def execute_sql_files(sql_files: List[str], engine: Engine) -> None:
    """Populate test db by executing the sql_files."""
    def exec_sql(filename: str) -> None:
        with open(filename) as sql_file:
            file_lines: List[str] = [line.strip() for line in sql_file]
        list(map(lambda ln: engine.execute(text(ln)), file_lines))

    list(map(exec_sql, sql_files))


def path_of_for_test(rel_path: str) -> str:
    """Returns absolute path of rel_path, assuming rel_path is under tests/."""
    return os.path.join(os.path.dirname(__file__), rel_path)
