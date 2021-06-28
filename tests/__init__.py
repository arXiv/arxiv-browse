"""Test utility functions."""
from typing import List, Optional
import os
import glob

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


def comment(s):
    return not s or s.startswith('--') or s.startswith('/*')

def execute_sql_files(sql_files: List[str], engine: Engine) -> None:
    """Populate test db by executing the sql_files."""
    def exec_sql(filename: str) -> None:
        lnum=0
        try:
            with open(filename) as sql_file:
                for ln, line in enumerate([line.strip() for line in sql_file]):
                    lnum = ln
                    if not comment(line):
                        engine.execute(text(line))
        except Exception as err:
            raise Exception( f"Error at line {filename}:{lnum}") from err
    list(map(exec_sql, sql_files))


def path_of_for_test(rel_path: str) -> str:
    """Returns absolute path of rel_path, assuming rel_path is under tests/."""
    return os.path.join(os.path.dirname(__file__), rel_path)

def foreign_key_check(engine, check_on:bool ):
    if check_on:
        if 'sqlite' in str(engine.url):
            engine.execute(text('PRAGMA foreign_keys = ON;'))
        else:
            engine.execute(text('SET FOREIGN_KEY_CHECKS = 1;'))
    else:
        if 'sqlite' in str(engine.url):
            engine.execute(text('PRAGMA foreign_keys = OFF;'))
        else:
            engine.execute(text('SET FOREIGN_KEY_CHECKS = 0;'))

def populate_test_database(drop_and_create: bool, models):
    """Initialize the browse tables."""
    if drop_and_create:
        foreign_key_check(models.db.engine, False)
        models.db.drop_all()
        models.db.session.commit()
        foreign_key_check(models.db.engine, True)
        models.db.create_all()
        models.db.session.commit()

    # Member institution data
    models.db.session.add(
        models.MemberInstitution(
            id=1, name='Localhost University', label='Localhost University'),
    )
    models.db.session.add(models.MemberInstitutionIP(
        id=1, sid=1, start=2130706433, end=2130706433, exclude=0))

    # Intentionally add another insitution for the same loopback IP as above
    models.db.session.add(
        models.MemberInstitution(
            id=2, name='Loopback University', label='Loopback University'),
    )
    models.db.session.add(models.MemberInstitutionIP(
        id=2, sid=2, start=2130706433, end=2130706433, exclude=0))

    models.db.session.commit()
    sql_files: List[str] = glob.glob('./tests/data/db/sql/*.sql')
    foreign_key_check(models.db.engine, False)
    execute_sql_files(sql_files, models.db.engine)


    
