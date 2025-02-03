"""Service to get per article audio URLs."""
from enum import StrEnum
from typing import Optional, List, Dict

from arxiv.document.metadata import DocMetadata
from pydantic import BaseModel

class AudioProvider(StrEnum):
    """Ids for audio provider services."""
    SCIENCECAST = "sciencecast"


class AudioLink(BaseModel):
    """Link to an audio item for a paper."""
    service: AudioProvider
    url: Optional[str]
    not_available_reason: Optional[str]=None


def get_audio_urls(metadata: DocMetadata) -> Dict[str, AudioLink]:
    if metadata.primary_category and metadata.primary_category.in_archive == "astro-ph":
        return {AudioProvider.SCIENCECAST:
                    AudioLink(service=AudioProvider.SCIENCECAST,
                          url=f"https://sciencecast.ai/arxiv/{metadata.arxiv_id_v}",
                          )
                }
    else:
        return {AudioProvider.SCIENCECAST:
                    AudioLink(service=AudioProvider.SCIENCECAST,
                          url=None,
                          not_available_reason="This paper's area is not yet supported. "
                                               "Sciencecast only supports astro-ph. ")}


def has_audio(metadata: DocMetadata) -> bool:
    return any([True for value in get_audio_urls(metadata).values() if value.url])