from typing import List, Optional

from sqlite3 import Connection

def grep_f_count(filename: str, query: str) -> Optional[int]:
    """Like counting lines from grep -F "query" filename"""
    try:
        with open(filename) as search_file:
            file_lines: List[str] = [line.strip() for line in search_file]
        return sum(map(lambda ln: 1 if query in ln else 0, file_lines))
    except OSError:
        print('cannot open', filename)
        return None


def execute_sql_files(sql_files: List[str], conn: Connection) -> None:
    """Populate test db by executing the sql_files"""

    def exec_sql(file: str) -> None:
        query = open(file, 'r').read()
        conn.executescript(query)
        conn.commit()

    list(map(exec_sql, sql_files))
    conn.close()
