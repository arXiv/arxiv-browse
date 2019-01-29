from typing import List, Any, Dict, Tuple

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, HiddenField, SubmitField
from wtforms.validators import DataRequired

MONTHS = [
    ('01','01 (Jan)'),
    ('02','02 (Feb)'),
    ('03','03 (Mar)'),
    ('04','04 (Apr)'),
    ('05','05 (May)'),
    ('06','06 (Jun)'),
    ('07','07 (Jul)'),
    ('08','08 (Aug)'),
    ('09','09 (Sep)'),
    ('10','10 (Oct)'),
    ('11','11 (Nov)'),
    ('12','12 (Dec)'),
]

DAYS = [(i,i) for i in range(1,31)]

class CatchupForm(FlaskForm):
    """Form for catchup.

    This doesn't try to account for the start date of the 
    archive, end date of the archive or dates in the future. 
    It just accepts these, and expects the /list controller
    to deal with dates for which there are no articles.
    """
    day = SelectField('syear',
                       validators=[DataRequired()],
                       choices=DAYS)
    month = SelectField('smonth',
                        validators=[DataRequired()],
                        choices=MONTHS)
    year = SelectField('syear',
                       validators=[DataRequired()],
                       choices=[])
    abstracts = SelectField('method', choices=[('without','without'),('with','with')])
    archive = HiddenField('archive', validators=[DataRequired()])
    submit = SubmitField('Go')
    
    def __init__(self, archive_id:str, archive:Dict[str,Any]):
        super(CatchupForm, self).__init__()
        self.year.choices = year_choices( archive )
        self.archive.data = archive_id
        # TODO set selected month to now.month - 1
        # TODO set day to now.dayOfMonth - 7 days ago



def year_choices(archive:Dict[str,Any])->List[Tuple[str,str]]:
    # TODO make list based on start date, end date and current date
    return [('2000','2000'), ('2001','2001'), ('2002','2002'), ('2003','2003'), ('2004','2004'), ('2005','2005'), ('2006','2006'), ('2007','2007'), ('2008','2008'), ('2009','2009'), ]
