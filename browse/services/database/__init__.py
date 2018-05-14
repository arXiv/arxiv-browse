"""Import db instance and define utility functions."""

import ipaddress
from browse.services.database.models import db
from browse.services.database.models import MemberInstitution, \
    MemberInstitutionIP
from sqlalchemy.sql import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound
from flask_sqlalchemy import SQLAlchemy

from typing import Optional

# def get_institution(ip: str):
#     """Get institution label from IP address."""
#     decimal_ip = int(ipaddress.ip_address(ip))
#     try:
#         stmt = (
#             db.session.query(
#                 MemberInstitution.label,
#                 func.sum(MemberInstitutionIP.exclude).label("exclusions")
#             ).
#             join(MemberInstitutionIP).
#             filter(
#                 MemberInstitutionIP.start <= decimal_ip,
#                 MemberInstitutionIP.end >= decimal_ip
#             ).
#             group_by(MemberInstitution.label).
#             subquery()
#         )
#
#         return (
#                     db.session.query(stmt.c.label).
#                     filter(stmt.c.exclusions == 0).one().label
#                )
#     except NoResultFound:
#         return None
#     except SQLAlchemyError as e:
#         raise IOError('Database error: %s' % e) from e
