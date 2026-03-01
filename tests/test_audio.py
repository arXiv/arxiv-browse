import pytest
from arxiv.identifier import Identifier
from browse.services.audio import get_audio_urls, AudioProvider

tests = [
    ("check_scienceCast_valid", Identifier("2501.12345"), "astro-ph.HE", "tex", True, False),
    ("check_scienceCast_valid", Identifier("2501.12345"), "astro-ph.HE", "pdftex", True, False),
    ("check_scienceCast_wrong_format", Identifier("2501.12345"), "astro-ph.HE", "html", False, False),
    ("check_scienceCast_wrong_format", Identifier("2501.12345"), "astro-ph.HE", "pdf", False, False),
    ("check_scienceCast_old_paper", Identifier("2001.12345"), "astro-ph.HE", "tex", False, False),
    ("check_scienceCast_wrong_category", Identifier("2501.12345"), "quant-ph", "tex", False, False),
    ("check_scienceCast_missing_category", Identifier("2501.12345"), None, "tex", False, False),
    ("check_scienceCast_missing_category_2", Identifier("2501.12345"), "", "tex", False, False),
    ("check_alphaXiv_valid", Identifier("2403.10561"), "cs.HC", "tex", False, True),
]

@pytest.mark.parametrize("desc, paperid, category, src_format, has_sciencecast_audio, has_alphaxiv_audio", tests)
def test_sciencecast_conditions(mocker, desc, paperid, category, src_format, has_sciencecast_audio, has_alphaxiv_audio):
    """Test metadata and if it returns a ScienceCast URL."""
    metadata = mocker.MagicMock()
    metadata.arxiv_identifier = paperid
    metadata.primary_category.id = category
    metadata.source_format = src_format

    result = get_audio_urls(metadata)
    if has_sciencecast_audio:
        assert AudioProvider.SCIENCECAST in result
        assert result[AudioProvider.SCIENCECAST].url is not None
    else:
        assert AudioProvider.SCIENCECAST in result
        assert result[AudioProvider.SCIENCECAST].url is None
        assert "not yet supported" in result[AudioProvider.SCIENCECAST].not_available_reason.lower()

    if has_alphaxiv_audio:
        assert AudioProvider.ALPHAXIV in result
        assert result[AudioProvider.ALPHAXIV].url is not None
    else:
        assert AudioProvider.ALPHAXIV in result
        assert result[AudioProvider.ALPHAXIV].url is None
        assert "only rolled out in" in result[AudioProvider.ALPHAXIV].not_available_reason.lower()
