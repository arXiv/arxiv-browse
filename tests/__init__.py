"""Test utility functions."""
from datetime import datetime, timezone
import glob
from datetime import datetime, timezone
import os
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.engine.base import Engine

from arxiv.db.models import Metadata


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
            with engine.connect() as conn:
                with open(filename) as sql_file:
                    for ln, line in enumerate([line.strip() for line in sql_file]):
                        lnum = ln
                        if not comment(line):
                            conn.execute(text(line))

                conn.commit()
        except Exception as err:
            raise Exception( f"Error at line {filename}:{lnum}") from err
    list(map(exec_sql, sql_files))


def path_of_for_test(rel_path: str) -> str:
    """Returns absolute path of rel_path, assuming rel_path is under tests/."""
    return os.path.join(os.path.dirname(__file__), rel_path)

def foreign_key_check(engine, check_on:bool ):
    if check_on:
        if 'sqlite' in str(engine.url):
            with engine.connect() as conn:
                conn.execute(text('PRAGMA foreign_keys = ON;'))
        else:
            with engine.connect() as conn:
                conn.execute(text('SET FOREIGN_KEY_CHECKS = 1;'))
    else:
        if 'sqlite' in str(engine.url):
            with engine.connect() as conn:
                conn.execute(text('PRAGMA foreign_keys = OFF;'))
        else:
            with engine.connect() as conn:
                conn.execute(text('SET FOREIGN_KEY_CHECKS = 0;'))

def _populate_latexml_test_data (db, latexml_engine: Engine):
    db.LaTeXMLBase.metadata.drop_all(bind=latexml_engine)
    db.LaTeXMLBase.metadata.create_all(bind=latexml_engine)

    dt = datetime(2024, 1, 30, 15, 0, 0)
    dt = dt.replace(tzinfo=timezone.utc)

    doc1 = {
        'paper_id': '0906.2112',
        'document_version': 3,
        'conversion_status': 1,
        'latexml_version': 'test_latexml_version',
        'tex_checksum': 'test_checksum',
        'conversion_start_time': 0,
        'conversion_end_time': 1,
        'publish_dt': datetime(2024, 1, 1, 0, 0, 0)
    }

    doc2 = {
        'paper_id': '2303.00763',
        'document_version': 1,
        'conversion_status': 1,
        'latexml_version': 'test_latexml_version',
        'tex_checksum': 'test_checksum',
        'conversion_start_time': 0,
        'conversion_end_time': 1,
    }
    doc3 = {
        'paper_id': '0906.5132',
        'document_version': 4,
        'conversion_status': 1,
        'latexml_version': 'test_latexml_version',
        'tex_checksum': 'test_checksum',
        'conversion_start_time': 0,
        'conversion_end_time': 1,
        'publish_dt': None
    }

    doc4 = {
        'paper_id': '2310.08262',
        'document_version': 1,
        'conversion_status': 1,
        'latexml_version': 'test_latexml_version',
        'tex_checksum': 'test_checksum',
        'conversion_start_time': 0,
        'conversion_end_time': 1,
        'publish_dt': datetime(2022, 1, 1, 0, 0, 0)
    }

    with db.Session() as session:
        for doc in [doc1, doc2, doc3, doc4]:
            session.add(db.models.DBLaTeXMLDocuments(**doc))
        session.commit()

def populate_test_database(drop_and_create: bool, db, engine: Engine, latexml_engine: Engine):
    """Initialize the browse tables."""
    if drop_and_create:
        foreign_key_check(engine, False)
        db.metadata.drop_all(bind=engine)
        db.Session.commit()
        foreign_key_check(engine, True)
        db.metadata.create_all(bind=engine)
        db.Session.commit()

    # Member institution data
    with db.Session() as session:
        session.add(
            db.models.MemberInstitution(
                id=1, name='Localhost University', label='Localhost University'),
        )
        session.add(db.models.MemberInstitutionIP(
            id=1, sid=1, start=2130706433, end=2130706433, exclude=0))

        # Intentionally add another insitution for the same loopback IP as above
        session.add(
            db.models.MemberInstitution(
                id=2, name='Loopback University', label='Loopback University'),
        )
        session.add(db.models.MemberInstitutionIP(
            id=2, sid=2, start=2130706433, end=2130706433, exclude=0))

        inst_cornell = db.models.MemberInstitution(
            id=3,
            name='Cornell University',
            label='Cornell University'
        )
        session.add(inst_cornell)

        inst_cornell_ip = db.models.MemberInstitutionIP(
            id=3,
            sid=inst_cornell.id,
            start=2152988672,  # 128.84.0.0
            end=2153054207,    # 128.84.255.255
            exclude=0
        )
        session.add(inst_cornell_ip)

        inst_cornell_ip_exclude = \
            db.models.MemberInstitutionIP(
                id=4,
                sid=inst_cornell.id,
                start=2152991233,  # 128.84.10.1
                end=2152991242,    # 128.84.10.10
                exclude=1
            )
        session.add(inst_cornell_ip_exclude)

        inst_other = db.models.MemberInstitution(
            id=5,
            name='Other University',
            label='Other University'
        )
        session.add(inst_other)

        inst_other_ip = db.models.MemberInstitutionIP(
            id=5,
            sid=inst_other.id,
            start=2152991236,  # 128.84.10.4
            end=2152991242,    # 128.84.10.10
            exclude=0
        )
        session.add(inst_other_ip)
        session.commit()

    sql_files: List[str] = glob.glob('./tests/data/db/sql/*.sql')
    foreign_key_check(engine, False)
    execute_sql_files(sql_files, engine)

    print ("FIRST METADATA:")
    print (db.Session.query(Metadata).first())

    _populate_latexml_test_data(db, db._latexml_engine)

ABS_FILES = path_of_for_test('data/abs_files')