"""Service to get per article audio URLs."""
from enum import StrEnum
from typing import Optional, List, Dict

from arxiv.document.metadata import DocMetadata
from pydantic import BaseModel

DOI_PREFIX = "10.48550"
"""arXiv's DOI_PREFIX."""

class AudioProvider(StrEnum):
    """Ids for audio provider services."""
    SCIENCECAST = "sciencecast"


class AudioLink(BaseModel):
    """Link to an audio item for a paper."""
    service: AudioProvider
    url: Optional[str]
    not_available_reason: Optional[str]=None


def get_audio_urls(metadata: DocMetadata) -> Dict[str, AudioLink]:
    if metadata.primary_category and metadata.primary_category.id == "astro-ph.HE":
        return {AudioProvider.SCIENCECAST:
                    AudioLink(service=AudioProvider.SCIENCECAST,
                          url=f"https://sciencecast.org/papers/{DOI_PREFIX}/arXiv.{metadata.arxiv_id}",
                          )
                }
    else:
        return {AudioProvider.SCIENCECAST:
                    AudioLink(service=AudioProvider.SCIENCECAST,
                          url=None,
                          not_available_reason="This paper's area is not yet supported. "
                                               "Sciencecast currently only supports astro-ph.HE ")}


def has_audio(metadata: DocMetadata) -> bool:
    return any([True for value in get_audio_urls(metadata).values() if value.url])