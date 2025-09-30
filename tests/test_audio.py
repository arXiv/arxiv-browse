import pytest
from arxiv.identifier import Identifier
from browse.services.audio import check_scienceCast, get_audio_urls, has_audio, AudioProvider


tests = [
    ("check_scienceCast_valid", Identifier("2501.12345"), "astro-ph.HE", "tex", True),
    ("check_scienceCast_valid", Identifier("2501.12345"), "astro-ph.HE", "pdftex", True),
    ("check_scienceCast_wrong_format", Identifier("2501.12345"), "astro-ph.HE", "html", False),
    ("check_scienceCast_wrong_format", Identifier("2501.12345"), "astro-ph.HE", "pdf", False),
    ("check_scienceCast_old_paper", Identifier("2001.12345"), "astro-ph.HE", "tex", False),
    ("check_scienceCast_wrong_category", Identifier("2501.12345"), "quant-ph", "tex", False),
    ("check_scienceCast_missing_category", Identifier("2501.12345"), None, "tex", False),
    ("check_scienceCast_missing_category_2", Identifier("2501.12345"), "", "tex", False),
]

@pytest.mark.parametrize("desc, paperid, category, src_format, has_audio", tests)
def test_sciencecast_conditions(mocker, desc, paperid, category, src_format, has_audio):
    """Test metadata and if it returns a ScienceCast URL."""
    metadata = mocker.MagicMock()
    metadata.arxiv_identifier = paperid
    metadata.primary_category.id = category
    metadata.source_format = src_format

    result = get_audio_urls(metadata)
    if has_audio:
        assert AudioProvider.SCIENCECAST in result
        assert result[AudioProvider.SCIENCECAST].url is not None
    else:
        assert AudioProvider.SCIENCECAST in result
        assert result[AudioProvider.SCIENCECAST].url is None
        assert "not yet supported" in result[AudioProvider.SCIENCECAST].not_available_reason.lower()
