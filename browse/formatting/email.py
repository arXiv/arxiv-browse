"""Email utility functions."""
import hashlib
from typing import Optional


def generate_show_email_hash(paper_id: str, secret: str) -> Optional[str]:
    """Get the hash used in generating show-email link."""
    if not paper_id or not secret:
        return None
    s = f'{paper_id}/{secret}'
    return hashlib.md5(s.encode()).hexdigest()[7:15]
