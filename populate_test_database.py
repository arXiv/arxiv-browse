"""Helper script to initialize the browse database and add a few rows."""

import click
from browse.factory import create_web_app
from browse.services.database import models
import glob
from tests import execute_sql_files
from typing import List


app = create_web_app()
app.app_context().push()


@app.cli.command()
@click.option('--drop_and_create', '-c', is_flag=True,
              help='Drop and recreate tables from models.')
def populate_test_database(drop_and_create: bool) -> None:
    """Initialize the browse tables."""

    if drop_and_create:
        models.db.drop_all()
        models.db.create_all()

    # Member institution data
    models.db.session.add(
        models.MemberInstitution(
            id=1, name='Localhost University', label='Localhost University'),
    )
    models.db.session.add(models.MemberInstitutionIP(
        id=1, sid=1, start=2130706433, end=2130706433, exclude=0))
    models.db.session.commit()
    sql_files: List[str] = glob.glob('./tests/data/db/sql/*.sql')
    execute_sql_files(sql_files, models.db.engine)


if __name__ == '__main__':
    populate_test_database()
