"""Module to collect all of the service status."""

from typing import List

from browse.services import database
from browse.services.documents import get_doc_service
from browse.services.listing import get_listing_service


def service_statuses() ->List[str]:
    """Returns a list of any probelms in all the services."""
    probs = []
    probs.extend(get_listing_service().service_status())
    probs.extend(get_doc_service().service_status())
    probs.extend(database.service_status())
    return probs
