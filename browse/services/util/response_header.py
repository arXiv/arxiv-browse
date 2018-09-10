"""Response header utility functions."""
from datetime import datetime
from typing import Optional
#TODO import arXiv business timezone

def guess_next_update(dt: datetime = datetime.now()) -> datetime:
    """Make a sensible guess at earliest possible time of next update."""
    next_update = dt
    return next_update
