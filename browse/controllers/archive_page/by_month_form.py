"""Form for month selection of list controller."""
from typing import Any, Dict, List

from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, SubmitField
from wtforms.validators import DataRequired


MONTHS = [
    ('all', 'all months'),
    ('01', '01 (Jan)'),
    ('02', '02 (Feb)'),
    ('03', '03 (Mar)'),
    ('04', '04 (Apr)'),
    ('05', '05 (May)'),
    ('06', '06 (Jun)'),
    ('07', '07 (Jul)'),
    ('08', '08 (Aug)'),
    ('09', '09 (Sep)'),
    ('10', '10 (Oct)'),
    ('11', '11 (Nov)'),
    ('12', '12 (Dec)'),
]


class ByMonthForm(FlaskForm):
    """Form for browse by month input on archive pages.

    This doesn't try to account for the start date of the
    archive, end date of the archive or dates in the future.
    It just accepts these, and expects the /list controller
    to deal with dates for which there are no articles.
    """

    year = SelectField('year',
                       validators=[DataRequired()],
                       choices=[])
    month = SelectField('month',
                        validators=[DataRequired()],
                        choices=MONTHS)
    archive = HiddenField('archive', validators=[DataRequired()])
    submit = SubmitField('Go')

    def __init__(self,
                 archive_id: str,
                 archive: Dict[str, Any],
                 years: List[int]):
        super(ByMonthForm, self).__init__()
        self.year.choices = [(str(ye), str(ye)) for ye in years]
        self.archive.data = archive_id
