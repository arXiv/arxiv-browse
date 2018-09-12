"""Response header utility functions."""
from datetime import datetime, timedelta, timezone
from dateutil.tz import tzutc, gettz
from typing import Tuple
from browse.services.document.metadata import ARXIV_BUSINESS_TZ


def guess_next_update(dt: datetime = datetime.utcnow()) \
        -> Tuple[datetime, bool]:
    """
    Make a sensible guess at earliest possible datetime of next update.

    Guess is based on provided datetime.
    """
    # local_dt = datetime.now(tz=ARXIV_BUSINESS_TZ)
    publish_dt = datetime(year=dt.year, month=dt.month,
                          day=dt.day, hour=20, minute=0, second=0,
                          microsecond=0, tzinfo=gettz(ARXIV_BUSINESS_TZ))
                          # microsecond=0, tzinfo=tzutc())
    # approx_publish_duration = timedelta(hours=1, minutes=30)
    before_todays_publish: bool = dt < publish_dt
    if before_todays_publish:
        # It's before today's publish time
        delta_to_next_publish = publish_dt - dt
    else:
        # It's after today's publish time
        print(f"after today's publish time, weekday={dt.isoweekday()}")
        delta_to_next_publish = publish_dt + timedelta(days=1) - dt

    if dt.isoweekday() == 5 and not before_todays_publish:
        # It's Friday and after publish (or roughly after freeze)
        print("got here")
        delta_to_next_publish = delta_to_next_publish + timedelta(days=1)
    # elif dt.isoweekday() == 6:
    #     # It's Saturday
    #     delta_to_next_publish = delta_to_next_publish + timedelta(days=1)

    next_publish_dt = dt + delta_to_next_publish
    print(f"\ndt: {dt}\nnext: {next_publish_dt}")
    return next_publish_dt.astimezone(tz=timezone.utc)

def mime_header_date(dt: datetime) -> str:
    """Convert a datetime to string in MIME date format (RFC 1123)."""
    return dt.astimezone(tz=tzutc()).strftime('%a, %d %b %Y %H:%M:%S GMT')
