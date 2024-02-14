"""Response header utility functions."""
import json
from datetime import datetime, timedelta, timezone, date
from hashlib import sha1
from zoneinfo import ZoneInfo
from typing import Optional, Tuple, Any, Dict

from flask import request

APPROX_PUBLISH_DURATION = timedelta(hours=1, minutes=30)
PUBLISH_ISO_WEEKDAYS = [1, 2, 3, 4, 7]
"""Days of the week publish happens: Sunday-Thursday."""


def guess_next_update_utc(arxiv_business_tz: ZoneInfo, dt: Optional[datetime] = None) -> Tuple[datetime, bool]:
    """Make a sensible guess at earliest possible datetime of next update.

    Guess is based on provided datetime.

    This is function will be needed by several services that are
    outside of arxiv-browse. In the legacy system having this logic
    redundently implemented lead to difficult to debug problems. Move
    this to a common library like arxiv-base or make it a service
    offered by arxiv-publish.

    Parameters
    ----------
    arxiv_business_tz : ZoneInfo
        Timezone of the arxiv business offices.
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
    if dt is None:
        dt = datetime.now()
    dt = dt.astimezone(arxiv_business_tz)

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

    return (possible_publish_dt.astimezone(tz=timezone.utc), likely_in_publish)


def abs_expires_header(arxiv_business_tz: ZoneInfo) -> str:
    """Get the expires header key and value that should be used by abs."""
    (next_update_dt, likely_in_publish) = guess_next_update_utc(arxiv_business_tz)
    if likely_in_publish:
        return '-1'
    else:
        return mime_header_date(next_update_dt)


def mime_header_date(dt: datetime) -> str:
    """Convert a datetime to string in MIME date format (RFC 1123)."""
    return dt.astimezone(tz=timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')


def _etag_seralizer(input: Any) -> Any:
    if isinstance(input, datetime):
        return date.fromtimestamp(input.timestamp()).isoformat()
    else:
        # avoids unstable values like <lamda_fn:0XA23F2B> in the hash input
        return f"<{type(input).__name__} encoded by abs_page._etag_seralizer()>"


def check_etag_same(response_data: Dict[str, Any], resp_headers: Dict[str, Any]) -> bool:
    """Returns True if the reqeust had an etag and the content is different.

    Has side effects of setting etag header."""
    value = json.dumps(response_data, sort_keys=True, default=_etag_seralizer, ensure_ascii=True)
    hash = sha1(value.encode('utf8')).hexdigest()
    resp_headers["ETag"] = hash
    print("hash was " + hash)
    print("req header was " + str(get_req_header("If-None-Match")))
    return get_req_header("If-None-Match") == hash


def get_req_header(header: str) -> Optional[str]:
    """Gets request header, needs to be case insensative for keys.

    HTTP header keys are case insensitive. RFC 2616
    """
    return next((value for key, value in request.headers.items()
                 if key.lower() == header.lower()), None)
