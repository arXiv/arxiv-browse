"""Response header utility functions."""
from datetime import datetime, timedelta, timezone
from typing import Tuple
from dateutil.tz import tzutc, gettz


from arxiv.base.globals import get_application_config


APPROX_PUBLISH_DURATION = timedelta(hours=1, minutes=30)
PUBLISH_ISO_WEEKDAYS = [1, 2, 3, 4, 7]
"""Days of the week publish happens: Sunday-Thursday."""


def guess_next_update_utc(dt: datetime = datetime.now(timezone.utc)) \
        -> Tuple[datetime, bool]:
    """
    Make a sensible guess at earliest possible datetime of next update.

    Guess is based on provided datetime.

    Parameters
    ----------
    dt : datetime
        The datetime to use as the basis for comparison to guess the
        "next update" datetime.

    Returns
    -------
    Tuple[datetime, bool]
        A UTC-based datetime for the next update; a boolean that indicates
        whether the provided dt is likely to coincide with a publish process,
        which is the APPROX_PUBLISH_DURATION window starting 20:00 on the
        normal publish days specified by PUBLISH_ISO_WEEKDAYS.

    """
    config = get_application_config()
    tz = gettz(config.get('ARXIV_BUSINESS_TZ', 'US/Eastern'))
    dt = dt.astimezone(tz=tz)

    possible_publish_dt = dt.replace(hour=20, minute=0, second=0)

    after_todays_publish: bool = dt >= possible_publish_dt
    likely_in_publish = False
    delta_to_next_publish = timedelta(days=0)

    weekday = dt.isoweekday()
    if after_todays_publish:
        delta_to_next_publish = timedelta(days=1)
        if dt < (possible_publish_dt + APPROX_PUBLISH_DURATION) \
           and weekday in PUBLISH_ISO_WEEKDAYS:
            likely_in_publish = True

    if weekday == 4 and after_todays_publish:
        # It's Thursday and after publish; next update would be Sunday
        delta_to_next_publish = timedelta(days=3)
    elif weekday in (5, 6):
        # It's Friday or Saturday
        days_to_add = 7 - weekday
        delta_to_next_publish = timedelta(days=days_to_add)

    possible_publish_dt = possible_publish_dt + delta_to_next_publish

    return (possible_publish_dt.astimezone(tz=tzutc()), likely_in_publish)


def abs_expires_header() -> Tuple[str, str]:
    """Get the expires header key and value that should be used by abs."""
    (next_update_dt, likely_in_publish) = guess_next_update_utc()
    if likely_in_publish:
        return ('Expires', '-1')
    else:
        return ('Expires', mime_header_date(next_update_dt))


def mime_header_date(dt: datetime) -> str:
    """Convert a datetime to string in MIME date format (RFC 1123)."""
    return dt.astimezone(tz=tzutc()).strftime('%a, %d %b %Y %H:%M:%S GMT')
