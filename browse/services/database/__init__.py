from browse.services.database.models import db, MemberInstitution, MemberInstitutionIP
from sqlalchemy.sql import func
from sqlalchemy.exc import SQLAlchemyError
import ipaddress

def get_institution(ip: str):

   decimal_ip = int(ipaddress.ip_address(ip))
   try:
       stmt = db.session.query(MemberInstitution.label, func.sum(MemberInstitutionIP.exclude).label("exclusions")).join(MemberInstitutionIP).filter(MemberInstitutionIP.start <= decimal_ip, MemberInstitutionIP.end >= decimal_ip).group_by(MemberInstitution.label).subquery()
       return db.session.query(stmt.c.label).filter(stmt.c.exclusions == 0).one().label
   except SQLAlchemyError as e:
       raise IOError('Database problem: %s' % e) from e
