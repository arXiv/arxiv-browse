"""Helper script to initialize the browse database and add a few rows."""

import glob
from typing import List

import click

from browse.factory import create_web_app
from browse.services.database import models
from tests import populate_test_database as populate_db

app = create_web_app()
app.app_context().push()

@app.cli.command()
@click.option('--drop_and_create', '-c', is_flag=True,
              help='Drop and recreate tables from models.')
def populate_test_database(drop_and_create: bool) -> None:
    """Initialize the browse tables."""
    print("Writing to DB at " + app.settings.SQLALCHEMY_DATABASE_URI)
    populate_db(drop_and_create, models)

if __name__ == '__main__':
    populate_test_database()
