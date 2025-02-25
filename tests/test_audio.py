
from unittest.mock import MagicMock
from arxiv.identifier import Identifier
from browse.services.audio import check_scienceCast, get_audio_urls, has_audio, AudioProvider

def test_check_scienceCast_valid():
    """Test valid metadata that should return a ScienceCast URL."""
    metadata = MagicMock()
    metadata.arxiv_identifier= Identifier("2501.12345")
    metadata.primary_category.id = "astro-ph.HE"

    result = check_scienceCast(metadata)
    assert result.url is not None
    assert "sciencecast.org" in result.url
    assert result.service == AudioProvider.SCIENCECAST

def test_check_scienceCast_old_paper():
    """Test old paper that should return 'not available'."""
    metadata = MagicMock()
    metadata.arxiv_identifier= Identifier("2301.12345")
    metadata.primary_category.id = "astro-ph.HE"

    result = check_scienceCast(metadata)
    assert result.url is None
    assert "not yet supported" in result.not_available_reason

def test_check_scienceCast_wrong_category():
    """Test paper in wrong category that should return 'not available'."""
    metadata = MagicMock()
    metadata.arxiv_identifier= Identifier("2501.12345")
    metadata.primary_category.id = "cs.AI"  

    result = check_scienceCast(metadata)
    assert result.url is None
    assert "not yet supported" in result.not_available_reason

def test_check_scienceCast_missing_category():
    """Test missing primary_category should return 'not available'."""
    metadata = MagicMock()
    metadata.arxiv_identifier= Identifier("2501.12345")
    metadata.primary_category = None  # Missing primary_category

    result = check_scienceCast(metadata)
    assert result.url is None
    assert "not yet supported" in result.not_available_reason

def test_check_scienceCast_missing_year_month():
    """Test missing year/month should return 'not available'."""
    metadata = MagicMock()
    metadata.arxiv_identifier.year = None
    metadata.arxiv_identifier.month = None
    metadata.arxiv_identifier.id = "2501.55555"
    metadata.primary_category.id = "astro-ph.HE"

    result = check_scienceCast(metadata)
    assert result.url is None
    assert "not yet supported" in result.not_available_reason

def test_get_audio_urls_valid():
    """Test that get_audio_urls correctly includes the ScienceCast URL."""
    metadata = MagicMock()
    metadata.arxiv_identifier= Identifier("2501.12345")
    metadata.primary_category.id = "astro-ph.HE"

    result = get_audio_urls(metadata)
    assert AudioProvider.SCIENCECAST in result
    assert result[AudioProvider.SCIENCECAST].url is not None

def test_get_audio_urls_not_available():
    """Test get_audio_urls when the paper doesn't qualify (should return 'not available')."""
    metadata = MagicMock()
    metadata.arxiv_identifier= Identifier("2301.12345")
    metadata.primary_category.id = "astro-ph.HE"

    result = get_audio_urls(metadata)
    assert AudioProvider.SCIENCECAST in result
    assert result[AudioProvider.SCIENCECAST].url is None
    assert "not yet supported" in result[AudioProvider.SCIENCECAST].not_available_reason

def test_has_audio_valid():
    """Test has_audio should return True for valid metadata."""
    metadata = MagicMock()
    metadata.arxiv_identifier= Identifier("2501.12345")
    metadata.primary_category.id = "astro-ph.HE"
    assert has_audio(metadata) is True

def test_has_audio_no_audio():
    """Test has_audio should return False when there is no available audio."""
    metadata = MagicMock()
    metadata.arxiv_identifier= Identifier("2301.12345")
    metadata.primary_category.id = "astro-ph.HE"
    assert has_audio(metadata) is False
