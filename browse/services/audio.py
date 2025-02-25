"""Service to get per article audio URLs."""
from enum import StrEnum
from typing import Optional, Dict
from datetime import datetime

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
    """get all audio urls for a paper"""
    audio_links: Dict[str, AudioLink]={}

    #scienceCast check
    audio_links[AudioProvider.SCIENCECAST]=check_scienceCast(metadata)

    #other audio providers here
    return audio_links

def has_audio(metadata: DocMetadata) -> bool:
    return any([True for value in get_audio_urls(metadata).values() if value.url])

def check_scienceCast(metadata: DocMetadata) -> AudioLink:
    """check is scienceCast should have an audio summary for the paper"""
    scienceCast_start=datetime(year=2024, month=12, day=1)
    scienceCast_cats=["astro-ph.HE"]
    not_available=AudioLink(service=AudioProvider.SCIENCECAST,
                url=None,
                not_available_reason=f"This paper's area is not yet supported for this paper. Sciencecast currently only supports categories {', '.join(scienceCast_cats)} for papers announced after {scienceCast_start.strftime('%Y-%m-%d')}")

    if not metadata.primary_category or metadata.arxiv_identifier.year is None or metadata.arxiv_identifier.month is None:
        return not_available

    paper_month=datetime(year=metadata.arxiv_identifier.year, month=metadata.arxiv_identifier.month, day=2)
    if paper_month>scienceCast_start and metadata.primary_category.id in scienceCast_cats:
        return AudioLink(service=AudioProvider.SCIENCECAST,
                    url=f"https://sciencecast.org/papers/{DOI_PREFIX}/arXiv.{metadata.arxiv_identifier.id}",
                    )
    else: 
        return not_available
  
