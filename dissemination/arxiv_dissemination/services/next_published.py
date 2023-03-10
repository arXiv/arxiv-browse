from datetime import datetime, timezone, timedelta

def next_publish(now=None):
    """Guesses the next publish but knows nothing about holidays.

    This is a conservative approch. If this is used for Expires
    headers should never cache when the contents were updated due to publish. It will
    cache less then optimal when there is a holiday and nothing could
    have been updated.
    """
    if now == None:
        now = datetime.now()

    if now.weekday() in [0,1,2,3,6]:
        if now.hour > 20 and now.hour < 21:
            #It's around publish time, PDF might change, really short
            return now.replace(minute=now.minute + 5)
        elif now.hour > 21:
            return next_publish((now + timedelta(days=1)).replace(hour=12))
        else:
            return now.replace(hour=20)

    if now.weekday() == 4:
        return (now + timedelta(days=2)).replace(hour=20)
    if now.weekday() == 5:
        return (now + timedelta(days=2)).replace(hour=20)
