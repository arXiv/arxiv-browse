"""Import db instance and define utility functions."""

import ipaddress
from typing import Optional
from sqlalchemy.sql import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound
from browse.services.database.models import db, MemberInstitution, \
    MemberInstitutionIP


def get_institution(ip: str) -> Optional[str]:
    """Get institution label from IP address."""
    decimal_ip = int(ipaddress.ip_address(ip))
    try:
        stmt = (
            db.session.query(
                MemberInstitution.label,
                func.sum(MemberInstitutionIP.exclude).label("exclusions")
            ).
            join(MemberInstitutionIP).
            filter(
                MemberInstitutionIP.start <= decimal_ip,
                MemberInstitutionIP.end >= decimal_ip
            ).
            group_by(MemberInstitution.label).
            subquery()
        )
        institution_name = db.session.query(stmt.c.label).\
            filter(stmt.c.exclusions == 0).one().label
        return institution_name  # type: ignore
    except NoResultFound:
        return None
    except SQLAlchemyError as e:
        raise IOError('Database error: %s' % e) from e
